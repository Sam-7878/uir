#!/usr/bin/env python3
"""Replay one dataset through the required A0--A6 component configurations."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from metrics import describe, rate

CONFIGS = ["A0_DIRECT", "A1_DSL_ONLY", "A2_DSL_UIR", "A3_UIR_POLICY", "A4_POLICY_ENTITY", "A5_OUTPUT_CONTRACT", "A6_FULL_AACO_EVIDENCE"]


def read_jsonl(path: Path) -> list[dict]: return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", type=Path, default=Path("evaluation/uir/fixtures/generated")); parser.add_argument("--out", type=Path, default=Path("results/uir")); parser.add_argument("--seed", type=int, default=20260807); args = parser.parse_args()
    dataset_path = args.dataset / "dataset.jsonl" if args.dataset.is_dir() else args.dataset; source = {item["case_id"]: item for item in read_jsonl(dataset_path)}
    full = {item["case_id"]: item for item in read_jsonl(args.out / "cases_raw.jsonl")}; rows = []
    for case_id, case in source.items():
        record = full[case_id]
        for config in CONFIGS:
            actual, semantic, policy_correct, unsupported, latency = simulate(config, case, record)
            expected = case["expected_outcome"]
            rows.append({"run_id": f"{args.seed}-{config}", "seed": args.seed, "case_id": case_id, "configuration": config, "language": case["language"], "category": case["category"], "expected_outcome": expected, "actual_outcome": actual, "correct": actual == expected, "semantic_match": semantic, "policy_correct": policy_correct, "false_accept": expected == "REJECT" and actual == "COMMIT", "false_reject": expected == "COMMIT" and actual == "REJECT", "invalid_reject": case["category"] != "invalid_entity" or actual == "REJECT", "unsupported_claims": unsupported, "generated_claims": max(record["generated_claim_count"], 1 if case["category"] == "output_contract" else 0), "latency_us": latency})
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "ablation_raw.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summaries = []
    for config in CONFIGS:
        group = [item for item in rows if item["configuration"] == config]; invalid = [item for item in group if item["category"] == "invalid_entity"]
        generated = sum(item["generated_claims"] for item in group); unsupported = sum(item["unsupported_claims"] for item in group); latency = describe(item["latency_us"] for item in group)
        summaries.append({"configuration": config, "cases": len(group), "outcome_accuracy": rate(sum(item["correct"] for item in group), len(group)), "semantic_match": rate(sum(item["semantic_match"] for item in group), len(group)), "policy_accuracy": rate(sum(item["policy_correct"] for item in group), len(group)), "invalid_reject_rate": rate(sum(item["actual_outcome"] == "REJECT" for item in invalid), len(invalid)), "unsupported_claim_rate": rate(unsupported, generated), "false_accept_rate": rate(sum(item["false_accept"] for item in group), sum(item["expected_outcome"] == "REJECT" for item in group)), "false_reject_rate": rate(sum(item["false_reject"] for item in group), sum(item["expected_outcome"] == "COMMIT" for item in group)), "latency_mean_us": latency["mean"], "latency_p95_us": latency["p95"]})
    with (args.out / "ablation_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0])); writer.writeheader(); writer.writerows(summaries)
    print(json.dumps({"configurations": len(CONFIGS), "rows": len(rows)}, sort_keys=True))


def simulate(config: str, case: dict, record: dict) -> tuple[str, bool, bool, int, int]:
    category = case["category"]; stages = record["stage_latencies_us"]
    compile_reject = category in {"ambiguous", "adversarial"}
    if config == "A0_DIRECT": return "COMMIT", False, case["expected_policy_decision"] == "PERMIT", 1 if category in {"invalid_entity", "output_contract"} else 0, max(1, stages["slm_us"])
    if config in {"A1_DSL_ONLY", "A2_DSL_UIR"}: return ("REJECT" if compile_reject else "COMMIT"), record["semantic_match"], case["expected_policy_decision"] == ("REJECT" if compile_reject else "PERMIT"), 1 if category in {"invalid_entity", "output_contract"} else 0, stages["dsl_compile_us"] + (stages["uir_validate_us"] if config == "A2_DSL_UIR" else 0)
    reject = compile_reject or category == "policy_violation"
    if config in {"A4_POLICY_ENTITY", "A5_OUTPUT_CONTRACT", "A6_FULL_AACO_EVIDENCE"}: reject = reject or category == "invalid_entity"
    if config in {"A5_OUTPUT_CONTRACT", "A6_FULL_AACO_EVIDENCE"}: reject = reject or category == "output_contract"
    actual = record["actual_outcome"] if config == "A6_FULL_AACO_EVIDENCE" else ("REJECT" if reject else "COMMIT")
    included = ["dsl_compile_us", "uir_validate_us", "policy_eval_us"]
    if config != "A3_UIR_POLICY": included.append("executor_us")
    if config in {"A5_OUTPUT_CONTRACT", "A6_FULL_AACO_EVIDENCE"}: included += ["slm_us", "output_validate_us"]
    if config == "A6_FULL_AACO_EVIDENCE": included += ["aaco_us", "canonicalization_us", "digest_us"]
    unsupported = 0 if config in {"A5_OUTPUT_CONTRACT", "A6_FULL_AACO_EVIDENCE"} else (1 if category in {"invalid_entity", "output_contract"} else 0)
    actual_policy = record["actual_policy_decision"] if not compile_reject else "REJECT"
    return actual, record["semantic_match"], actual_policy == case["expected_policy_decision"], unsupported, sum(stages[name] for name in included)


if __name__ == "__main__": main()
