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
        # Exclude common non-entity capitalized words and markers
        filter_out = {
            "A", "AN", "THE", "JSON", "UIR", "SLM", "SEC", "DART", "API", "USD", "KRW",
            "AND", "OR", "NOT", "FOR", "IN", "EDGAR", "EST", "FY23", "FY24", "FY22", "FY",
            "10-K", "10-Q", "REPORT", "FILING"
        }
        ticker_matches = re.findall(r"\b([A-Z]{2,6}|\d{6})\b", clean_text)
        for t in ticker_matches:
            if t not in filter_out and t not in entities:
                entities.append(t)

        named_map = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "nvidia": "NVDA",
            "meta": "META",
            "tesla": "TSLA",
            "netflix": "NFLX",
            "samsung": "005930",
            "hynix": "000660",
            "hyundai": "005380",
            "naver": "035420",
            "kia": "000270",
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
        else:
            from ..evidence.trusted_resolver import VERIFIED_ENTITY_REGISTRY
            known = [e for e in entities if e in VERIFIED_ENTITY_REGISTRY]
            if known:
                entities = known + [e for e in entities if e not in known]

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
