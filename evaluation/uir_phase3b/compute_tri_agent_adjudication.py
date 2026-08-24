#!/usr/bin/env python3
"""
Extract tri-agent disagreement cases and apply majority adjudication.
Produces ai3_disagreement_cases.csv and tri_agent_adjudication.csv.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW_DIR = ROOT / "evaluation/uir_phase3b/review"
OUT_DIR = ROOT / "results/uir_phase3c"

FIELDS = ("source_text_valid", "language_valid", "intent_valid", "target_valid",
          "conditions_valid", "policy_valid", "outcome_valid", "claims_valid")


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def classify_pattern(r1: str, r2: str, r3: str) -> str:
    """Classify the agreement pattern among three reviewers."""
    if r1 == r2 == r3:
        return "unanimous"
    if r1 == r2 and r2 != r3:
        return "R1==R2!=R3"
    if r1 == r3 and r1 != r2:
        return "R1==R3!=R2"
    if r2 == r3 and r1 != r2:
        return "R2==R3!=R1"
    return "all_three_disagree"


def majority_value(r1: str, r2: str, r3: str) -> str | None:
    """Compute majority value (2 out of 3). Returns None if all disagree."""
    if r1 == r2:
        return r1
    if r1 == r3:
        return r1
    if r2 == r3:
        return r2
    return None


def adjudication_status(pattern: str) -> str:
    """Determine adjudication status from pattern."""
    if pattern == "unanimous":
        return "unanimous"
    if pattern == "all_three_disagree":
        return "unresolved_tri_agent_disagreement"
    return "majority_ai_adjudicated"


def main() -> None:
    r1_rows = read_csv(REVIEW_DIR / "review_R1.csv")
    r2_rows = read_csv(REVIEW_DIR / "review_R2.csv")
    r3_rows = read_csv(REVIEW_DIR / "review_R3.csv")

    r1_by_id = {r["case_id"]: r for r in r1_rows}
    r2_by_id = {r["case_id"]: r for r in r2_rows}
    r3_by_id = {r["case_id"]: r for r in r3_rows}
    common = sorted(set(r1_by_id) & set(r2_by_id) & set(r3_by_id))

    print(f"Processing {len(common)} common cases across R1, R2, R3")

    disagreements = []
    adjudications = []
    pattern_counts = {}

    for case_id in common:
        for field in FIELDS:
            v1 = r1_by_id[case_id][field].upper()
            v2 = r2_by_id[case_id][field].upper()
            v3 = r3_by_id[case_id][field].upper()

            pattern = classify_pattern(v1, v2, v3)
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

            if pattern == "unanimous":
                # No disagreement, no adjudication needed (except for record)
                adjudications.append({
                    "case_id": case_id,
                    "field": field,
                    "r1_value": v1,
                    "r2_value": v2,
                    "r3_value": v3,
                    "final_value": v1,
                    "decision_basis": "unanimous",
                    "original_value": v1,
                    "adjudicated_value": v1,
                    "status": "unanimous",
                })
                continue

            # Disagreement found
            maj = majority_value(v1, v2, v3)
            status = adjudication_status(pattern)

            notes = f"pattern={pattern}"
            if pattern == "all_three_disagree":
                notes += " | all three reviewers gave different values"
            elif "R3" in pattern:
                notes += " | R3 disagrees with majority"
            else:
                notes += " | majority adjudication applied"

            disagreements.append({
                "case_id": case_id,
                "field": field,
                "r1_value": v1,
                "r2_value": v2,
                "r3_value": v3,
                "majority_value": maj if maj else "none",
                "agreement_pattern": pattern,
                "audit_notes": notes,
            })

            adjudications.append({
                "case_id": case_id,
                "field": field,
                "r1_value": v1,
                "r2_value": v2,
                "r3_value": v3,
                "final_value": maj if maj else "unresolved",
                "decision_basis": "majority_vote" if maj else "unresolved_requires_review",
                "original_value": v1,  # R1 value as baseline reference
                "adjudicated_value": maj if maj else "unresolved",
                "status": status,
            })

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write disagreement cases
    disagree_path = OUT_DIR / "ai3_disagreement_cases.csv"
    if disagreements:
        disagree_fields = ["case_id", "field", "r1_value", "r2_value", "r3_value",
                          "majority_value", "agreement_pattern", "audit_notes"]
        with disagree_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=disagree_fields)
            writer.writeheader()
            writer.writerows(disagreements)
    else:
        # Write header-only file
        with disagree_path.open("w", encoding="utf-8", newline="") as f:
            f.write("case_id,field,r1_value,r2_value,r3_value,majority_value,agreement_pattern,audit_notes\n")

    # Write adjudication records
    adj_path = OUT_DIR / "tri_agent_adjudication.csv"
    adj_fields = ["case_id", "field", "r1_value", "r2_value", "r3_value",
                  "final_value", "decision_basis", "original_value", "adjudicated_value", "status"]
    with adj_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=adj_fields)
        writer.writeheader()
        writer.writerows(adjudications)

    print(f"\nPattern distribution:")
    for pat, count in sorted(pattern_counts.items()):
        print(f"  {pat:30s}: {count}")
    print(f"\nDisagreement cases: {len(disagreements)}")
    print(f"Unresolved (all_three_disagree): {sum(1 for d in disagreements if d['agreement_pattern'] == 'all_three_disagree')}")
    print(f"\nDisagreement cases saved to: {disagree_path}")
    print(f"Adjudication records saved to: {adj_path}")


if __name__ == "__main__":
    main()
