#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from semantic_error_taxonomy import TAXONOMY, classify


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", type=Path, default=Path("evaluation/uir_external/frozen_test_v1.jsonl")); parser.add_argument("--records", type=Path, default=Path("results/uir_slm/frozen_uir_core.jsonl")); parser.add_argument("--out", type=Path, default=Path("results/uir_phase3/v1_failure_taxonomy.csv")); args = parser.parse_args()
    cases = {row["case_id"]: row for row in read_jsonl(args.dataset)}; records = {row["case_id"]: row for row in read_jsonl(args.records)}; counts = Counter()
    details = []
    for case_id, case in cases.items():
        if not case["split"].startswith(("G2_", "G3_", "G4_")) or records[case_id]["semantic_match"]: continue
        error = classify(case, records[case_id]); counts[(case["split"], case["language"], error)] += 1; details.append({"case_id": case_id, "split": case["split"], "language": case["language"], "error_type": error})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"split": split, "language": language, "error_type": error, "count": counts[(split, language, error)]} for split in sorted({case["split"] for case in cases.values() if case["split"].startswith(("G2_", "G3_", "G4_"))}) for language in ("ko", "en") for error in TAXONOMY]
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["split", "language", "error_type", "count"]); writer.writeheader(); writer.writerows(rows)
    (args.out.parent / "v1_failure_details.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in details), encoding="utf-8")
    print(json.dumps({"failures": len(details), "dominant": Counter(row["error_type"] for row in details).most_common()}, sort_keys=True))


if __name__ == "__main__": main()
