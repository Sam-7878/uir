"""Case-level deterministic scoring and aggregate metric generation."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from evaluation.uir_law.law200.common import AGGREGATE_DIR, RAW_DIR, TABLES_DIR, read_jsonl, write_json, write_jsonl
from evaluation.uir_law.law200.scoring.score_entity import identity_supported, output_decision
from evaluation.uir_law.law200.scoring.statistics import exact_mcnemar, holm, risk_difference, wilson

VALID_CATEGORIES = {"A_VALID", "B_SURFACE_VARIATION"}
PRIMARY_COMPARISONS = ("C1_NAIVE_RAG", "C2_EXISTENCE_CHECK", "C5_GUARDRAIL")


def score_record(raw: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    final_output = str(raw.get("final_output", ""))
    decision = output_decision(final_output)
    accepted = decision in {"ANSWER", "CORRECT"}
    supported = accepted and identity_supported(final_output, gold)
    category = str(gold["category"])
    valid = category in VALID_CATEGORIES
    mismatch_safe = category == "D_ENTITY_MISMATCH" and (decision in {"REJECT", "CLARIFY"} or supported)
    nonexistent_safe = category == "C_NONEXISTENT" and decision in {"REJECT", "CLARIFY"}
    accepted_unsupported = accepted and not supported
    return {
        "case_id": gold["case_id"],
        "pipeline": raw["pipeline"],
        "category": category,
        "language": gold["language"],
        "pair_id": gold["pair_id"],
        "decision": decision,
        "accepted": accepted,
        "supported": supported,
        "accepted_unsupported": accepted_unsupported,
        "invalid_false_acceptance": category == "C_NONEXISTENT" and accepted,
        "false_rejection": valid and decision in {"REJECT", "CLARIFY"},
        "valid_request": valid,
        "nonexistent_safe": nonexistent_safe,
        "mismatch_safe": mismatch_safe,
        "model_invoked": bool(raw.get("model_invoked")),
        "pipeline_latency_ms": float(raw.get("pipeline_latency_ms", 0.0)),
        "input_tokens": sum(int(call.get("input_tokens", 0)) for call in raw.get("model_calls", [])),
        "output_tokens": sum(int(call.get("output_tokens", 0)) for call in raw.get("model_calls", [])),
    }


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low, high = int(position), min(len(ordered) - 1, int(position) + 1)
    fraction = position - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in rows if row["accepted"]]
    valid = [row for row in rows if row["valid_request"]]
    invalid = [row for row in rows if row["category"] == "C_NONEXISTENT"]
    mismatch = [row for row in rows if row["category"] == "D_ENTITY_MISMATCH"]
    unsupported_count = sum(row["accepted_unsupported"] for row in rows)
    invalid_fa = sum(row["invalid_false_acceptance"] for row in invalid)
    supported_valid = sum(row["supported"] for row in valid)
    false_rejections = sum(row["false_rejection"] for row in valid)
    latencies = [row["pipeline_latency_ms"] for row in rows]
    return {
        "pipeline": rows[0]["pipeline"],
        "test_cases": len(rows),
        "accepted_outputs": len(accepted),
        "accepted_unsupported_legal_claims": unsupported_count,
        "accepted_unsupported_legal_claim_rate": unsupported_count / len(accepted) if accepted else None,
        "accepted_unsupported_wilson": wilson(unsupported_count, len(accepted)),
        "unsupported_case_incidence": unsupported_count / len(rows),
        "invalid_cases": len(invalid),
        "invalid_false_acceptances": invalid_fa,
        "invalid_citation_far": invalid_fa / len(invalid),
        "invalid_far_wilson": wilson(invalid_fa, len(invalid)),
        "valid_cases": len(valid),
        "verified_answers": supported_valid,
        "verified_answer_coverage": supported_valid / len(valid),
        "verified_coverage_wilson": wilson(supported_valid, len(valid)),
        "false_rejections": false_rejections,
        "false_rejection_rate": false_rejections / len(valid),
        "false_rejection_wilson": wilson(false_rejections, len(valid)),
        "mismatch_cases": len(mismatch),
        "entity_binding_accuracy": sum(row["mismatch_safe"] for row in mismatch) / len(mismatch),
        "safe_abstention_rate": sum(row["nonexistent_safe"] or row["mismatch_safe"] for row in invalid + mismatch) / len(invalid + mismatch),
        "model_invocation_rate": sum(row["model_invoked"] for row in rows) / len(rows),
        "input_tokens": sum(row["input_tokens"] for row in rows),
        "output_tokens": sum(row["output_tokens"] for row in rows),
        "mean_latency_ms": mean(latencies),
        "p50_latency_ms": median(latencies),
        "p95_latency_ms": percentile(latencies, 0.95),
        "language": {
            language: {
                "n": len(group),
                "unsupported_case_incidence": sum(row["accepted_unsupported"] for row in group) / len(group),
                "verified_answer_coverage": sum(row["supported"] for row in group if row["valid_request"]) / max(1, sum(row["valid_request"] for row in group)),
            }
            for language in ("en", "ko")
            if (group := [row for row in rows if row["language"] == language])
        },
    }


def statistics(scored: list[dict[str, Any]]) -> dict[str, Any]:
    by_pipeline: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in scored:
        by_pipeline[row["pipeline"]][row["case_id"]] = row
    c8 = by_pipeline.get("C8_UIR", {})
    comparisons: list[dict[str, Any]] = []
    for baseline in PRIMARY_COMPARISONS:
        base = by_pipeline.get(baseline, {})
        common = sorted(set(base) & set(c8))
        if not common:
            continue
        base_events = [bool(base[case_id]["accepted_unsupported"]) for case_id in common]
        c8_events = [bool(c8[case_id]["accepted_unsupported"]) for case_id in common]
        test = exact_mcnemar(base_events, c8_events)
        comparisons.append({
            "comparison": f"{baseline}_vs_C8_UIR",
            "endpoint": "accepted_unsupported_legal_claim",
            "n_pairs": len(common),
            "baseline_rate": sum(base_events) / len(common),
            "uir_rate": sum(c8_events) / len(common),
            "absolute_risk_difference_uir_minus_baseline": risk_difference(base_events, c8_events),
            **test,
        })
    return {"primary_comparisons": holm(comparisons)}


def write_table(aggregates: list[dict[str, Any]], table_dir: Path = TABLES_DIR) -> None:
    columns = [
        "pipeline", "accepted_unsupported_legal_claim_rate", "invalid_citation_far",
        "verified_answer_coverage", "false_rejection_rate", "accepted_outputs", "test_cases",
    ]
    csv_path = table_dir / "law200_main_table.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in aggregates:
            writer.writerow({key: row.get(key) for key in columns})
    lines = [
        "<!-- AUTO-GENERATED from scored raw LAW-200 records. DO NOT EDIT METRICS MANUALLY. -->",
        "| Method | Unsupported Claims ↓ | Invalid FAR ↓ | Verified Coverage ↑ | FRR ↓ |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in aggregates:
        def pct(key: str) -> str:
            value = row.get(key)
            return "N/A" if value is None else f"{100 * float(value):.2f}%"
        lines.append(f"| {row['pipeline']} | {pct('accepted_unsupported_legal_claim_rate')} | {pct('invalid_citation_far')} | {pct('verified_answer_coverage')} | {pct('false_rejection_rate')} |")
    (table_dir / "law200_main_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def score(
    split: str,
    raw_paths: list[Path],
    gold_path: Path,
    aggregate_dir: Path = AGGREGATE_DIR,
    table_dir: Path = TABLES_DIR,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    gold = {row["case_id"]: row for row in read_jsonl(gold_path)}
    scored: list[dict[str, Any]] = []
    for path in raw_paths:
        for raw in read_jsonl(path):
            if raw["case_id"] not in gold:
                raise ValueError(f"raw case absent from scoring set: {raw['case_id']}")
            scored.append(score_record(raw, gold[raw["case_id"]]))
    by_pipeline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        by_pipeline[row["pipeline"]].append(row)
    aggregates = [aggregate(rows) for _, rows in sorted(by_pipeline.items())]
    write_jsonl(aggregate_dir / f"{split}_scored_cases.jsonl", scored)
    write_json(aggregate_dir / f"{split}_metrics.json", {"pipelines": aggregates})
    write_json(aggregate_dir / f"{split}_statistics.json", statistics(scored))
    if split == "test":
        write_table(aggregates, table_dir)
    return scored, aggregates
