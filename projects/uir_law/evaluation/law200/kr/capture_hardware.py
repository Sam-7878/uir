#!/usr/bin/env python3
"""Bind a post-run hardware observation to the frozen Korean test execution."""
from __future__ import annotations

import json

from evaluation.uir_law.law200.common import hardware_summary, read_json, sha256_file, utc_now, write_json
from evaluation.uir_law.law200.kr.validate_publication_results import KR_AGGREGATE_DIR, KR_RAW_DIR


def capture() -> dict:
    execution_path = KR_RAW_DIR / "test_execution_manifest_phi3-5-latest.json"
    execution = read_json(execution_path)
    artifact = {
        "schema": "law200-hardware-observation/1.0",
        "captured_at": utc_now(),
        "capture_timing": "post-run",
        "jurisdiction": "kr",
        "runtime_sha256": execution["runtime_sha256"],
        "execution_manifest_sha256": sha256_file(execution_path),
        "hardware": hardware_summary(),
    }
    write_json(KR_AGGREGATE_DIR / "hardware_environment.json", artifact)
    return artifact


if __name__ == "__main__":
    print(json.dumps(capture(), ensure_ascii=False, indent=2))
