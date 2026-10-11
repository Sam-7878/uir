#!/usr/bin/env python3
"""Run the Rust UIR pipeline and derive machine-readable evaluation summaries."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from metrics import describe, prf, rate, wilson

STAGES = ["dsl_compile_us", "uir_validate_us", "policy_eval_us", "aaco_us", "executor_us", "slm_us", "output_validate_us", "canonicalization_us", "digest_us", "total_us"]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if not rows and not fields: return
    fields = fields or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore"); writer.writeheader(); writer.writerows(rows)


def flatten(record: dict) -> dict:
    row = {key: value for key, value in record.items() if key not in {"stage_latencies_us", "actual_semantics"}}
    row.update(record["stage_latencies_us"]); row["actual_semantics"] = json.dumps(record["actual_semantics"], sort_keys=True, separators=(",", ":"))
    return row


def ratio_row(metric: str, success: int, total: int, group: str = "overall") -> dict:
    low, high = wilson(success, total)
    return {"group": group, "metric": metric, "successes": success, "total": total, "value": rate(success, total), "ci95_low": low, "ci95_high": high}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", type=Path, default=Path("evaluation/uir/fixtures/generated")); parser.add_argument("--out", type=Path, default=Path("results/uir")); args = parser.parse_args()
    dataset = args.dataset / "dataset.jsonl" if args.dataset.is_dir() else args.dataset
    args.out.mkdir(parents=True, exist_ok=True); raw_jsonl = args.out / "cases_raw.jsonl"
    subprocess.run(["cargo", "run", "--quiet", "-p", "poa-uir", "--bin", "uir-eval", "--", str(dataset), str(raw_jsonl)], check=True)
    records = read_jsonl(raw_jsonl); source = {item["case_id"]: item for item in read_jsonl(dataset)}
    rows = [flatten(item) for item in records]; write_csv(args.out / "cases_raw.csv", rows)
    failures = [item for item in records if not item["correct"] or not item["semantic_match"]]
    (args.out / "failures.jsonl").write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in failures), encoding="utf-8")

    valid = [item for item in records if source[item["case_id"]]["expected_outcome"] == "COMMIT"]
    invalid = [item for item in records if source[item["case_id"]]["expected_outcome"] == "REJECT"]
    factual_claims = sum(item["generated_claim_count"] for item in records)
    unsupported = sum(item["unsupported_claim_count"] for item in records)
    compilable = [item for item in records if source[item["case_id"]].get("expected_semantics")]
    metric_rows = [
        ratio_row("uir_exact_structural_match", sum(item["exact_structural_match"] for item in compilable), len(compilable)),
        ratio_row("semantic_uir_match", sum(item["semantic_match"] for item in compilable), len(compilable)),
        ratio_row("policy_decision_accuracy", sum(item["expected_policy_decision"] == item["actual_policy_decision"] for item in records), len(records)),
        ratio_row("outcome_accuracy", sum(item["correct"] for item in records), len(records)),
        ratio_row("false_accept_rate", sum(item["actual_outcome"] == "COMMIT" for item in invalid), len(invalid)),
        ratio_row("false_reject_rate", sum(item["actual_outcome"] == "REJECT" for item in valid), len(valid)),
        ratio_row("invalid_entity_fabrication_prevention_rate", sum(item["actual_outcome"] == "REJECT" for item in records if item["category"] == "invalid_entity"), sum(item["category"] == "invalid_entity" for item in records)),
        ratio_row("unsupported_claim_rate", unsupported, factual_claims),
        ratio_row("unsupported_claim_acceptance_rate", sum(item["actual_outcome"] == "COMMIT" for item in records if item["category"] == "output_contract"), sum(item["category"] == "output_contract" for item in records)),
        ratio_row("provenance_accuracy", sum(item["supported_claim_count"] for item in records), factual_claims),
    ]
    # Pair-level cross-lingual evidence.
    pairs: dict[str, list[dict]] = defaultdict(list)
    for item in records:
        pair_id = source[item["case_id"]].get("pair_id")
        if pair_id: pairs[pair_id].append(item)
    equivalent = sum(len(items) == 2 and len({item["semantic_digest"] for item in items}) == 1 for items in pairs.values())
    metric_rows.append(ratio_row("cross_lingual_equivalence_rate", equivalent, len(pairs)))
    expected_slots: set[tuple[str, str]] = set(); actual_slots: set[tuple[str, str]] = set()
    for item in records:
        expected = source[item["case_id"]].get("expected_semantics") or {}
        actual = item.get("actual_semantics") or {}
        expected_slots |= {(f"{item['case_id']}:{key}", str(value)) for key, value in expected.items()}
        actual_slots |= {(f"{item['case_id']}:{key}", str(value)) for key, value in actual.items()}
    precision, recall, f1 = prf(expected_slots, actual_slots)
    for name, value in (("slot_precision", precision), ("slot_recall", recall), ("slot_f1", f1)):
        metric_rows.append({"group": "overall", "metric": name, "successes": "", "total": "", "value": value, "ci95_low": "", "ci95_high": ""})
    write_csv(args.out / "metric_summary.csv", metric_rows)
    write_csv(args.out / "confidence_intervals.csv", [row for row in metric_rows if row["ci95_low"] != ""])

    def grouped(field: str) -> list[dict]:
        result = []
        for key in sorted({item[field] for item in records}):
            group = [item for item in records if item[field] == key]
            result.append({field: key, "cases": len(group), "outcome_accuracy": rate(sum(item["correct"] for item in group), len(group)), "semantic_match": rate(sum(item["semantic_match"] for item in group), len(group)), "policy_accuracy": rate(sum(item["expected_policy_decision"] == item["actual_policy_decision"] for item in group), len(group)), "false_accept_rate": rate(sum(item["expected_outcome"] == "REJECT" and item["actual_outcome"] == "COMMIT" for item in group), sum(item["expected_outcome"] == "REJECT" for item in group)), "false_reject_rate": rate(sum(item["expected_outcome"] == "COMMIT" and item["actual_outcome"] == "REJECT" for item in group), sum(item["expected_outcome"] == "COMMIT" for item in group))})
        return result
    write_csv(args.out / "language_summary.csv", grouped("language")); write_csv(args.out / "category_summary.csv", grouped("category"))
    policy_rows = []
    for level in ["L0_SYSTEM", "L1_DOMAIN", "L2_ENTERPRISE", "L3_PREFERENCE"]:
        group = [item for item in records if source[item["case_id"]].get("policy_level") == level]
        policy_rows.append({"policy_level": level, "cases": len(group), "accuracy": rate(sum(item["expected_policy_decision"] == item["actual_policy_decision"] for item in group), len(group)), "far": rate(sum(item["actual_policy_decision"] == "PERMIT" for item in group), len(group)), "frr": 0.0})
    write_csv(args.out / "policy_summary.csv", policy_rows)
    latency_rows = []
    for stage in STAGES:
        values = [item["stage_latencies_us"][stage] for item in records]; latency_rows.append({"stage": stage, **describe(values)})
    write_csv(args.out / "latency_summary.csv", latency_rows)

    dataset_bytes = dataset.read_bytes()
    timestamp = os.environ.get("SOURCE_DATE_EPOCH") or datetime.now(timezone.utc).isoformat()
    git_prefix = ["git", "-c", f"safe.directory={Path.cwd()}"]
    manifest = {"git_commit": command(git_prefix + ["rev-parse", "HEAD"]), "worktree_dirty": bool(command(git_prefix + ["status", "--short"])), "timestamp": timestamp, "os": platform.platform(), "cpu": platform.processor() or platform.machine(), "ram_bytes": memory_bytes(), "compiler_version": "poa-uir/0.1.0", "rustc_version": command(["rustc", "--version"]), "python_version": platform.python_version(), "dataset_seed": json.loads((dataset.parent / "dataset_manifest.json").read_text())["seed"], "dataset_hash": hashlib.sha256(dataset_bytes).hexdigest(), "config_hash": configuration_hash(), "case_count": len(records), "failure_count": len(failures)}
    (args.out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(records), "failures": len(failures), "out": str(args.out)}, sort_keys=True))


def command(args: list[str]) -> str:
    return subprocess.check_output(args, text=True).strip()


def configuration_hash() -> str:
    files = sorted(Path("crates/poa-uir/src").rglob("*.rs"))
    files += sorted(Path("evaluation/uir").glob("*.py"))
    files += [Path("protocol/schemas/uir.schema.json")]
    digest = hashlib.sha256()
    for path in files:
        name = path.as_posix().encode(); payload = path.read_bytes()
        digest.update(len(name).to_bytes(8, "big")); digest.update(name)
        digest.update(len(payload).to_bytes(8, "big")); digest.update(payload)
    return digest.hexdigest()


def memory_bytes() -> int | None:
    try:
        pages = os.sysconf("SC_PHYS_PAGES"); page_size = os.sysconf("SC_PAGE_SIZE"); return pages * page_size
    except (AttributeError, ValueError, OSError): return None


if __name__ == "__main__": main()
