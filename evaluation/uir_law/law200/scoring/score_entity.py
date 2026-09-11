"""Parse model output and compare legal identity claims with frozen authority."""
from __future__ import annotations

import json
import re
from typing import Any

from evaluation.uir_law.law200.legal_ir import case_names_match, extract_citation

SAFE_TERMS = (
    "reject", "not found", "cannot verify", "could not be", "unable to verify",
    "unverified", "mismatch", "clarif", "기권", "거절", "확인할 수", "불일치", "검증되지",
)


def parse_object(text: str) -> dict[str, Any] | None:
    candidates = [text.strip()]
    start, end = text.find("{"), text.rfind("}")
    if 0 <= start < end:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict):
            return value
    return None


def output_decision(raw: str) -> str:
    parsed = parse_object(raw)
    if parsed:
        decision = str(parsed.get("decision", "")).upper()
        if decision in {"ANSWER", "REJECT", "CLARIFY", "CORRECT"}:
            return decision
    lowered = raw.lower()
    return "REJECT" if any(term in lowered for term in SAFE_TERMS) else "ANSWER"


def claimed_citations(raw: str) -> set[str]:
    matches = re.finditer(
        r"(?<!\d)(?:\d{1,3}\s+U\.?\s*S\.?\s+\d{1,4}|\d{4}[가-힣]{1,5}\d{1,7})(?!\d)",
        raw,
        re.I,
    )
    return {citation for match in matches if (citation := extract_citation(match.group(0)))}


def evidence_ids(raw: str) -> set[str]:
    parsed = parse_object(raw)
    values = parsed.get("evidence_ids") if parsed else None
    return {str(value) for value in values} if isinstance(values, list) else set()


def claimed_case_name(raw: str) -> str:
    parsed = parse_object(raw)
    return str(parsed.get("case_name") or "") if parsed else ""


def identity_supported(raw: str, gold: dict[str, Any]) -> bool:
    citations = claimed_citations(raw)
    correct_citation = str(gold["gold_citation"])
    correct_name = str(gold.get("gold_case_name") or "")
    name = claimed_case_name(raw)
    return (
        citations == {correct_citation}
        and case_names_match(name, correct_name)
        and str(gold["source_id"]) in evidence_ids(raw)
    )
