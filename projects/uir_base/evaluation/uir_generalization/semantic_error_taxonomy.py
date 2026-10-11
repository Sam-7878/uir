#!/usr/bin/env python3
from __future__ import annotations

TAXONOMY = [
    "INTENT_UNSEEN", "ACTION_SYNONYM_UNSEEN", "TARGET_EXTRACTION_FAILURE",
    "ENTITY_ALIAS_FAILURE", "ATTRIBUTE_SYNONYM_FAILURE", "TEMPORAL_SCOPE_FAILURE",
    "CONDITION_ORDER_FAILURE", "NEGATION_FAILURE", "EXCEPTION_SCOPE_FAILURE",
    "COORDINATION_FAILURE", "CODE_SWITCH_FAILURE", "MORPHOLOGY_FAILURE_KO",
    "PREPOSITION_FAILURE_EN", "UNSUPPORTED_SURFACE_FORM", "AMBIGUOUS_INPUT",
    "SECURITY_REJECT_EXPECTED",
]


def classify(case: dict, record: dict) -> str:
    text = case["input"]; lower = text.lower(); expected = case.get("expected_semantics") or {}; actual = record.get("actual_semantics") or {}
    if case.get("category") == "adversarial" and case.get("expected_outcome") == "REJECT":
        return "SECURITY_REJECT_EXPECTED"
    if case.get("category") == "ambiguous" or not expected:
        return "AMBIGUOUS_INPUT"
    if actual:
        if actual.get("target") != expected.get("target"): return "TARGET_EXTRACTION_FAILURE"
        if actual.get("metric") != expected.get("metric"): return "ATTRIBUTE_SYNONYM_FAILURE"
        if actual.get("period") != expected.get("period"): return "TEMPORAL_SCOPE_FAILURE"
    if any(token in lower for token in ("unless", "except", "예외", "제외")): return "EXCEPTION_SCOPE_FAILURE"
    if any(token in lower for token in (" and ", " or ", "그리고", "또는")): return "COORDINATION_FAILURE"
    if any(token in lower for token in (" not ", "never", "아니", "않")): return "NEGATION_FAILURE"
    known = ("verify", "check", "analyze", "summarize", "extract", "compare", "검증", "확인", "분석", "요약", "추출", "비교")
    if not any(token in lower for token in known): return "ACTION_SYNONYM_UNSEEN"
    if case.get("language") == "ko" and any(token in lower for token in (" verify ", " check ", " unless ", " except ", " analyze ")): return "CODE_SWITCH_FAILURE"
    if case.get("language") == "ko": return "MORPHOLOGY_FAILURE_KO"
    if any(token in lower for token in ("associated with", " during ", " for ", "'s ")): return "PREPOSITION_FAILURE_EN"
    return "UNSUPPORTED_SURFACE_FORM"
