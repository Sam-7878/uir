#!/usr/bin/env python3
"""Prepare independent Phase-3B review sheets without supplying judgments."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELDS = (
    "source_text_valid", "language_valid", "intent_valid", "target_valid",
    "conditions_valid", "policy_valid", "outcome_valid", "claims_valid",
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=ROOT / "evaluation/uir_phase3b/candidate_v2_0.jsonl")
    parser.add_argument("--out", type=Path, default=ROOT / "evaluation/uir_phase3b/review")
    args = parser.parse_args()
    rows = read_jsonl(args.candidate)
    args.out.mkdir(parents=True, exist_ok=True)
    columns = ["case_id", "category", "language", "source_text", *FIELDS, "notes"]
    for reviewer in ("R1", "R2"):
        with (args.out / f"review_{reviewer}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["reviewer_id", *columns])
            writer.writeheader()
            for row in rows:
                writer.writerow({"reviewer_id": reviewer, "case_id": row["case_id"], "category": row["category"],
                                 "language": row["language"], "source_text": row["source_text"]})
    adjudication_columns = ["case_id", "field", "r1_value", "r2_value", "final_value", "reason",
                            "original_value", "adjudicated_value"]
    with (args.out / "adjudication.csv").open("w", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=adjudication_columns).writeheader()
    manifest = {"candidate_sha256": hashlib.sha256(args.candidate.read_bytes()).hexdigest(), "case_count": len(rows),
                "reviewers": ["R1", "R2"], "allowed_values": ["1", "0", "NA"], "fields": list(FIELDS),
                "review_status": "not_started", "judgments_prefilled": False}
    (args.out / "REVIEW_PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
