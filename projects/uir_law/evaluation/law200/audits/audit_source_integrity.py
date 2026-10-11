#!/usr/bin/env python3
"""Recompute every frozen CourtListener response and registry binding hash."""
from __future__ import annotations

import json
from typing import Any

from evaluation.uir_law.law200.common import DATA_DIR, PACKAGE_ROOT, canonical_json, read_jsonl, sha256_file, sha256_text, utc_now, write_json


def audit() -> dict[str, Any]:
    registry_path = DATA_DIR / "source_registry.jsonl"
    findings: list[dict[str, Any]] = []
    if not registry_path.exists():
        findings.append({"type": "missing_registry", "path": str(registry_path)})
        records: list[dict[str, Any]] = []
    else:
        records = read_jsonl(registry_path)
    raw_cache: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        relative = str(record.get("raw_response_file", ""))
        raw_path = PACKAGE_ROOT / relative
        if not raw_path.exists():
            findings.append({"type": "raw_response_missing", "citation": record.get("citation_canonical"), "path": relative})
            continue
        actual_batch_hash = sha256_file(raw_path)
        if actual_batch_hash != record.get("raw_batch_sha256"):
            findings.append({"type": "raw_batch_hash_mismatch", "citation": record.get("citation_canonical")})
            continue
        if relative not in raw_cache:
            content = json.loads(raw_path.read_bytes())
            raw_cache[relative] = content if isinstance(content, list) else []
        entry_hashes = {sha256_text(canonical_json(entry)) for entry in raw_cache[relative]}
        if record.get("response_sha256") not in entry_hashes:
            findings.append({"type": "entry_hash_not_in_raw_response", "citation": record.get("citation_canonical")})
        status = int(record.get("lookup_status", 0))
        if status not in {200, 404}:
            findings.append({"type": "disallowed_lookup_status", "citation": record.get("citation_canonical"), "status": status})
        if status == 200 and (not record.get("case_name") or record.get("courtlistener_cluster_id") is None):
            findings.append({"type": "incomplete_valid_entity", "citation": record.get("citation_canonical")})
        if status == 404 and not record.get("mutation"):
            findings.append({"type": "nonexistent_not_mutation_derived", "citation": record.get("citation_canonical")})
    valid_count = sum(int(row.get("lookup_status", 0)) == 200 for row in records)
    invalid_count = sum(int(row.get("lookup_status", 0)) == 404 for row in records)
    if records and (valid_count != 60 or invalid_count != 30):
        findings.append({"type": "registry_balance", "valid": valid_count, "not_found": invalid_count, "expected": [60, 30]})
    report = {
        "audit": "LAW200_SOURCE_INTEGRITY",
        "audited_at": utc_now(),
        "registry_records": len(records),
        "valid_200_records": valid_count,
        "nonexistent_404_records": invalid_count,
        "raw_response_files": len(raw_cache),
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }
    write_json(PACKAGE_ROOT / "results" / "aggregate" / "source_integrity_audit.json", report)
    return report


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, ensure_ascii=False))
