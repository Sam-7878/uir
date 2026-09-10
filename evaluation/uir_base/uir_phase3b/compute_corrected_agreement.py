#!/usr/bin/env python3
"""
Compute corrected reviewer agreement statistics for R1-R2.
Fixes Critical Issue A: single-class fields report kappa=NA instead of 1.0.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW_DIR = ROOT / "evaluation/uir_phase3b/review"
OUT_DIR = ROOT / "results/uir_phase3c"

FIELDS = ("source_text_valid", "language_valid", "intent_valid", "target_valid",
          "conditions_valid", "policy_valid", "outcome_valid", "claims_valid")
ALLOWED = {"1", "0", "NA"}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def class_distribution(values: list[str]) -> str:
    """Summarize class distribution as string, e.g. '{1:1200}'."""
    counter = Counter(values)
    parts = [f"{k}:{v}" for k, v in sorted(counter.items())]
    return "{" + ", ".join(parts) + "}"


def is_single_class(values: list[str]) -> bool:
    """Check if all values belong to a single class."""
    return len(set(values)) <= 1


def cohens_kappa(left: list[str], right: list[str]) -> tuple[float, float | None, bool, str]:
    """
    Compute Cohen's kappa with correct handling of degenerate cases.
    Returns: (raw_agreement, kappa_or_None, kappa_defined, reason)
    """
    n = len(left)
    raw = sum(a == b for a, b in zip(left, right)) / n

    labels = sorted(ALLOWED)
    p_e = sum((left.count(v) / n) * (right.count(v) / n) for v in labels)

    if p_e >= 1.0:
        # Both reviewers used only one class → marginal variance is zero → kappa undefined
        return raw, None, False, "undefined_due_to_zero_marginal_variance"

    # Check if both reviewers used only a single class (even if different)
    if is_single_class(left) and is_single_class(right):
        if set(left) == set(right):
            return raw, None, False, "undefined_due_to_zero_marginal_variance"
        else:
            kappa = (raw - p_e) / (1 - p_e)
            return raw, kappa, True, "computed"

    kappa = (raw - p_e) / (1 - p_e)
    return raw, kappa, True, "computed"


def main() -> None:
    r1_rows = read_csv(REVIEW_DIR / "review_R1.csv")
    r2_rows = read_csv(REVIEW_DIR / "review_R2.csv")

    r1_by_id = {r["case_id"]: r for r in r1_rows}
    r2_by_id = {r["case_id"]: r for r in r2_rows}
    common = sorted(set(r1_by_id) & set(r2_by_id))

    print(f"R1 cases: {len(r1_rows)}, R2 cases: {len(r2_rows)}, common: {len(common)}")

    results = []
    for field in FIELDS:
        left = [r1_by_id[c][field].upper() for c in common]
        right = [r2_by_id[c][field].upper() for c in common]

        raw, kappa, defined, reason = cohens_kappa(left, right)
        results.append({
            "field": field,
            "n": len(common),
            "r1_class_distribution": class_distribution(left),
            "r2_class_distribution": class_distribution(right),
            "raw_agreement": f"{raw:.9f}",
            "cohens_kappa": f"{kappa:.9f}" if kappa is not None else "NA",
            "kappa_defined": str(defined).lower(),
            "kappa_reason": reason,
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "reviewer_agreement_corrected.csv"
    fieldnames = ["field", "n", "r1_class_distribution", "r2_class_distribution",
                  "raw_agreement", "cohens_kappa", "kappa_defined", "kappa_reason"]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nCorrected agreement saved to: {out_path}")
    for r in results:
        print(f"  {r['field']:30s}: raw={r['raw_agreement']} kappa={r['cohens_kappa']} ({r['kappa_reason']})")


if __name__ == "__main__":
    main()
