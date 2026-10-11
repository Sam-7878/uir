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
        # Match 6-digit Korean stock codes even when attached to Korean particles (e.g. 005930의, 035420은)
        code_matches = re.findall(r"(?:^|[^\d])(\d{6})(?:[^\d]|$)", clean_text)
        for c in code_matches:
            if c not in entities:
                entities.append(c)

        # Match uppercase English tickers (2-6 letters) even if followed by Korean particles
        filter_out = {
            "JSON", "UIR", "SLM", "DART", "API", "KRW", "USD", "SEC", "EDGAR", "EST",
            "FY23", "FY24", "FY22", "FY", "10-K", "10-Q"
        }
        ticker_matches = re.findall(r"\b([A-Z]{2,6})(?:[가-힣]|\b)", clean_text)
        for t in ticker_matches:
            t_up = t.upper()
            if t_up not in filter_out and t_up not in entities:
                entities.append(t_up)

        # Korean Named Entities & English company mentions
        named_map = {
            "삼성전자": "005930",
            "삼성": "005930",
            "sk하이닉스": "000660",
            "하이닉스": "000660",
            "현대차": "005380",
            "현대자동차": "005380",
            "네이버": "035420",
            "naver": "035420",
            "기아": "000270",
            "kia": "000270",
            "lg화학": "051910",
            "셀트리온": "068270",
            "포스코": "005490",
            "카카오": "035720",
            "애플": "AAPL",
            "apple": "AAPL",
            "마이크로소프트": "MSFT",
            "microsoft": "MSFT",
            "구글": "GOOGL",
            "google": "GOOGL",
            "아마존": "AMZN",
            "amazon": "AMZN",
            "엔비디아": "NVDA",
            "nvidia": "NVDA",
            "메타": "META",
            "meta": "META",
            "테슬라": "TSLA",
            "tesla": "TSLA",
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
        else:
            from ..evidence.trusted_resolver import VERIFIED_ENTITY_REGISTRY
            known = [e for e in entities if e in VERIFIED_ENTITY_REGISTRY]
            if known:
                entities = known + [e for e in entities if e not in known]

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
