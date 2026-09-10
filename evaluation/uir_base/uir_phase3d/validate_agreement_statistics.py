#!/usr/bin/env python3
"""Cross-check generated kappa statistics with independent libraries."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import sklearn
import statsmodels
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats.inter_rater import fleiss_kappa

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/uir_phase3d"
FIELDS = (
    "source_text_valid", "language_valid", "intent_valid", "target_valid",
    "conditions_valid", "policy_valid", "outcome_valid", "claims_valid",
)
REVIEWERS = ("R1", "R2", "R3")
LABELS = ("0", "1", "NA")


def main() -> int:
    judgments = {}
    for reviewer in REVIEWERS:
        path = OUT / f"actual_ai_review_{reviewer}.jsonl"
        judgments[reviewer] = {
            row["case_id"]: row["judgment"]
            for row in map(json.loads, path.read_text(encoding="utf-8").splitlines())
        }
    with (OUT / "actual_ai_agreement.csv").open(encoding="utf-8", newline="") as handle:
        stored = {row["field"]: row for row in csv.DictReader(handle)}

    checks = []
    for field in FIELDS:
        case_ids = sorted(judgments["R1"])
        values = [
            [str(judgments[reviewer][case_id][field]).upper() for reviewer in REVIEWERS]
            for case_id in case_ids
        ]
        counts = [[row.count(label) for label in LABELS] for row in values]
        expected = stored[field]
        if expected["fleiss_kappa"] != "NA":
            actual = float(fleiss_kappa(counts, method="fleiss"))
            checks.append({
                "field": field, "statistic": "fleiss_kappa", "stored": float(expected["fleiss_kappa"]),
                "independent": actual, "absolute_delta": abs(actual - float(expected["fleiss_kappa"])),
            })
        for left, right, column in (
            ("R1", "R2", "AI-R1_AI-R2_kappa"),
            ("R1", "R3", "AI-R1_AI-R3_kappa"),
            ("R2", "R3", "AI-R2_AI-R3_kappa"),
        ):
            if expected[column] == "NA":
                continue
            left_index, right_index = REVIEWERS.index(left), REVIEWERS.index(right)
            actual = float(cohen_kappa_score(
                [row[left_index] for row in values], [row[right_index] for row in values], labels=LABELS,
            ))
            checks.append({
                "field": field, "statistic": column, "stored": float(expected[column]),
                "independent": actual, "absolute_delta": abs(actual - float(expected[column])),
            })

    tolerance = 1e-12
    max_delta = max((check["absolute_delta"] for check in checks), default=0.0)
    result = {
        "status": "PASS" if max_delta < tolerance else "FAIL",
        "independent_library_checks": len(checks),
        "max_absolute_delta": max_delta,
        "tolerance": tolerance,
        "libraries": {"scikit-learn": sklearn.__version__, "statsmodels": statsmodels.__version__},
        "checks": checks,
    }
    (OUT / "agreement_statistics_validation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
