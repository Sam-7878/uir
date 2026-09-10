#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

REQUIRED = {"case_id", "category", "language", "input", "expected_claims", "template_id", "generator_id", "generation_method", "human_reviewed", "split"}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", type=Path, default=Path("evaluation/uir_external/frozen_test_v1.jsonl")); parser.add_argument("--manifest", type=Path, default=Path("evaluation/uir_external/FROZEN_TEST_MANIFEST.json")); args = parser.parse_args(); raw = args.dataset.read_bytes(); rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]; manifest = json.loads(args.manifest.read_text())
    errors = []
    if hashlib.sha256(raw).hexdigest() != manifest["dataset_sha256"]: errors.append("dataset hash mismatch")
    if len(rows) != 1000 or manifest["case_count"] != 1000: errors.append("frozen set must contain 1000 cases")
    if len({row["case_id"] for row in rows}) != len(rows): errors.append("duplicate case_id")
    for row in rows:
        missing = REQUIRED - set(row)
        if missing: errors.append(f"{row.get('case_id')}: missing {sorted(missing)}")
    dev = set(manifest["dev_template_ids"]); frozen = set(manifest["frozen_template_ids"])
    if dev & frozen: errors.append(f"template leakage: {sorted(dev & frozen)}")
    if Counter(row["language"] for row in rows) != Counter({"ko": 500, "en": 500}): errors.append("language balance mismatch")
    expected_splits = {name: 200 for name in ["G1_TEMPLATE_SEEN_ENTITY_UNSEEN", "G2_TEMPLATE_UNSEEN_ENTITY_SEEN", "G3_TEMPLATE_UNSEEN_ENTITY_UNSEEN", "G4_LEXICAL_UNSEEN", "G5_STRUCTURAL_UNSEEN"]}
    if Counter(row["split"] for row in rows) != Counter(expected_splits): errors.append("generalization split mismatch")
    result = {"status": "failed" if errors else "passed", "case_count": len(rows), "dataset_sha256": hashlib.sha256(raw).hexdigest(), "template_overlap_count": len(dev & frozen), "errors": errors}
    print(json.dumps(result, sort_keys=True));
    if errors: raise SystemExit(1)


if __name__ == "__main__": main()
