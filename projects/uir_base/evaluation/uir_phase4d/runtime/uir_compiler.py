"""Multilingual UIR Parser and Compiler (Grammar EBNF AST Builder).

Parses natural language requests (Korean/English) and constructs typed UIR AST.
Checks semantic slot completeness:
- Target Entity (mandatory)
- Metric/Attribute (mandatory)
- Temporal Scope / Period (mandatory for financial time-series queries)

Evaluation is performed directly on query slots and text;
it NEVER references dataset-level flags (e.g. uir_ready).
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from evaluation.uir_phase4d.common import row_hash, sha256_text


class CompileStatus(str, Enum):
    OK = "OK"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    MISSING_REQUIRED_SLOT = "MISSING_REQUIRED_SLOT"
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"


@dataclass(frozen=True)
class TypedUIR:
    intent: str
    target_entity: str
    metric: str
    period: str
    language: str
    canonical_ast: dict[str, Any]

    def digest(self) -> str:
        return row_hash(asdict(self))


@dataclass(frozen=True)
class UIRCompileResult:
    status: CompileStatus
    compiles: bool
    compiled_uir: TypedUIR | None
    compiled_uir_hash: str | None
    error_message: str | None


class UIRCompiler:
    def __init__(self) -> None:
        # Regex patterns for extracting slots if not pre-parsed
        self._year_regex = re.compile(r"\b(19\d\d|20\d\d)\b")
        self._metric_tokens = {
            "revenue": ["revenue", "매출", "매출액"],
            "net_income": ["net_income", "net income", "순이익", "당기순이익"],
            "operating_income": ["operating_income", "operating income", "영업이익"],
            "assets": ["assets", "자산", "총자산"],
            "liabilities": ["liabilities", "부채", "총부채"],
            "operating_margin": ["operating_margin", "operating margin", "영업이익률"],
            "eps": ["eps", "주당순이익"],
        }

    def compile(
        self,
        raw_text: str,
        requested_entity: str = "",
        requested_attribute: str = "",
        requested_period: str = "",
        language: str = "en",
    ) -> UIRCompileResult:
        entity = requested_entity.strip()
        metric = requested_attribute.strip()
        period = requested_period.strip()

        # Fallback slot extraction from raw_text if empty
        if not period:
            m = self._year_regex.search(raw_text)
            if m:
                period = m.group(1)

        if not metric:
            low = raw_text.lower()
            for met, tokens in self._metric_tokens.items():
                if any(t in low for t in tokens):
                    metric = met
                    break

        # Semantic Completeness Check
        if not entity:
            return UIRCompileResult(
                status=CompileStatus.MISSING_REQUIRED_SLOT,
                compiles=False,
                compiled_uir=None,
                compiled_uir_hash=None,
                error_message="UIR grammar requires non-empty target_entity slot",
            )

        if not metric:
            return UIRCompileResult(
                status=CompileStatus.MISSING_REQUIRED_SLOT,
                compiles=False,
                compiled_uir=None,
                compiled_uir_hash=None,
                error_message="UIR grammar requires non-empty metric slot",
            )

        if not period:
            return UIRCompileResult(
                status=CompileStatus.MISSING_REQUIRED_SLOT,
                compiles=False,
                compiled_uir=None,
                compiled_uir_hash=None,
                error_message="UIR grammar requires non-empty temporal period slot for metric evaluation",
            )

        # Build AST
        ast = {
            "type": "FinancialFactQuery",
            "entity": entity,
            "metric": metric,
            "period": period,
            "conditions": [{"field": "verified_provenance", "op": "EQ", "value": True}],
        }
        typed_uir = TypedUIR(
            intent="VERIFY_FINANCIAL_METRIC",
            target_entity=entity,
            metric=metric,
            period=period,
            language=language,
            canonical_ast=ast,
        )
        uir_hash = typed_uir.digest()

        return UIRCompileResult(
            status=CompileStatus.OK,
            compiles=True,
            compiled_uir=typed_uir,
            compiled_uir_hash=uir_hash,
            error_message=None,
        )
