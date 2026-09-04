#!/usr/bin/env python3
"""Pre-register internal and official Phase-4C inputs before model execution.

Runtime files intentionally exclude benchmark answers, programs, expected claims,
and hallucination labels. Those fields remain in immutable official/internal source
files and are opened only by the post-generation scorer.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.uir_phase4c.common import (
    FROZEN_DIR, RESULTS_DIR, ROOT, SEED, SOURCE_DIR, row_hash, sha256_file,
    write_json, write_jsonl,
)

FINQA_COMMIT = "0f16e2867befa6840783e58be38c9efb9229d742"
HALUEVAL_COMMIT = "b7253db3cdaa0ab2c382f92b26b390109174f77e"
FINQA_SOURCE = SOURCE_DIR / "FinQA/test.json"
HALUEVAL_SOURCE = SOURCE_DIR / "HaluEval/qa_data.json"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _internal_sources() -> list[dict[str, Any]]:
    paths = (
        ("frozen_v2", ROOT / "results/uir_phase3b/frozen_test_v2.jsonl"),
        ("real_fact", ROOT / "results/uir_phase3b/real_fact_subset.jsonl"),
        ("frozen_v1", ROOT / "evaluation/uir_external/frozen_test_v1.jsonl"),
    )
    rows: list[dict[str, Any]] = []
    for dataset, path in paths:
        for row in _load_jsonl(path):
            copied = dict(row)
            copied["_source_dataset"] = dataset
            copied["_source_file"] = str(path.relative_to(ROOT))
            copied["_source_row_hash"] = row_hash(row)
            rows.append(copied)
    return rows


def _stratum(row: dict[str, Any]) -> str:
    category = row.get("category", "")
    dataset = row["_source_dataset"]
    if category == "invalid_entity" or row.get("entity_valid") is False:
        return "invalid_entity"
    if category == "adversarial":
        return "adversarial"
    if category == "policy_conflict":
        return "policy_violation"
    if category in {"structural_unseen", "ambiguous_incomplete", "ambiguous"}:
        return "condition_heavy"
    if category == "numeric_provenance" or dataset == "real_fact":
        return "numeric_provenance"
    return "valid_benign"


def _balanced_take(rows: list[dict[str, Any]], count: int, rng: random.Random) -> list[dict[str, Any]]:
    ko = [row for row in rows if row.get("language") == "ko"]
    en = [row for row in rows if row.get("language") == "en"]
    other = [row for row in rows if row.get("language") not in {"ko", "en"}]
    for group in (ko, en, other):
        rng.shuffle(group)
    selected = ko[: count // 2] + en[: count // 2]
    needed = count - len(selected)
    pool = ko[count // 2 :] + en[count // 2 :] + other
    rng.shuffle(pool)
    selected.extend(pool[:needed])
    if len(selected) != count:
        raise ValueError(f"stratum has {len(selected)} rows, expected {count}")
    return selected


def _runtime_internal(row: dict[str, Any]) -> dict[str, Any]:
    semantics = row.get("expected_semantics") or {}
    facts = row.get("context_claims") or []
    return {
        "case_id": row["case_id"],
        "source_dataset": row["_source_dataset"],
        "source_file": row["_source_file"],
        "source_row_hash": row["_source_row_hash"],
        "stratum": _stratum(row),
        "language": row.get("language", "unknown"),
        "input": row.get("input") or row.get("source_text") or "",
        "requested_entity": semantics.get("target") or row.get("expected_target") or "",
        "requested_attribute": semantics.get("metric") or "",
        "requested_period": str(semantics.get("period") or ""),
        "context_claims": facts,
        "runtime_entity_exists": bool(row.get("entity_valid", True)),
        "runtime_policy_permit": bool(row.get("policy_valid", True)),
        "runtime_uir_compiles": bool(row.get("uir_ready", row.get("expected_outcome") == "COMMIT")),
    }


def _score_internal(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": row["case_id"],
        "source_row_hash": row["_source_row_hash"],
        "stratum": _stratum(row),
        "expected_claims": row.get("expected_claims") or row.get("context_claims") or [],
        "expected_outcome": row.get("expected_outcome", "COMMIT"),
        "is_adversarial": row.get("category") == "adversarial",
        "is_invalid_entity": row.get("entity_valid") is False or row.get("category") == "invalid_entity",
        "is_policy_violation": row.get("policy_valid") is False,
        "numeric_eligible": bool(row.get("expected_claims") or row.get("context_claims")),
    }


def freeze_internal() -> dict[str, Any]:
    rng = random.Random(SEED)
    rows = _internal_sources()
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        buckets.setdefault(_stratum(row), []).append(row)
    full_plan = {"valid_benign": 250, "condition_heavy": 100, "policy_violation": 50, "adversarial": 50, "numeric_provenance": 100, "invalid_entity": 50}
    smoke_plan = {"valid_benign": 40, "condition_heavy": 15, "policy_violation": 10, "adversarial": 10, "numeric_provenance": 15, "invalid_entity": 10}
    selected: list[dict[str, Any]] = []
    by_stratum: dict[str, list[dict[str, Any]]] = {}
    for name, count in full_plan.items():
        chosen = _balanced_take(buckets.get(name, []), count, rng)
        by_stratum[name] = chosen
        selected.extend(chosen)
    selected.sort(key=lambda row: row["case_id"])
    smoke: list[dict[str, Any]] = []
    smoke_rng = random.Random(SEED + 1)
    for name, count in smoke_plan.items():
        smoke.extend(_balanced_take(by_stratum[name], count, smoke_rng))
    smoke.sort(key=lambda row: row["case_id"])
    write_jsonl(FROZEN_DIR / "strong_runtime_600.jsonl", (_runtime_internal(row) for row in selected))
    write_jsonl(FROZEN_DIR / "strong_scoring_600.jsonl", (_score_internal(row) for row in selected))
    write_jsonl(FROZEN_DIR / "smoke_runtime_100.jsonl", (_runtime_internal(row) for row in smoke))
    write_jsonl(FROZEN_DIR / "smoke_scoring_100.jsonl", (_score_internal(row) for row in smoke))
    return {
        "seed": SEED, "full_plan": full_plan, "smoke_plan": smoke_plan,
        "full_runtime_sha256": sha256_file(FROZEN_DIR / "strong_runtime_600.jsonl"),
        "full_scoring_sha256": sha256_file(FROZEN_DIR / "strong_scoring_600.jsonl"),
        "smoke_runtime_sha256": sha256_file(FROZEN_DIR / "smoke_runtime_100.jsonl"),
        "smoke_scoring_sha256": sha256_file(FROZEN_DIR / "smoke_scoring_100.jsonl"),
    }


def freeze_finqa() -> list[dict[str, Any]]:
    rows = json.loads(FINQA_SOURCE.read_text(encoding="utf-8"))
    indices = sorted(random.Random(SEED).sample(range(len(rows)), 200))
    runtime, mapping = [], []
    source_sha = sha256_file(FINQA_SOURCE)
    for index in indices:
        row = rows[index]
        source_hash = row_hash(row)
        case_id = f"FINQA-OFFICIAL-{index:04d}"
        runtime.append({"case_id": case_id, "source_dataset": "FinQA", "source_original_id": row["id"], "source_index": index, "source_file_sha256": source_sha, "source_row_hash": source_hash, "filename": row.get("filename", ""), "question": row["qa"]["question"], "pre_text": row.get("pre_text", []), "post_text": row.get("post_text", []), "table": row.get("table", [])})
        mapping.append({"case_id": case_id, "source_original_id": row["id"], "source_index": index, "source_row_hash": source_hash})
    write_jsonl(FROZEN_DIR / "finqa_runtime_200.jsonl", runtime)
    return mapping


def freeze_halueval() -> list[dict[str, Any]]:
    rows = _load_jsonl(HALUEVAL_SOURCE)
    indices = sorted(random.Random(SEED).sample(range(len(rows)), 200))
    runtime, mapping = [], []
    source_sha = sha256_file(HALUEVAL_SOURCE)
    for position, index in enumerate(indices):
        row = rows[index]
        source_hash = row_hash(row)
        case_id = f"HALUEVAL-QA-OFFICIAL-{index:05d}"
        candidate = row["right_answer"] if position % 2 == 0 else row["hallucinated_answer"]
        runtime.append({"case_id": case_id, "source_dataset": "HaluEval-QA", "source_original_id": f"qa_data.json:{index}", "source_index": index, "source_file_sha256": source_sha, "source_row_hash": source_hash, "knowledge": row["knowledge"], "question": row["question"], "candidate_answer": candidate})
        mapping.append({"case_id": case_id, "source_original_id": f"qa_data.json:{index}", "source_index": index, "source_row_hash": source_hash})
    write_jsonl(FROZEN_DIR / "halueval_qa_runtime_200.jsonl", runtime)
    return mapping


def main() -> None:
    for required in (FINQA_SOURCE, HALUEVAL_SOURCE):
        if not required.exists():
            raise FileNotFoundError(f"official frozen source missing: {required}")
    internal = freeze_internal()
    finqa_mapping = freeze_finqa()
    halueval_mapping = freeze_halueval()
    provenance = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "selection_seed": SEED,
        "sources": {
            "FinQA": {"repository_url": "https://github.com/czyssrs/FinQA", "git_commit": FINQA_COMMIT, "file": str(FINQA_SOURCE.relative_to(ROOT)), "file_sha256": sha256_file(FINQA_SOURCE), "license": "Apache-2.0", "selected_rows": len(finqa_mapping)},
            "HaluEval-QA": {"repository_url": "https://github.com/RUCAIBox/HaluEval", "git_commit": HALUEVAL_COMMIT, "file": str(HALUEVAL_SOURCE.relative_to(ROOT)), "file_sha256": sha256_file(HALUEVAL_SOURCE), "license": "MIT", "selected_rows": len(halueval_mapping)},
        },
        "internal_campaign": internal,
        "mappings": {"FinQA": finqa_mapping, "HaluEval-QA": halueval_mapping},
    }
    write_json(RESULTS_DIR / "OFFICIAL_BENCHMARK_PROVENANCE.json", provenance)
    write_json(FROZEN_DIR / "freeze_manifest.json", provenance)
    print(json.dumps({"status": "FROZEN", "internal": 600, "finqa": 200, "halueval": 200}, sort_keys=True))


if __name__ == "__main__":
    main()
