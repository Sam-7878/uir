#!/usr/bin/env python3
"""Strict publication gate for the independent Korean LAW-KR-200 stratum."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from evaluation.uir_law.law200.baselines import PIPELINES
from evaluation.uir_law.law200.common import (
    FORBIDDEN_RUNTIME_KEYS,
    PACKAGE_ROOT,
    REPO_ROOT,
    canonical_json,
    read_json,
    read_jsonl,
    sha256_file,
    sha256_text,
    utc_now,
    write_json,
)
from evaluation.uir_law.law200.kr.law_go_kr import KR_DATA_DIR, exact_case_number, result_rows, SearchSnapshot
from evaluation.uir_law.law200.legal_ir import compile_legal_uir
from evaluation.uir_law.law200.scoring.score_supported_claims import aggregate, score_record, statistics

KR_RESULTS_DIR = PACKAGE_ROOT / "results" / "kr"
KR_RAW_DIR = KR_RESULTS_DIR / "raw"
KR_AGGREGATE_DIR = KR_RESULTS_DIR / "aggregate"
KR_TABLES_DIR = KR_RESULTS_DIR / "tables"


class Validator:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def check(self, condition: bool, name: str, detail: Any) -> None:
        self.checks.append({"name": name, "status": "PASS" if condition else "FAIL", "detail": detail})

    @property
    def blockers(self) -> list[dict[str, Any]]:
        return [item for item in self.checks if item["status"] == "FAIL"]


def snapshot_rows(raw_path: Path) -> list[dict[str, Any]]:
    body = json.loads(raw_path.read_text(encoding="utf-8"))
    snapshot = SearchSnapshot(body, raw_path, sha256_file(raw_path), "", {})
    return result_rows(snapshot)


def source_integrity() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    registry_path = KR_DATA_DIR / "source_registry.jsonl"
    records = read_jsonl(registry_path) if registry_path.exists() else []
    raw_cache: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        relative = str(record.get("raw_response_file") or "")
        raw_path = PACKAGE_ROOT / relative
        if not raw_path.exists():
            findings.append({"type": "raw_response_missing", "citation": record.get("citation_canonical")})
            continue
        if sha256_file(raw_path) != record.get("raw_batch_sha256"):
            findings.append({"type": "raw_batch_hash_mismatch", "citation": record.get("citation_canonical")})
            continue
        rows = raw_cache.setdefault(relative, snapshot_rows(raw_path))
        status = int(record.get("lookup_status", 0))
        citation = str(record.get("citation_canonical") or "")
        if status == 200:
            matching = [row for row in rows if exact_case_number(row) == citation]
            entry_hashes = {sha256_text(canonical_json(row)) for row in matching}
            if record.get("response_sha256") not in entry_hashes:
                findings.append({"type": "valid_entry_hash_or_binding_mismatch", "citation": citation})
            if not record.get("case_name") or not record.get("law_go_kr_prec_id") or record.get("court") != "대법원":
                findings.append({"type": "incomplete_supreme_court_entity", "citation": citation})
        elif status == 404:
            observed = sorted(exact_case_number(row) for row in rows)
            evidence = {
                "candidate_case_number": citation,
                "observed_exact_case_numbers": observed,
                "raw_batch_sha256": record.get("raw_batch_sha256"),
            }
            if citation in observed or record.get("response_sha256") != sha256_text(canonical_json(evidence)):
                findings.append({"type": "not_found_exact_case_number_evidence_mismatch", "citation": citation})
            if record.get("http_status") != 200 or record.get("verification_outcome") != "NOT_FOUND_EXACT_CASE_NUMBER":
                findings.append({"type": "incorrect_not_found_semantics", "citation": citation})
            if not record.get("mutation"):
                findings.append({"type": "not_found_not_mutation_derived", "citation": citation})
        else:
            findings.append({"type": "disallowed_normalized_lookup_status", "citation": citation, "status": status})
    valid = sum(int(row.get("lookup_status", 0)) == 200 for row in records)
    not_found = sum(int(row.get("lookup_status", 0)) == 404 for row in records)
    if (valid, not_found) != (60, 30):
        findings.append({"type": "registry_balance", "valid": valid, "not_found_exact": not_found})
    return {
        "status": "PASS" if not findings else "FAIL",
        "registry_records": len(records),
        "valid_200_records": valid,
        "normalized_not_found_records": not_found,
        "not_found_http_semantics": "HTTP 200 with no exact 사건번호 match; registry lookup_status normalized to 404",
        "findings": findings,
    }


def secret_leak_paths() -> list[str]:
    key_path = REPO_ROOT / "local_security" / "open.law.go.kr.txt"
    if not key_path.exists():
        return []
    secret = key_path.read_text(encoding="utf-8-sig").strip().encode()
    if not secret:
        return []
    return [str(path.relative_to(PACKAGE_ROOT)) for path in PACKAGE_ROOT.rglob("*") if path.is_file() and secret in path.read_bytes()]


def nested_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(nested_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(nested_keys(item) for item in value), set())
    return set()


def validate() -> dict[str, Any]:
    validator = Validator()
    runtime_path = KR_DATA_DIR / "law200_test_runtime.jsonl"
    gold_path = KR_DATA_DIR / "law200_test_gold.jsonl"
    registry_path = KR_DATA_DIR / "source_registry.jsonl"
    corpus_path = KR_DATA_DIR / "corpus" / "legal_cases.jsonl"
    manifest_path = KR_DATA_DIR / "benchmark_manifest.json"
    hardware_path = KR_AGGREGATE_DIR / "hardware_environment.json"
    inputs = (runtime_path, gold_path, registry_path, corpus_path, manifest_path, hardware_path)
    validator.check(all(path.exists() for path in inputs), "required_frozen_inputs", [str(path) for path in inputs if not path.exists()])
    if not all(path.exists() for path in inputs):
        return finish(validator)

    runtime, gold, manifest = read_jsonl(runtime_path), read_jsonl(gold_path), read_json(manifest_path)
    runtime_ids = [str(row.get("case_id")) for row in runtime]
    gold_ids = [str(row.get("case_id")) for row in gold]
    validator.check(len(runtime) == len(gold) == 200, "exactly_200_test_cases", {"runtime": len(runtime), "gold": len(gold)})
    validator.check(set(runtime_ids) == set(gold_ids) and len(set(runtime_ids)) == 200, "runtime_gold_case_alignment", "one-to-one opaque IDs")
    leaked = sum(bool(nested_keys(row) & FORBIDDEN_RUNTIME_KEYS) for row in runtime)
    validator.check(leaked == 0, "gold_labels_absent_from_runtime", {"leaking_rows": leaked})
    category_counts = Counter(row.get("category") for row in gold)
    language_counts = Counter(row.get("language") for row in gold)
    validator.check(category_counts == {"A_VALID": 50, "B_SURFACE_VARIATION": 50, "C_NONEXISTENT": 50, "D_ENTITY_MISMATCH": 50}, "category_balance", dict(category_counts))
    validator.check(language_counts == {"en": 100, "ko": 100}, "language_balance", dict(language_counts))
    validator.check(len({row["query"] for row in runtime}) == 200, "unique_runtime_queries", "200 required")
    validator.check(manifest.get("hashes", {}).get(runtime_path.name) == sha256_file(runtime_path), "frozen_test_hash", sha256_file(runtime_path))
    validator.check(manifest.get("source_registry_sha256") == sha256_file(registry_path), "frozen_registry_hash", sha256_file(registry_path))
    validator.check(manifest.get("corpus_sha256") == sha256_file(corpus_path), "frozen_corpus_hash", sha256_file(corpus_path))
    hardware = read_json(hardware_path)
    validator.check(
        hardware.get("runtime_sha256") == sha256_file(runtime_path)
        and bool(hardware.get("hardware", {}).get("cpu_model"))
        and hardware.get("hardware", {}).get("logical_cpu_count") is not None
        and "gpu_probe" in hardware.get("hardware", {}),
        "hardware_observation_bound_to_test",
        {"capture_timing": hardware.get("capture_timing"), "gpu_probe": hardware.get("hardware", {}).get("gpu_probe")},
    )

    runtime_by_id = {row["case_id"]: row for row in runtime}
    pairs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in gold:
        pairs[str(row["pair_id"])].append(row)
    equivalent = 0
    for pair in pairs.values():
        if len(pair) != 2:
            continue
        uirs = [compile_legal_uir(runtime_by_id[row["case_id"]]["query"]) for row in pair]
        signatures = [(u.domain, u.intent, u.entity_type, u.citation, u.claimed_case_name) for u in uirs]
        equivalent += signatures[0] == signatures[1]
    validator.check(equivalent == 100, "cross_lingual_uir_equivalence", {"equivalent_pairs": equivalent, "pairs": len(pairs)})

    source = source_integrity()
    validator.check(source["status"] == "PASS", "source_integrity_audit", source)
    leaks = secret_leak_paths()
    validator.check(not leaks, "credential_absent_from_artifacts", {"leak_file_count": len(leaks)})
    dev_runtime = read_jsonl(KR_DATA_DIR / "law200_dev_runtime.jsonl")
    validator.check(not ({row["case_id"] for row in runtime} & {row["case_id"] for row in dev_runtime}), "dev_test_id_separation", "no overlap")
    validator.check(not ({row["query"] for row in runtime} & {row["query"] for row in dev_runtime}), "dev_test_query_separation", "no overlap")

    access_path = KR_RAW_DIR / "test_pre_generation_access_log.json"
    access_ok = False
    if access_path.exists():
        access = read_json(access_path)
        accessed = [str(row.get("path", "")).lower() for row in access.get("pre_generation_files_read", [])]
        access_ok = bool(accessed) and not any("gold" in path or "oracle" in path or "scoring" in path for path in accessed)
    validator.check(access_ok, "forbidden_pre_generation_gold_access_zero", str(access_path))

    raw_by_pipeline: dict[str, list[dict[str, Any]]] = {}
    for pipeline in PIPELINES:
        paths = sorted(KR_RAW_DIR.glob(f"test_{pipeline}_*.jsonl"))
        validator.check(len(paths) == 1, f"raw_file_{pipeline}", [str(path) for path in paths])
        if len(paths) != 1:
            continue
        rows = read_jsonl(paths[0])
        raw_by_pipeline[pipeline] = rows
        validator.check(len(rows) == 200, f"raw_rows_{pipeline}", len(rows))
        validator.check({row.get("case_id") for row in rows} == set(runtime_ids), f"same_cases_{pipeline}", "must equal frozen runtime")
        complete = all(
            "final_output" in row and isinstance(row.get("model_calls"), list)
            and (not row.get("model_invoked") or all("raw_response" in call for call in row["model_calls"]))
            for row in rows
        )
        validator.check(complete, f"raw_output_complete_{pipeline}", "model raw response or explicit pre-model output required")
    configs = {canonical_json(row.get("model_config")) for rows in raw_by_pipeline.values() for row in rows}
    validator.check(len(configs) == 1 and bool(configs), "same_backbone_and_configuration", {"distinct_configs": len(configs)})

    metrics_path = KR_AGGREGATE_DIR / "test_metrics.json"
    stats_path = KR_AGGREGATE_DIR / "test_statistics.json"
    validator.check(metrics_path.exists() and stats_path.exists(), "aggregate_and_statistics_present", {"metrics": metrics_path.exists(), "statistics": stats_path.exists()})
    gold_by_id = {row["case_id"]: row for row in gold}
    recomputed_rows: list[dict[str, Any]] = []
    recomputed_aggregates: list[dict[str, Any]] = []
    for pipeline, rows in sorted(raw_by_pipeline.items()):
        scored = [score_record(row, gold_by_id[row["case_id"]]) for row in rows]
        recomputed_rows.extend(scored)
        recomputed_aggregates.append(aggregate(scored))
    if metrics_path.exists():
        validator.check(
            canonical_json({"pipelines": recomputed_aggregates}) == canonical_json(read_json(metrics_path)),
            "aggregates_and_confidence_intervals_recomputed",
            "full metric objects must reproduce exactly",
        )
    if stats_path.exists():
        validator.check(canonical_json(statistics(recomputed_rows)) == canonical_json(read_json(stats_path)), "statistics_recomputed_from_raw", "McNemar, Holm, and risk differences must reproduce")

    csv_path, md_path = KR_TABLES_DIR / "law200_main_table.csv", KR_TABLES_DIR / "law200_main_table.md"
    validator.check(csv_path.exists() and md_path.exists(), "paper_facing_tables_present", {"csv": csv_path.exists(), "md": md_path.exists()})
    if csv_path.exists():
        with csv_path.open(encoding="utf-8", newline="") as handle:
            table = {row["pipeline"]: row for row in csv.DictReader(handle)}
        keys = ("accepted_unsupported_legal_claim_rate", "invalid_citation_far", "verified_answer_coverage", "false_rejection_rate")
        table_ok = len(table) == len(recomputed_aggregates)
        for row in recomputed_aggregates:
            for key in keys:
                expected, observed = row.get(key), table.get(row["pipeline"], {}).get(key)
                table_ok = table_ok and ((expected is None and observed == "") or (expected is not None and abs(float(observed) - float(expected)) <= 1e-12))
        validator.check(table_ok, "paper_table_recomputed_not_manual", "CSV must equal raw recomputation")
    if md_path.exists():
        validator.check("AUTO-GENERATED" in md_path.read_text(encoding="utf-8"), "markdown_table_generation_marker", "required")
    return finish(validator)


def finish(validator: Validator) -> dict[str, Any]:
    status = "READY_FOR_KAIC_MANUSCRIPT_KR" if not validator.blockers else "NOT_READY"
    report = {
        "validator": "LAW-KR-200 publication gate 1.0",
        "validated_at": utc_now(),
        "status": status,
        "blocker_count": len(validator.blockers),
        "checks": validator.checks,
    }
    write_json(KR_AGGREGATE_DIR / "publication_validation.json", report)
    lines = ["# LAW-KR-200 Audit Report", "", f"Status: **{status}**", "", "## Checks", ""]
    for item in validator.checks:
        mark = "x" if item["status"] == "PASS" else " "
        lines.append(f"- [{mark}] {item['name']}: `{item['status']}` — {item['detail']}")
    (PACKAGE_ROOT / "LAW200_KR_AUDIT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> None:
    result = validate()
    print(json.dumps({"status": result["status"], "blocker_count": result["blocker_count"]}, indent=2, ensure_ascii=False))
    if result["status"] != "READY_FOR_KAIC_MANUSCRIPT_KR":
        raise SystemExit(1)
    print("READY_FOR_KAIC_MANUSCRIPT_KR")


if __name__ == "__main__":
    main()
