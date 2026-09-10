#!/usr/bin/env python3
"""Fail closed on template, hash, timing, token, tool, and source-mapping evidence."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from evaluation.uir_phase4c.common import PIPELINES, RAW_DIR, RESULTS_DIR, read_jsonl, sha256_text, write_json

PLACEHOLDERS = (
    "Direct SLM generated assertion without factual retrieval.",
    "RAG context prepended: generated answer based on retrieved documents.",
    "Syntactically valid JSON output",
    "Graph-retrieval answer emitted.",
    "UIR draft: verified claims",
)


def inspect_records(records: list[dict[str, Any]], require_metrics: bool = False, check_diversity: bool = True) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for record in records:
        cid, pipeline = record.get("case_id"), record.get("pipeline")
        generation = record.get("generation", {})
        raw = generation.get("raw_response")
        digest = generation.get("raw_response_sha256")
        if raw is None or not digest or digest != sha256_text(raw): findings.append({"case_id": cid, "pipeline": pipeline, "type": "raw_hash_missing_or_mismatch"})
        if any(phrase in (raw or "") for phrase in PLACEHOLDERS): findings.append({"case_id": cid, "pipeline": pipeline, "type": "placeholder_phrase"})
        if record.get("model_invoked") and (generation.get("input_tokens", 0) <= 0 or generation.get("output_tokens", 0) <= 0): findings.append({"case_id": cid, "pipeline": pipeline, "type": "invoked_token_count_missing"})
        timing = record.get("timing", {})
        if not timing.get("start_ns") or not timing.get("end_ns") or timing.get("end_ns") <= timing.get("start_ns"): findings.append({"case_id": cid, "pipeline": pipeline, "type": "measured_timestamp_missing"})
        if pipeline == "C4_TOOL_CALLING_AGENT" and record.get("model_invoked"):
            request = record.get("model_tool_request", {})
            if not request or request.get("model_produced") is not True: findings.append({"case_id": cid, "pipeline": pipeline, "type": "model_tool_request_missing"})
        if require_metrics and "metrics" not in record: findings.append({"case_id": cid, "pipeline": pipeline, "type": "score_missing"})
    invoked = [record for record in records if record.get("model_invoked")]
    if check_diversity:
        for pipeline in ("C0_DIRECT_SLM", "C1_NAIVE_RAG", "C3_JSON_SCHEMA_STRUCTURED"):
            relevant = [record for record in invoked if record["pipeline"] == pipeline]
            hashes = {record["generation"]["raw_response_sha256"] for record in relevant}
            if relevant and len(hashes) <= 1: findings.append({"pipeline": pipeline, "type": "implausibly_identical_responses", "unique": len(hashes)})
    for pipeline in PIPELINES:
        latencies = [round(record["timing"]["end_to_end_ms"], 6) for record in records if record["pipeline"] == pipeline]
        if len(latencies) >= 100 and len(set(latencies)) <= 5: findings.append({"pipeline": pipeline, "type": "deterministic_latency_grid", "unique": len(set(latencies))})
    return findings


def inspect_external() -> list[dict[str, Any]]:
    findings = []
    for dataset in ("finqa", "halueval"):
        for short in ("C1", "C2", "C4", "C8"):
            path = RESULTS_DIR / f"{dataset}_predictions_actual_{short}.jsonl"
            if not path.exists(): findings.append({"type": "external_prediction_missing", "file": str(path)}); continue
            for record in read_jsonl(path):
                if not record.get("source_original_id") or not record.get("source_row_hash") or not record.get("source_file_sha256"): findings.append({"case_id": record.get("case_id"), "pipeline": short, "type": "official_source_mapping_missing"})
                findings.extend(inspect_records([record], check_diversity=False))
                if "score" not in record: findings.append({"case_id": record.get("case_id"), "pipeline": short, "type": "external_score_missing"})
            records = read_jsonl(path)
            if short == "C1" and len({row["generation"]["raw_response_sha256"] for row in records}) <= 1:
                findings.append({"pipeline": short, "file": str(path), "type": "implausibly_identical_responses"})
    return findings


def audit(stage: str, include_external: bool) -> dict[str, Any]:
    records = []
    for pipeline in PIPELINES:
        path = RAW_DIR / f"{stage}_{pipeline}.jsonl"
        if path.exists(): records.extend(read_jsonl(path))
        else: records.append({"case_id": "", "pipeline": pipeline, "generation": {}, "timing": {}})
    findings = inspect_records(records)
    if include_external: findings.extend(inspect_external())
    report = {"stage": stage, "records_checked": len(records), "include_external": include_external, "placeholder_evidence_count": len(findings), "findings_by_type": dict(Counter(item["type"] for item in findings)), "findings": findings, "status": "PASS" if not findings else "FAIL"}
    write_json(RESULTS_DIR / f"placeholder_audit_{stage}.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--stage", choices=("smoke", "full"), default="smoke"); parser.add_argument("--include-external", action="store_true"); args = parser.parse_args()
    report = audit(args.stage, args.include_external); print(json.dumps(report, sort_keys=True)); raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__": main()
