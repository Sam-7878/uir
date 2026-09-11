#!/usr/bin/env python3
"""Strict publication gate for the frozen LAW-200 benchmark."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from evaluation.uir_law.law200.audits.audit_dataset_duplicates import audit as duplicate_audit
from evaluation.uir_law.law200.audits.audit_gold_access import audit as gold_access_audit
from evaluation.uir_law.law200.audits.audit_source_integrity import audit as source_integrity_audit
from evaluation.uir_law.law200.baselines import PIPELINES
from evaluation.uir_law.law200.common import (
    AGGREGATE_DIR,
    CORPUS_DIR,
    DATA_DIR,
    FORBIDDEN_RUNTIME_KEYS,
    PACKAGE_ROOT,
    RAW_DIR,
    TABLES_DIR,
    canonical_json,
    read_json,
    read_jsonl,
    sha256_file,
    utc_now,
    write_json,
)
from evaluation.uir_law.law200.legal_ir import compile_legal_uir
from evaluation.uir_law.law200.scoring.score_supported_claims import aggregate, score_record


class Validator:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def check(self, condition: bool, name: str, detail: Any) -> None:
        self.checks.append({"name": name, "status": "PASS" if condition else "FAIL", "detail": detail})

    @property
    def blockers(self) -> list[dict[str, Any]]:
        return [item for item in self.checks if item["status"] == "FAIL"]


def close_enough(left: Any, right: Any, tolerance: float = 1e-12) -> bool:
    if left is None or right is None:
        return left is right
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return left == right


def validate() -> dict[str, Any]:
    validator = Validator()
    runtime_path = DATA_DIR / "law200_test_runtime.jsonl"
    gold_path = DATA_DIR / "law200_test_gold.jsonl"
    registry_path = DATA_DIR / "source_registry.jsonl"
    corpus_path = CORPUS_DIR / "legal_cases.jsonl"
    manifest_path = PACKAGE_ROOT / "benchmark_manifest.json"
    required_inputs = (runtime_path, gold_path, registry_path, corpus_path, manifest_path)
    validator.check(all(path.exists() for path in required_inputs), "required_frozen_inputs", [str(path) for path in required_inputs if not path.exists()])
    if not all(path.exists() for path in required_inputs):
        return finish(validator)

    runtime = read_jsonl(runtime_path)
    gold = read_jsonl(gold_path)
    manifest = read_json(manifest_path)
    validator.check(len(runtime) == 200 and len(gold) == 200, "exactly_200_test_cases", {"runtime": len(runtime), "gold": len(gold)})
    runtime_ids = [row.get("case_id") for row in runtime]
    gold_ids = [row.get("case_id") for row in gold]
    validator.check(set(runtime_ids) == set(gold_ids) and len(set(runtime_ids)) == 200, "runtime_gold_case_alignment", "opaque IDs are a one-to-one match")
    validator.check(
        all(not (set(row) & FORBIDDEN_RUNTIME_KEYS) for row in runtime),
        "gold_labels_absent_from_runtime",
        "forbidden key intersection must be empty",
    )
    category_counts = Counter(row.get("category") for row in gold)
    language_counts = Counter(row.get("language") for row in gold)
    validator.check(set(category_counts.values()) == {50} and len(category_counts) == 4, "category_balance", dict(category_counts))
    validator.check(language_counts == {"en": 100, "ko": 100}, "language_balance", dict(language_counts))
    validator.check(len({row["query"] for row in runtime}) == 200, "unique_runtime_queries", "200 unique queries required")
    validator.check(
        manifest.get("hashes", {}).get(runtime_path.name) == sha256_file(runtime_path),
        "frozen_test_hash",
        sha256_file(runtime_path),
    )
    validator.check(manifest.get("source_registry_sha256") == sha256_file(registry_path), "frozen_source_registry_hash", sha256_file(registry_path))
    validator.check(manifest.get("corpus_sha256") == sha256_file(corpus_path), "frozen_corpus_hash", sha256_file(corpus_path))

    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    runtime_by_id = {row["case_id"]: row for row in runtime}
    for row in gold:
        by_pair[str(row["pair_id"])].append(row)
    equivalent = 0
    for pair in by_pair.values():
        if len(pair) != 2:
            continue
        left = compile_legal_uir(runtime_by_id[pair[0]["case_id"]]["query"])
        right = compile_legal_uir(runtime_by_id[pair[1]["case_id"]]["query"])
        if (left.domain, left.intent, left.entity_type, left.citation, left.claimed_case_name) == (
            right.domain, right.intent, right.entity_type, right.citation, right.claimed_case_name
        ):
            equivalent += 1
    validator.check(equivalent == 100, "cross_lingual_uir_equivalence", {"equivalent_pairs": equivalent, "pairs": len(by_pair)})

    for name, result in (
        ("source_integrity_audit", source_integrity_audit()),
        ("gold_access_audit", gold_access_audit()),
        ("dataset_duplicate_audit", duplicate_audit()),
    ):
        validator.check(result["status"] == "PASS", name, result.get("findings", []))

    raw_by_pipeline: dict[str, list[dict[str, Any]]] = {}
    for pipeline in PIPELINES:
        matches = sorted(RAW_DIR.glob(f"test_{pipeline}_*.jsonl"))
        validator.check(len(matches) == 1, f"raw_file_{pipeline}", [str(path) for path in matches])
        if len(matches) != 1:
            continue
        rows = read_jsonl(matches[0])
        raw_by_pipeline[pipeline] = rows
        validator.check(len(rows) == 200, f"raw_rows_{pipeline}", len(rows))
        validator.check({row.get("case_id") for row in rows} == set(runtime_ids), f"same_cases_{pipeline}", "case-ID set must match frozen runtime")
        validator.check(all("final_output" in row and row.get("model_calls") is not None for row in rows), f"raw_output_complete_{pipeline}", "each row needs raw model evidence or explicit pre-model rejection")

    configs = {
        canonical_json(row.get("model_config"))
        for rows in raw_by_pipeline.values() for row in rows
    }
    validator.check(len(configs) == 1 and bool(configs), "same_backbone_and_configuration", list(configs))

    metrics_path = AGGREGATE_DIR / "test_metrics.json"
    statistics_path = AGGREGATE_DIR / "test_statistics.json"
    validator.check(metrics_path.exists() and statistics_path.exists(), "aggregate_and_statistics_present", {"metrics": metrics_path.exists(), "statistics": statistics_path.exists()})
    recomputed: list[dict[str, Any]] = []
    gold_by_id = {row["case_id"]: row for row in gold}
    for pipeline, rows in sorted(raw_by_pipeline.items()):
        scored = [score_record(row, gold_by_id[row["case_id"]]) for row in rows if row["case_id"] in gold_by_id]
        if scored:
            recomputed.append(aggregate(scored))
    if metrics_path.exists():
        stored = {row["pipeline"]: row for row in read_json(metrics_path).get("pipelines", [])}
        metric_keys = (
            "accepted_unsupported_legal_claim_rate", "invalid_citation_far",
            "verified_answer_coverage", "false_rejection_rate", "model_invocation_rate",
        )
        matches = len(stored) == len(recomputed)
        for row in recomputed:
            prior = stored.get(row["pipeline"], {})
            matches = matches and all(close_enough(row.get(key), prior.get(key)) for key in metric_keys)
            matches = matches and row["accepted_unsupported_wilson"] == prior.get("accepted_unsupported_wilson")
        validator.check(matches, "aggregates_recomputed_from_raw", "stored metrics and Wilson intervals must exactly reproduce")

    csv_path = TABLES_DIR / "law200_main_table.csv"
    md_path = TABLES_DIR / "law200_main_table.md"
    validator.check(csv_path.exists() and md_path.exists(), "paper_facing_tables_present", {"csv": csv_path.exists(), "md": md_path.exists()})
    if csv_path.exists():
        with csv_path.open(encoding="utf-8", newline="") as handle:
            table_rows = {row["pipeline"]: row for row in csv.DictReader(handle)}
        table_ok = len(table_rows) == len(recomputed)
        for row in recomputed:
            table = table_rows.get(row["pipeline"], {})
            table_ok = table_ok and all(
                close_enough(row.get(key), table.get(key))
                for key in ("accepted_unsupported_legal_claim_rate", "invalid_citation_far", "verified_answer_coverage", "false_rejection_rate")
            )
        validator.check(table_ok, "paper_table_recomputed_not_manual", "CSV values must match raw-record recomputation")
    if md_path.exists():
        validator.check("AUTO-GENERATED" in md_path.read_text(encoding="utf-8"), "markdown_table_generation_marker", "auto-generation marker required")
    return finish(validator)


def finish(validator: Validator) -> dict[str, Any]:
    status = "READY_FOR_KAIC_MANUSCRIPT" if not validator.blockers else "NOT_READY"
    report = {
        "validator": "LAW-200 publication gate 1.0",
        "validated_at": utc_now(),
        "status": status,
        "checks": validator.checks,
        "blocker_count": len(validator.blockers),
    }
    write_json(AGGREGATE_DIR / "publication_validation.json", report)
    lines = [
        "# LAW-200 Audit Report", "", f"Status: **{status}**", "",
        f"Validated: {report['validated_at']}", "", "## Checks", "",
    ]
    for item in validator.checks:
        lines.append(f"- [{ 'x' if item['status'] == 'PASS' else ' ' }] {item['name']}: `{item['status']}` — {item['detail']}")
    (PACKAGE_ROOT / "LAW200_AUDIT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> None:
    result = validate()
    print(json.dumps({"status": result["status"], "blocker_count": result["blocker_count"]}, indent=2))
    if result["status"] == "READY_FOR_KAIC_MANUSCRIPT":
        print("READY_FOR_KAIC_MANUSCRIPT")
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
