"""English Controlled Language Frontend for UIR."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base import BaseFrontend, ParsedDraft


class EnglishFrontend(BaseFrontend):
    """Parses English research/query requests into structured UIR draft."""

    INTENT_KEYWORDS = {
        "summarize": "SUMMARIZE",
        "summary": "SUMMARIZE",
        "extract": "EXTRACT",
        "lookup": "LOOKUP",
        "search": "LOOKUP",
        "find": "LOOKUP",
        "analyze": "ANALYZE",
        "compare": "COMPARE",
        "verify": "VERIFY",
        "trace": "CAUSE_TRACE",
        "why": "CAUSE_TRACE",
        "audit": "AUDIT",
        "transfer": "TRANSFER",
        "wire": "TRANSFER",
        "execute": "EXECUTE_TOOL",
        "run": "EXECUTE_TOOL",
    }

    ACTION_MAP = {
        "SUMMARIZE": "SUMMARIZE",
        "EXTRACT": "EXTRACT",
        "LOOKUP": "LOOKUP",
        "ANALYZE": "ANALYZE",
        "COMPARE": "COMPARE",
        "VERIFY": "VERIFY",
        "CAUSE_TRACE": "CAUSE_TRACE",
        "AUDIT": "AUDIT",
        "TRANSFER": "TRANSFER",
        "EXECUTE_TOOL": "EXECUTE_TOOL",
    }

    def parse(self, text: str) -> ParsedDraft:
        clean_text = text.strip()
        lower = clean_text.lower()

        # 1. Detect Intent
        detected_intent = "LOOKUP"
        for kw, intent in self.INTENT_KEYWORDS.items():
            if re.search(rf"\b{kw}\b", lower):
                detected_intent = intent
                break

        action = self.ACTION_MAP.get(detected_intent, "LOOKUP")

        # 2. Extract Entities
        entities = []
        ticker_matches = re.findall(r"\b([A-Z]{1,5}|\d{6})\b", clean_text)
        for t in ticker_matches:
            if t not in {"A", "AN", "THE", "JSON", "UIR", "SLM", "SEC", "API", "USD", "KRW", "AND", "OR", "NOT", "FOR", "IN"}:
                entities.append(t)

        named_map = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "samsung": "005930",
            "hynix": "000660",
            "fake_corp": "FAKE_CORP",
            "phantom": "PHANTOM_LLC",
            "null_ticker": "NULL_TICKER",
        }
        for name, code in named_map.items():
            if name in lower and code not in entities:
                entities.append(code)

        if not entities:
            # Fallback check for quotes
            match = re.search(r"['\"]([^'\"]+)['\"]", clean_text)
            if match:
                entities.append(match.group(1).strip().upper())
            else:
                entities.append("UNKNOWN_ENTITY")

        # 3. Extract Period
        period = None
        year_match = re.search(r"\b(20\d{2})\b", clean_text)
        if year_match:
            period = year_match.group(1)

        # 4. Extract Metric / Attributes
        arguments: Dict[str, Any] = {"raw_query": clean_text}
        if "revenue" in lower or "sales" in lower:
            arguments["metric"] = "revenue"
        elif "net income" in lower or "profit" in lower:
            arguments["metric"] = "net_income"
        elif "operating profit" in lower or "operating income" in lower:
            arguments["metric"] = "operating_profit"

        if period:
            arguments["fiscal_year"] = period

        return ParsedDraft(
            language="EN",
            intent=detected_intent,
            action=action,
            target_entities=entities,
            arguments=arguments,
            temporal_scope=period,
            domain="FINANCE",
            raw_prompt=clean_text,
        )
