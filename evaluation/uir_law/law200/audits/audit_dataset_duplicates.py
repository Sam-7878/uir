#!/usr/bin/env python3
"""Check case/query uniqueness and dev/test separation."""
from __future__ import annotations

import json
from collections import Counter
from typing import Any

from evaluation.uir_law.law200.common import DATA_DIR, PACKAGE_ROOT, read_jsonl, utc_now, write_json


def duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def audit() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    splits: dict[str, list[dict[str, Any]]] = {}
    for split in ("dev", "test"):
        path = DATA_DIR / f"law200_{split}_runtime.jsonl"
        if not path.exists():
            findings.append({"type": "missing_runtime", "split": split})
            splits[split] = []
            continue
        rows = read_jsonl(path)
        splits[split] = rows
        for field in ("case_id", "query"):
            found = duplicates([str(row[field]) for row in rows])
            if found:
                findings.append({"type": f"duplicate_{field}", "split": split, "values": found})
    overlap_ids = sorted({row["case_id"] for row in splits["dev"]} & {row["case_id"] for row in splits["test"]})
    overlap_queries = sorted({row["query"] for row in splits["dev"]} & {row["query"] for row in splits["test"]})
    if overlap_ids:
        findings.append({"type": "dev_test_case_id_overlap", "values": overlap_ids})
    if overlap_queries:
        findings.append({"type": "dev_test_query_overlap", "values": overlap_queries})
    report = {
        "audit": "LAW200_DATASET_DUPLICATES",
        "audited_at": utc_now(),
        "dev_rows": len(splits["dev"]),
        "test_rows": len(splits["test"]),
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }
    write_json(PACKAGE_ROOT / "results" / "aggregate" / "dataset_duplicate_audit.json", report)
    return report


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, ensure_ascii=False))
