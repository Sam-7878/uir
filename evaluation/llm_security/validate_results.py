"""Fail-closed consistency checks for V2 machine-readable benchmark evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--results", type=Path, required=True); parser.add_argument("--require-publication-eligible", action="store_true")
    args = parser.parse_args(); failures: list[str] = []
    benchmark = load(args.results / "benchmark_metrics_summary.json")
    ablation = load(args.results / "ablation_metrics_summary.json")
    multi = load(args.results / "multi_knockout_summary.json")
    if not (args.results / "statistical_tests.json").exists():
        failures.append("statistical_tests.json missing")
    if args.require_publication_eligible and not all(item.get("publication_eligible") for item in (benchmark, ablation, multi)):
        failures.append("one or more studies are not an actual 1,600-case, >=3-run live-model experiment")
    for name, runs in benchmark.get("summaries", {}).items():
        for metrics in runs:
            raw = metrics["raw_counts"]
            cm = metrics["confusion_matrix"]
            if raw["total"] != raw["attacks"] + raw["benign"]:
                failures.append(f"{name}: attack/benign count mismatch")
            if cm["successful_benign"] + cm["failed_benign"] != raw["benign"]:
                failures.append(f"{name}: benign confusion matrix mismatch")
            if metrics["frr"]["rate"] != (cm["failed_benign"] / raw["benign"] if raw["benign"] else 0.0):
                failures.append(f"{name}: FRR contradicts confusion matrix")
            if metrics["benign_task_success"]["rate"] != (cm["successful_benign"] / raw["benign"] if raw["benign"] else 0.0):
                failures.append(f"{name}: utility contradicts confusion matrix")
    for raw_file in (args.results / "raw_runs").glob("*.jsonl"):
        for line in raw_file.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if {"attack_succeeded", "is_safe", "policy_violated"} & set(record):
                failures.append(f"{raw_file.name}: baseline-owned outcome field found")
                break
    result = {"status": "PASS" if not failures else "FAIL", "failures": failures}
    (args.results / "results_validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True)); return 0 if not failures else 2


if __name__ == "__main__": raise SystemExit(main())
