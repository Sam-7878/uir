"""Korean Controlled Language Frontend for UIR."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base import BaseFrontend, ParsedDraft


class KoreanFrontend(BaseFrontend):
    """Parses Korean research/query requests into structured UIR draft."""

    INTENT_KEYWORDS = {
        "요약": "SUMMARIZE",
        "추출": "EXTRACT",
        "조회": "LOOKUP",
        "검색": "LOOKUP",
        "분석": "ANALYZE",
        "비교": "COMPARE",
        "검증": "VERIFY",
        "원인": "CAUSE_TRACE",
        "추적": "CAUSE_TRACE",
        "감사": "AUDIT",
        "이체": "TRANSFER",
        "송금": "TRANSFER",
        "실행": "EXECUTE_TOOL",
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

        # 1. Detect Intent
        detected_intent = "LOOKUP"
        for kw, intent in self.INTENT_KEYWORDS.items():
            if kw in clean_text:
                detected_intent = intent
                break

        action = self.ACTION_MAP.get(detected_intent, "LOOKUP")

        # 2. Extract Entities (Tickers / CIKs / CRNOs / English or Korean Capitalized Terms)
        entities = []
        ticker_matches = re.findall(r"\b([A-Z0-9]{3,6}|\d{6})\b", clean_text)
        for t in ticker_matches:
            if t not in {"JSON", "UIR", "SLM", "DART", "API", "KRW", "USD"}:
                entities.append(t)

        # Korean Named Entities & English company mentions
        named_map = {
            "삼성전자": "005930",
            "삼성": "005930",
            "sk하이닉스": "000660",
            "하이닉스": "000660",
            "애플": "AAPL",
            "apple": "AAPL",
            "마이크로소프트": "MSFT",
            "microsoft": "MSFT",
            "가짜기업": "가짜기업_99",
            "유령법인": "유령법인_001",
        }
        lower_text = clean_text.lower()
        for name, code in named_map.items():
            if name in lower_text and code not in entities:
                entities.append(code)

        if not entities:
            # Fallback check for any quoted or tagged entity
            match = re.search(r"['\"]([^'\"]+)['\"]", clean_text)
            if match:
                entities.append(match.group(1).strip().upper())
            else:
                entities.append("UNKNOWN_ENTITY")

        # 3. Extract Year/Period
        period = None
        year_match = re.search(r"(20\d{2})년?", clean_text)
        if year_match:
            period = year_match.group(1)

        # 4. Extract Attributes/Metrics
        arguments: Dict[str, Any] = {"raw_query": clean_text}
        if "매출" in clean_text or "매출액" in clean_text:
            arguments["metric"] = "revenue"
        elif "영업이익" in clean_text:
            arguments["metric"] = "operating_profit"
        elif "순이익" in clean_text:
            arguments["metric"] = "net_income"

        if period:
            arguments["fiscal_year"] = period

        return ParsedDraft(
            language="KO",
            intent=detected_intent,
            action=action,
            target_entities=entities,
            arguments=arguments,
            temporal_scope=period,
            domain="FINANCE",
            raw_prompt=clean_text,
        )
