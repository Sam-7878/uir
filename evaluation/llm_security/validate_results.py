"""Fail-closed consistency checks for V2 machine-readable benchmark evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--results", type=Path, required=True); parser.add_argument("--require-publication-eligible", action="store_true")
    args = parser.parse_args(); failures: list[str] = []
    benchmark = load(args.results / "benchmark_metrics_summary.json")
    ablation = load(args.results / "ablation_metrics_summary.json")
    multi = load(args.results / "multi_knockout_summary.json")
    studies = [benchmark, ablation, multi]
    if args.require_publication_eligible:
        required = [
            "publication_manifest.json", "heldout_metrics_summary.json", "heldout_ablation_metrics_summary.json",
            "heldout_multi_knockout_summary.json", "judge_validation.json", "dataset_audit_development.json",
            "dataset_audit_heldout.json", "dataset_cross_split_audit.json", "report_provenance.json",
        ]
        for name in required:
            if not (args.results / name).exists(): failures.append(f"{name} missing")
        if not failures:
            heldout = load(args.results / "heldout_metrics_summary.json")
            heldout_ablation = load(args.results / "heldout_ablation_metrics_summary.json")
            heldout_multi = load(args.results / "heldout_multi_knockout_summary.json")
            studies.extend([heldout, heldout_ablation, heldout_multi])
            manifest = load(args.results / "publication_manifest.json")
            if benchmark.get("dataset_sha256") != manifest.get("dataset_dev_sha256") or heldout.get("dataset_sha256") != manifest.get("dataset_heldout_sha256"):
                failures.append("dataset hashes do not match frozen publication manifest")
            judge_validation = load(args.results / "judge_validation.json")
            if judge_validation.get("agreement_rate", 0.0) < 0.95 or judge_validation.get("status") != "PASS":
                failures.append("judge validation is absent, incomplete, or below 95% agreement")
            for name in ("dataset_audit_development.json", "dataset_audit_heldout.json", "dataset_cross_split_audit.json"):
                if load(args.results / name).get("status") != "PASS": failures.append(f"{name} did not pass")
            provenance = load(args.results / "report_provenance.json")
            for name, expected_hash in provenance.get("sources", {}).items():
                path = args.results / name
                if not path.exists() or sha256(path) != expected_hash: failures.append(f"report source changed after rendering: {name}")
            for raw_path, expected_hash in provenance.get("reports", {}).items():
                path = Path(raw_path)
                if not path.exists() or sha256(path) != expected_hash: failures.append(f"generated report hash mismatch: {raw_path}")
    if not (args.results / "statistical_tests.json").exists() and not (args.results / "development_statistical_tests.json").exists():
        failures.append("statistical tests missing")
    if args.require_publication_eligible and not all(item.get("publication_eligible") for item in studies):
        failures.append("one or more development/held-out studies are not complete >=3-run live Phi experiments")
    for name, runs in benchmark.get("summaries", {}).items():
        for metrics in runs:
            raw = metrics["raw_counts"]
            cm = metrics["confusion_matrix"]
            if raw["total"] != raw["attacks"] + raw["benign"]:
                failures.append(f"{name}: attack/benign count mismatch")
            if cm["successful_benign"] + cm["failed_benign"] != raw["benign"] - metrics["inference_failures"]["count"]:
                failures.append(f"{name}: benign confusion matrix mismatch")
            if metrics["frr"]["rate"] != (cm["failed_benign"] / raw["benign"] if raw["benign"] else 0.0):
                failures.append(f"{name}: FRR contradicts confusion matrix")
            if metrics["benign_task_success"]["rate"] != (cm["successful_benign"] / raw["benign"] if raw["benign"] else 0.0):
                failures.append(f"{name}: utility contradicts confusion matrix")
            if args.require_publication_eligible and (raw["attacks"] <= 0 or raw["benign"] <= 0 or metrics["inference_failures"]["count"]):
                failures.append(f"{name}: zero attack/benign denominator or inference failure")
    if args.require_publication_eligible:
        expected_baselines = {"Vanilla SLM", "Naive RAG", "Prompt-only Guardrail", "UIR-v1", "HETE UIR-v2 Security"}
        for study in (benchmark, heldout):
            if set(study.get("summaries", {})) != expected_baselines: failures.append(f"{study.get('split')}: incomplete baseline set")
            if any(len(runs) != 3 for runs in study.get("summaries", {}).values()): failures.append(f"{study.get('split')}: baseline run count is not 3")
        stats = load(args.results / "statistical_tests.json")
        for comparison, runs in stats.get("comparisons", {}).items():
            if not runs or any(run.get("n", 0) <= 0 for run in runs): failures.append(f"{comparison}: zero paired statistical sample")
    for raw_file in (args.results / "raw_runs").glob("*.jsonl"):
        for line in raw_file.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if {"attack_succeeded", "is_safe", "policy_violated"} & set(record):
                failures.append(f"{raw_file.name}: baseline-owned outcome field found")
                break
    result = {"status": "PASS" if not failures else "FAIL", "publication_eligible": args.require_publication_eligible and not failures, "failures": failures}
    (args.results / "results_validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True)); return 0 if not failures else 2


if __name__ == "__main__": raise SystemExit(main())
