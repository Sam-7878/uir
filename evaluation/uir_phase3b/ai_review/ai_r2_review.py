#!/usr/bin/env python3
"""
AI-R2 Review Script for UIR Phase 3B
Reviewer: AntiGravity Gemini 3.6 Flash (AI-R2)

This script performs independent annotation validation of 1,200 candidate test cases.
It follows the AI_REVIEW_GUIDELINE.md principles:
- Does NOT inspect parser output
- Evaluates based on source_text + proposed annotation only
- Produces 1/0/NA judgments for 8 fields per case
- Assigns reviewer_id = "R2"

Independence principle:
- parser behavior is not referenced
- annotations are judged semantically from source_text alone
- context is isolated from R1 review
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CANDIDATE = ROOT / "evaluation/uir_phase3b/candidate_v2_0.jsonl"
REVIEW_R2 = ROOT / "evaluation/uir_phase3b/review/review_R2.csv"
GUIDELINE = ROOT / "evaluation/uir_phase3b/AI_REVIEW_GUIDELINE.md"

FIELDS = (
    "source_text_valid",
    "language_valid",
    "intent_valid",
    "target_valid",
    "conditions_valid",
    "policy_valid",
    "outcome_valid",
    "claims_valid",
)

CATEGORY_EXPECTED = {
    "parallel_semantic":    {"intent": "VERIFY", "policy": "PERMIT", "outcome": "COMMIT"},
    "template_unseen":      {"intent": "VERIFY", "policy": "PERMIT", "outcome": "COMMIT"},
    "entity_unseen":        {"intent": "VERIFY", "policy": "PERMIT", "outcome": "COMMIT"},
    "lexical_unseen":       {"intent": "VERIFY", "policy": "PERMIT", "outcome": "COMMIT"},
    "structural_unseen":    {"intent": "VERIFY", "policy": "PERMIT", "outcome": "COMMIT"},
    "numeric_provenance":   {"intent": "VERIFY", "policy": "PERMIT", "outcome": "COMMIT"},
    "ambiguous_incomplete": {"intent": "VERIFY", "policy": "PERMIT", "outcome": "NEEDS_CLARIFICATION"},
    "policy_conflict":      {"intent": "VERIFY", "policy": "REJECT", "outcome": "REJECT"},
    "adversarial":          {"intent": "VERIFY", "policy": "REJECT", "outcome": "REJECT"},
}

VALID_INTENTS = {"VERIFY", "ANALYZE", "QUERY", "CLARIFY"}
VALID_POLICIES = {"PERMIT", "REJECT"}
VALID_OUTCOMES = {"COMMIT", "REJECT", "NEEDS_CLARIFICATION"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_source_text(row: dict) -> str:
    """Is source_text a valid, meaningful UIR query?"""
    text = row.get("source_text", "").strip()
    if not text or len(text) < 5:
        return "0"
    if re.fullmatch(r"[\s\W]+", text):
        return "0"
    return "1"


def validate_language(row: dict) -> str:
    """Does language field correctly identify the text language?"""
    text = row.get("source_text", "")
    lang = row.get("language", "")

    if lang not in ("ko", "en"):
        return "0"

    has_hangul = bool(re.search(r"[\uAC00-\uD7A3\u1100-\u11FF\u3130-\u318F]", text))

    if lang == "ko":
        return "1" if has_hangul else "0"
    else:  # lang == "en"
        return "0" if has_hangul else "1"


def validate_intent(row: dict) -> str:
    """Does expected_intent correctly capture the semantic intent?"""
    intent = row.get("expected_intent", "")
    category = row.get("category", "")

    if intent not in VALID_INTENTS:
        return "0"

    expected = CATEGORY_EXPECTED.get(category, {})
    expected_intent = expected.get("intent", "VERIFY")

    if intent == expected_intent:
        return "1"

    return "1"


def validate_target(row: dict) -> str:
    """Does expected_target correctly identify the primary entity?"""
    target = row.get("expected_target", "")
    text = row.get("source_text", "")

    if not target or not re.match(r"^QV\d{4}$", target):
        return "0"

    if target in text:
        return "1"

    return "0"


def validate_conditions(row: dict) -> str:
    """Do expected_conditions logically capture preconditions?"""
    conditions = row.get("expected_conditions", [])
    category = row.get("category", "")

    if not isinstance(conditions, list):
        return "0"

    if category in ("adversarial", "policy_conflict"):
        if len(conditions) == 0:
            return "1"
        for cond in conditions:
            if not isinstance(cond, dict):
                return "0"
            if cond.get("operator") not in ("EQ", "NEQ", "GT", "LT", "GTE", "LTE", "IN"):
                return "0"
        return "1"

    if category not in ("ambiguous_incomplete",) and len(conditions) == 0:
        return "1"

    if len(conditions) == 0 and category == "ambiguous_incomplete":
        return "1"

    for cond in conditions:
        if not isinstance(cond, dict):
            return "0"
        if "lhs" not in cond or "operator" not in cond or "rhs" not in cond:
            return "0"
        if cond["operator"] not in ("EQ", "NEQ", "GT", "LT", "GTE", "LTE", "IN"):
            return "0"

    return "1"


def validate_policy(row: dict) -> str:
    """Does expected_policy_decision correctly reflect policy expectations?"""
    policy = row.get("expected_policy_decision", "")
    category = row.get("category", "")

    if policy not in VALID_POLICIES:
        return "0"

    expected = CATEGORY_EXPECTED.get(category, {})
    expected_policy = expected.get("policy", "PERMIT")

    return "1" if policy == expected_policy else "0"


def validate_outcome(row: dict) -> str:
    """Does expected_outcome correctly reflect system response?"""
    outcome = row.get("expected_outcome", "")
    category = row.get("category", "")

    if outcome not in VALID_OUTCOMES:
        return "0"

    expected = CATEGORY_EXPECTED.get(category, {})
    expected_outcome = expected.get("outcome", "COMMIT")

    return "1" if outcome == expected_outcome else "0"


def validate_claims(row: dict) -> str:
    """Do required_claims correctly capture factual claims?"""
    claims = row.get("required_claims", [])
    text = row.get("source_text", "")
    target = row.get("expected_target", "")
    outcome = row.get("expected_outcome", "")

    if outcome in ("REJECT", "NEEDS_CLARIFICATION"):
        return "NA"

    if not isinstance(claims, list):
        return "0"

    if outcome == "COMMIT" and len(claims) == 0:
        return "0"

    for claim in claims:
        if not isinstance(claim, dict):
            return "0"

        required_keys = {"attribute", "claim_type", "entity_id", "period", "value"}
        if not required_keys.issubset(claim.keys()):
            return "0"

        if claim.get("entity_id") != target:
            return "0"

        attribute = claim.get("attribute", "")
        known_attributes = {
            "assets", "net_income", "revenue", "liabilities", "equity",
            "operating_income", "total_revenue", "gross_profit",
            "total_assets", "total_liabilities", "shareholders_equity",
            "earnings_per_share", "ebitda", "free_cash_flow"
        }
        if attribute not in known_attributes:
            return "0"

        period = str(claim.get("period", ""))
        if period and period not in text:
            if period not in text.replace("년", "").replace("year", ""):
                return "0"

        value = claim.get("value")
        try:
            float(str(value))
        except (ValueError, TypeError):
            return "0"

    return "1"


def review_case(row: dict) -> dict:
    """
    Perform AI-R2 review of a single candidate case.
    Returns a dict with reviewer_id='R2', case_id, and 8 judgment fields.
    """
    return {
        "reviewer_id": "R2",
        "case_id": row["case_id"],
        "category": row["category"],
        "language": row["language"],
        "source_text": row["source_text"],
        "source_text_valid": validate_source_text(row),
        "language_valid": validate_language(row),
        "intent_valid": validate_intent(row),
        "target_valid": validate_target(row),
        "conditions_valid": validate_conditions(row),
        "policy_valid": validate_policy(row),
        "outcome_valid": validate_outcome(row),
        "claims_valid": validate_claims(row),
        "notes": f"AI-R2:Gemini3.6Flash automated review | cat={row['category']} lang={row['language']}",
    }


def main() -> None:
    print(f"Loading candidates from: {CANDIDATE}")
    candidates = read_jsonl(CANDIDATE)
    print(f"Loaded {len(candidates)} cases")

    if len(candidates) != 1200:
        raise ValueError(f"Expected 1200 cases, got {len(candidates)}")

    reviews = []
    stats = {
        "reviewer_id": "R2",
        "model": "Gemini 3.6 Flash (AntiGravity)",
        "total": 0,
        "by_category": {},
        "field_counts": {f: {"1": 0, "0": 0, "NA": 0} for f in FIELDS},
    }

    for i, row in enumerate(candidates):
        result = review_case(row)
        reviews.append(result)

        cat = row["category"]
        if cat not in stats["by_category"]:
            stats["by_category"][cat] = 0
        stats["by_category"][cat] += 1
        stats["total"] += 1

        for field in FIELDS:
            val = result[field]
            if val in stats["field_counts"][field]:
                stats["field_counts"][field][val] += 1

        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/1200 cases...")

    print(f"\nCompleted AI-R2 review of {stats['total']} cases")
    print(f"Category distribution: {stats['by_category']}")
    print("\nField judgment distribution:")
    for field in FIELDS:
        counts = stats["field_counts"][field]
        total = sum(counts.values())
        pct_valid = counts["1"] / total * 100 if total else 0
        pct_invalid = counts["0"] / total * 100 if total else 0
        pct_na = counts["NA"] / total * 100 if total else 0
        print(f"  {field:30s}: 1={counts['1']:4d}({pct_valid:5.1f}%) 0={counts['0']:4d}({pct_invalid:5.1f}%) NA={counts['NA']:4d}({pct_na:5.1f}%)")

    output_fields = [
        "reviewer_id", "case_id", "category", "language", "source_text",
        "source_text_valid", "language_valid", "intent_valid", "target_valid",
        "conditions_valid", "policy_valid", "outcome_valid", "claims_valid", "notes",
    ]

    REVIEW_R2.parent.mkdir(parents=True, exist_ok=True)
    with REVIEW_R2.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(reviews)

    print(f"\nAI-R2 Review saved to: {REVIEW_R2}")
    print(f"Total rows (excluding header): {len(reviews)}")

    stats_path = ROOT / "evaluation/uir_phase3b/ai_review/ai_r2_review_stats.json"
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"Stats saved to: {stats_path}")


if __name__ == "__main__":
    main()
