#!/usr/bin/env python3
"""Final Phase-4C publication-consistency gate."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.uir_phase4c.common import PIPELINES, RESULTS_DIR, ROOT, read_jsonl, sha256_text, write_json
from evaluation.uir_phase4c.detect_placeholder_evidence import audit


def _csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


def evaluate_gate() -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    evidence_path = RESULTS_DIR / "per_case_evidence_actual.jsonl"
    records = read_jsonl(evidence_path) if evidence_path.exists() else []
    by_pipeline = {pipeline: [row for row in records if row.get("pipeline") == pipeline] for pipeline in PIPELINES}
    actual_complete = len(records) == 5400 and all(len(rows) == 600 for rows in by_pipeline.values())
    if not actual_complete: blockers.append(f"actual matched evidence incomplete: {len(records)}/5400")
    placeholder = audit("full", include_external=True)
    if placeholder["placeholder_evidence_count"]: blockers.append(f"placeholder/authenticity findings: {placeholder['placeholder_evidence_count']}")
    provenance_path = RESULTS_DIR / "OFFICIAL_BENCHMARK_PROVENANCE.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else {}
    finqa_mapping_complete = len(provenance.get("mappings", {}).get("FinQA", [])) == 200
    halu_mapping_complete = len(provenance.get("mappings", {}).get("HaluEval-QA", [])) == 200
    for dataset, expected in (("finqa", 200), ("halueval", 200)):
        for short in ("C1", "C2", "C4", "C8"):
            path = RESULTS_DIR / f"{dataset}_predictions_actual_{short}.jsonl"
            rows = read_jsonl(path) if path.exists() else []
            if len(rows) != expected or not all(row.get("score", {}).get("source_mapping_match") for row in rows):
                blockers.append(f"official mapping/score incomplete: {dataset} {short}")
    gold_audit_path = RESULTS_DIR / "GOLD_ACCESS_AUDIT.md"
    forbidden_gold = 0 if gold_audit_path.exists() and "forbidden_pre_generation_gold_access = 0" in gold_audit_path.read_text(encoding="utf-8") else 1
    if forbidden_gold: blockers.append("gold-access audit missing or non-zero")
    c4_rows = by_pipeline.get("C4_TOOL_CALLING_AGENT", [])
    tool_model_driven = len(c4_rows) == 600 and all(row.get("model_tool_request", {}).get("model_produced") is True for row in c4_rows)
    if not tool_model_driven: blockers.append("C4 tool request is not model-driven for every shared case")
    coupled = bool(records) and all(row.get("timing", {}).get("start_ns", 0) > 0 and row.get("timing", {}).get("end_ns", 0) > row.get("timing", {}).get("start_ns", 0) and (not row.get("model_invoked") or row.get("timing", {}).get("model_ms", 0) > 0) for row in records)
    if not coupled: blockers.append("per-case outcome/latency coupling incomplete")
    summary_path = RESULTS_DIR / "strong_baseline_summary_actual.csv"
    aggregate_ok = summary_path.exists()
    if aggregate_ok:
        summary = {row["pipeline"]: row for row in _csv(summary_path)}
        for pipeline, rows in by_pipeline.items():
            if pipeline not in summary or int(summary[pipeline]["total_cases"]) != len(rows) or int(summary[pipeline]["unsupported_claim_count"]) != sum(row["metrics"]["unsupported_claim"] for row in rows): aggregate_ok = False
    if not aggregate_ok: blockers.append("aggregate metrics do not derive from actual raw evidence")
    statistics_ok = all((RESULTS_DIR / name).exists() and len(_csv(RESULTS_DIR / name)) == 8 for name in ("stat_safety_actual.csv", "stat_utility_actual.csv", "stat_latency_actual.csv"))
    if not statistics_ok: blockers.append("matched actual statistics incomplete")
    mutation_path = ROOT / "results/uir_phase4b/mutation_test_report_phase4b.csv"
    mutation_unsafe = sum(int(row.get("unsafe_accept", "0")) for row in _csv(mutation_path)) if mutation_path.exists() else 1
    if mutation_unsafe: blockers.append(f"mutation unsafe accepts: {mutation_unsafe}")
    flags = {
        "phase4c_actual_model_generation_complete": actual_complete,
        "placeholder_evidence_count": placeholder["placeholder_evidence_count"],
        "official_finqa_source_mapping_complete": finqa_mapping_complete,
        "official_halueval_source_mapping_complete": halu_mapping_complete,
        "forbidden_gold_access_count": forbidden_gold,
        "tool_calling_baseline_is_model_driven": tool_model_driven,
        "per_case_outcome_latency_coupled": coupled,
        "aggregate_metrics_from_actual_raw": aggregate_ok,
        "statistics_from_actual_pairs": statistics_ok,
        "mutation_unsafe_accept_count": mutation_unsafe,
        "publication_consistency_blockers": len(blockers),
    }
    return flags, blockers


def main() -> None:
    flags, blockers = evaluate_gate(); status = "READY_FOR_FINAL_MANUSCRIPT_AUTHENTIC" if not blockers else "BLOCKED_PUBLICATION_EVIDENCE_INCOMPLETE"
    lines = ["# Phase UIR-4C Publication Consistency", "", f"Generated: {datetime.now(timezone.utc).isoformat()}", "", "## Gate", "", f"`{status}`", "", "## Machine-checkable conditions", ""]
    lines.extend(f"- `{key} = {str(value).lower() if isinstance(value, bool) else value}`" for key, value in flags.items())
    lines += ["", "## Blockers", ""] + ([f"- {item}" for item in blockers] if blockers else ["- None."])
    (RESULTS_DIR / "PUBLICATION_CONSISTENCY_PHASE4C.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    run_manifest = {"phase": "UIR-4C", "generated_at_utc": datetime.now(timezone.utc).isoformat(), "status": status, "gate": flags, "blockers": blockers}
    write_json(RESULTS_DIR / "run_manifest_phase4c.json", run_manifest)
    print(json.dumps(run_manifest, sort_keys=True)); raise SystemExit(0 if not blockers else 1)


if __name__ == "__main__": main()

