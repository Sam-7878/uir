#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--input", type=Path, default=Path("results/uir_phase3/v1_failure_taxonomy.csv")); parser.add_argument("--out", type=Path, default=Path("docs/work_reports/uir_phase3/V1_DIAGNOSTIC.md")); args = parser.parse_args()
    with args.input.open(encoding="utf-8") as handle: rows = list(csv.DictReader(handle))
    totals = Counter(); split_totals = Counter()
    for row in rows:
        count = int(row["count"]); totals[row["error_type"]] += count; split_totals[(row["split"], row["language"])] += count
    lines = ["# Phase-2 Frozen-v1 Semantic Failure Diagnostic", "", "Frozen-v1 is a retrospective diagnostic benchmark after Phase-2 and must not be described as the Phase-3 unseen holdout.", "", "## Taxonomy", "", "| Error type | Failures |", "|---|---:|"]
    lines.extend(f"| {error} | {count} |" for error, count in totals.most_common())
    lines.extend(["", "## G2–G4 failure counts", "", "| Split | Language | Failures |", "|---|---|---:|"])
    lines.extend(f"| {split} | {language} | {count} |" for (split, language), count in sorted(split_totals.items()))
    lines.extend(["", "## Interpretation", "", "The taxonomy is diagnostic, rule-based, and auditable. It is used to improve semantic categories rather than to add case IDs or entity instances to the parser."])
    args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
