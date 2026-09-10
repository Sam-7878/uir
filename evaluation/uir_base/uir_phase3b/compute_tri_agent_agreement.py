#!/usr/bin/env python3
"""
Compute tri-agent agreement statistics (R1, R2, R3).
Includes pairwise Cohen's kappa and Fleiss' kappa with degenerate-case handling.
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
    counter = Counter(values)
    parts = [f"{k}:{v}" for k, v in sorted(counter.items())]
    return "{" + ", ".join(parts) + "}"


def cohens_kappa_safe(left: list[str], right: list[str]) -> tuple[float | None, str]:
    """Compute Cohen's kappa with degenerate-case handling."""
    n = len(left)
    if n == 0:
        return None, "no_data"
    raw = sum(a == b for a, b in zip(left, right)) / n
    labels = sorted(ALLOWED)
    p_e = sum((left.count(v) / n) * (right.count(v) / n) for v in labels)
    if p_e >= 1.0:
        return None, "undefined_due_to_zero_marginal_variance"
    if len(set(left)) <= 1 and len(set(right)) <= 1 and set(left) == set(right):
        return None, "undefined_due_to_zero_marginal_variance"
    return (raw - p_e) / (1 - p_e), "computed"


def fleiss_kappa(ratings: list[list[str]]) -> tuple[float | None, str]:
    """
    Compute Fleiss' kappa for n raters.
    ratings: list of lists, each inner list = [r1_val, r2_val, r3_val, ...] for one subject.
    """
    n_subjects = len(ratings)
    n_raters = len(ratings[0]) if ratings else 0
    if n_subjects == 0 or n_raters < 2:
        return None, "no_data"

    categories = sorted(ALLOWED)
    k = len(categories)

    # Count category assignments per subject
    n_ij = []
    for subj_ratings in ratings:
        counts = Counter(subj_ratings)
        n_ij.append([counts.get(cat, 0) for cat in categories])

    # P_i for each subject
    p_i = []
    for row in n_ij:
        p_i.append((sum(x * x for x in row) - n_raters) / (n_raters * (n_raters - 1)))

    P_bar = sum(p_i) / n_subjects

    # p_j for each category
    p_j = []
    for j in range(k):
        total = sum(n_ij[i][j] for i in range(n_subjects))
        p_j.append(total / (n_subjects * n_raters))

    P_e_bar = sum(p * p for p in p_j)

    if P_e_bar >= 1.0:
        return None, "undefined_due_to_zero_marginal_variance"

    kappa = (P_bar - P_e_bar) / (1 - P_e_bar)
    return kappa, "computed"


def main() -> None:
    r1_rows = read_csv(REVIEW_DIR / "review_R1.csv")
    r2_rows = read_csv(REVIEW_DIR / "review_R2.csv")
    r3_rows = read_csv(REVIEW_DIR / "review_R3.csv")

    r1_by_id = {r["case_id"]: r for r in r1_rows}
    r2_by_id = {r["case_id"]: r for r in r2_rows}
    r3_by_id = {r["case_id"]: r for r in r3_rows}
    common = sorted(set(r1_by_id) & set(r2_by_id) & set(r3_by_id))

    print(f"R1: {len(r1_rows)}, R2: {len(r2_rows)}, R3: {len(r3_rows)}, common: {len(common)}")

    results = []
    for field in FIELDS:
        v1 = [r1_by_id[c][field].upper() for c in common]
        v2 = [r2_by_id[c][field].upper() for c in common]
        v3 = [r3_by_id[c][field].upper() for c in common]

        # Pairwise kappas
        k12, reason12 = cohens_kappa_safe(v1, v2)
        k13, reason13 = cohens_kappa_safe(v1, v3)
        k23, reason23 = cohens_kappa_safe(v2, v3)

        # Three-way raw agreement
        raw_3way = sum(a == b == c for a, b, c in zip(v1, v2, v3)) / len(common) if common else 0.0

        # Fleiss' kappa
        ratings = [[a, b, c] for a, b, c in zip(v1, v2, v3)]
        fk, fk_reason = fleiss_kappa(ratings)

        # Determine overall kappa_defined and reason
        all_single = (len(set(v1)) <= 1 and len(set(v2)) <= 1 and len(set(v3)) <= 1
                      and set(v1) == set(v2) == set(v3))
        kappa_defined = not all_single and any(x is not None for x in [k12, k13, k23, fk])
        kappa_reason = "undefined_due_to_zero_marginal_variance" if all_single else (
            fk_reason if fk is not None else "mixed")

        results.append({
            "field": field,
            "n": len(common),
            "r1_class_distribution": class_distribution(v1),
            "r2_class_distribution": class_distribution(v2),
            "r3_class_distribution": class_distribution(v3),
            "raw_three_way_agreement": f"{raw_3way:.9f}",
            "r1_r2_kappa": f"{k12:.9f}" if k12 is not None else "NA",
            "r1_r3_kappa": f"{k13:.9f}" if k13 is not None else "NA",
            "r2_r3_kappa": f"{k23:.9f}" if k23 is not None else "NA",
            "fleiss_kappa": f"{fk:.9f}" if fk is not None else "NA",
            "kappa_defined": str(kappa_defined).lower(),
            "kappa_reason": kappa_reason,
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "tri_agent_agreement.csv"
    fieldnames = ["field", "n", "r1_class_distribution", "r2_class_distribution", "r3_class_distribution",
                  "raw_three_way_agreement", "r1_r2_kappa", "r1_r3_kappa", "r2_r3_kappa",
                  "fleiss_kappa", "kappa_defined", "kappa_reason"]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nTri-agent agreement saved to: {out_path}")
    for r in results:
        print(f"  {r['field']:30s}: 3way={r['raw_three_way_agreement']} "
              f"R1R2={r['r1_r2_kappa']} R1R3={r['r1_r3_kappa']} R2R3={r['r2_r3_kappa']} "
              f"Fleiss={r['fleiss_kappa']} ({r['kappa_reason']})")


if __name__ == "__main__":
    main()
