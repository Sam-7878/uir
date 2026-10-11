#!/usr/bin/env python3
"""Verify sanitized runtime rows and recorded pre-generation file access."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.uir_law.law200.common import DATA_DIR, FORBIDDEN_RUNTIME_KEYS, PACKAGE_ROOT, RAW_DIR, read_json, read_jsonl, utc_now, write_json


def nested_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(nested_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(nested_keys(item) for item in value), set())
    return set()


def audit() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    rows_checked = 0
    for split in ("dev", "test"):
        path = DATA_DIR / f"law200_{split}_runtime.jsonl"
        if not path.exists():
            findings.append({"type": "missing_runtime", "path": str(path)})
            continue
        rows = read_jsonl(path)
        rows_checked += len(rows)
        for row in rows:
            leaked = sorted(nested_keys(row) & FORBIDDEN_RUNTIME_KEYS)
            if leaked:
                findings.append({"type": "runtime_label_leak", "case_id": row.get("case_id"), "keys": leaked})
    access_logs = sorted(RAW_DIR.glob("*_pre_generation_access_log.json"))
    access_violations = 0
    for path in access_logs:
        log = read_json(path)
        for entry in log.get("pre_generation_files_read", []):
            accessed = str(entry.get("path", "")).lower()
            if "gold" in accessed or "oracle" in accessed or "scoring" in accessed:
                access_violations += 1
                findings.append({"type": "forbidden_pre_generation_access", "log": str(path), "path": accessed})
    report = {
        "audit": "LAW200_GOLD_ACCESS",
        "audited_at": utc_now(),
        "runtime_rows_checked": rows_checked,
        "access_logs_checked": len(access_logs),
        "forbidden_pre_generation_gold_access": access_violations,
        "runtime_label_leakage_findings": sum(item["type"] == "runtime_label_leak" for item in findings),
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }
    write_json(PACKAGE_ROOT / "results" / "aggregate" / "gold_access_audit.json", report)
    return report


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, indent=2, ensure_ascii=False))
