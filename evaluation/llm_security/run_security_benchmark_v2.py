"""Run the actual Phi-3.5 behavioral security benchmark with a common oracle."""
from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import requests

from llm_trust.inference.ollama_client import OllamaClient
from llm_trust.inference.phi35_transformers import Phi35TransformersBackend
from .batch_execution import BatchCoordinator, DeferredInference
from .attacks.generator_v2 import generate_v2_datasets
from .baselines import NaiveRagBaseline, PromptGuardBaseline, UirV1Baseline, UirV2SecurityPipeline, VanillaSlmBaseline
from .judges import CompositeJudge
from .metrics_v2 import compute_behavioral_metrics
from .statistics_v2 import paired_mcnemar

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "evaluation/llm_security/datasets/security_benchmark_v2_development.jsonl"
RESULTS = ROOT / "results/llm_security_v2"


def load_dataset(path: Path) -> list[Dict[str, Any]]:
    if not path.exists():
        generate_v2_datasets()
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_completed_raw(path: Path, cases: list[Dict[str, Any]], expected_model: str) -> list[Dict[str, Any]]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected_ids = [case["case_id"] for case in cases]
    if len(records) != len(cases) or [record.get("case_id") for record in records] != expected_ids:
        raise AssertionError(f"resume artifact is incomplete or reordered: {path}")
    if any(record.get("model_name") not in {None, expected_model} for record in records):
        raise AssertionError(f"resume artifact model mismatch: {path}")
    if any(record.get("failure_type") for record in records):
        raise AssertionError(f"resume artifact contains inference failures: {path}")
    expected_hashes = [
        __import__("hashlib").sha256(
            json.dumps(case, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        for case in cases
    ]
    if [record.get("case_sha256") for record in records] != expected_hashes:
        raise AssertionError(f"resume artifact dataset fingerprint mismatch: {path}")
    return records


def verify_live_ollama(endpoint: str, model: str) -> Dict[str, Any]:
    response = requests.get(endpoint.rstrip("/") + "/api/tags", timeout=5)
    response.raise_for_status()
    names = [item.get("name", "") for item in response.json().get("models", [])]
    if model not in names and not any(name.split(":", 1)[0] == model.split(":", 1)[0] for name in names):
        raise RuntimeError(f"Phi model '{model}' is not available from {endpoint}; discovered={names}")
    return {"endpoint": endpoint, "models": names}


def evaluate_case(baseline: Any, case: Dict[str, Any], judge: CompositeJudge) -> Dict[str, Any]:
    try:
        record = baseline.run_case(case)
    except DeferredInference:
        raise
    except Exception as exc:
        from .execution import new_execution_record
        record = new_execution_record(case, baseline.__class__.__name__)
        message = f"{type(exc).__name__}: {exc}"
        lowered = message.lower()
        if "out of memory" in lowered:
            failure_type = "CUDA_OOM"
        elif "timeout" in lowered:
            failure_type = "TIMEOUT"
        elif "cuda" in lowered or "model" in lowered:
            failure_type = "MODEL_ERROR"
        else:
            failure_type = "BACKEND_ERROR"
        record.update({"terminal_status": "ERROR", "failure_type": failure_type, "failure_detail": message[:1000]})
    prohibited = {"attack_succeeded", "is_safe", "policy_violated", "dlp_violation"} & set(record)
    if prohibited:
        raise AssertionError(f"tested baseline wrote judge-owned fields: {sorted(prohibited)}")
    if not record.get("resource_budget"):
        record["resource_budget"] = case.get("attack_goal", {}).get("bounds", {"max_input_tokens": 4096, "max_output_tokens": 1024, "max_retrievals": 5, "max_tool_calls": 0, "max_depth": 3, "timeout_ms": 10000})
    return {**record, **judge.evaluate(case, record)}


def evaluate_cases(pipeline: Any, cases: list[Dict[str, Any]], judge: CompositeJudge,
                   coordinator: BatchCoordinator | None = None) -> list[Dict[str, Any]]:
    if coordinator is None:
        return [evaluate_case(pipeline, case, judge) for case in cases]
    coordinator.clear()
    completed: Dict[str, Dict[str, Any]] = {}
    deferred: list[Dict[str, Any]] = []
    for case in cases:
        try:
            completed[case["case_id"]] = evaluate_case(pipeline, case, judge)
        except DeferredInference:
            deferred.append(case)
    coordinator.resolve()
    for case in deferred:
        completed[case["case_id"]] = evaluate_case(pipeline, case, judge)
    if len(completed) != len(cases):
        raise AssertionError(f"incomplete execution: expected {len(cases)}, got {len(completed)}")
    return [completed[case["case_id"]] for case in cases]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("phi35-transformers", "ollama"), default="phi35-transformers")
    parser.add_argument("--model", default="phi3.5:latest")
    parser.add_argument("--model-path")
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--results", type=Path, default=RESULTS)
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--resume", action="store_true", help="Reuse only complete, ordered, failure-free raw artifacts.")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260826)
    parser.add_argument("--max-cases", type=int)
    parser.add_argument("--allow-fallback", action="store_true", help="Smoke testing only; output is marked non-publication.")
    args = parser.parse_args()
    if args.backend == "ollama":
        live = None if args.allow_fallback else verify_live_ollama(args.endpoint, args.model)
        backend = OllamaClient(model_name=args.model, endpoint=args.endpoint, enable_deterministic_fallback=args.allow_fallback, timeout_seconds=60)
    else:
        if args.allow_fallback:
            raise ValueError("--allow-fallback applies only to the Ollama smoke-test backend")
        live = {"local_transformers_snapshot": args.model_path or "default Phi-3.5 cache"}
        backend = Phi35TransformersBackend(model_path=args.model_path)
    coordinator = BatchCoordinator(backend, args.batch_size) if args.backend == "phi35-transformers" else None
    pipeline_backend = coordinator or backend
    cases = load_dataset(args.dataset)
    if args.max_cases:
        cases = cases[:args.max_cases]
    expected_total = len(cases)
    expected_attacks = sum(case["attack_class"] != "valid_benign" for case in cases)
    expected_benign = expected_total - expected_attacks
    baselines = {"Vanilla SLM": VanillaSlmBaseline, "Naive RAG": NaiveRagBaseline, "Prompt-only Guardrail": PromptGuardBaseline, "UIR-v1": UirV1Baseline, "HETE UIR-v2 Security": UirV2SecurityPipeline}
    args.results.mkdir(parents=True, exist_ok=True)
    raw_dir = args.results / "raw_runs"; raw_dir.mkdir(exist_ok=True)
    summaries: Dict[str, Any] = {}
    paired_records: Dict[int, Dict[str, list[Dict[str, Any]]]] = {}
    for run in range(args.runs):
        random.seed(args.seed + run)
        for name, factory in baselines.items():
            raw_path = raw_dir / f"{args.split}-run-{run:02d}-{name.lower().replace(' ', '_').replace('/', '_')}.jsonl"
            expected_model = args.model if args.backend == "ollama" else "microsoft/Phi-3.5-mini-instruct"
            if args.resume and raw_path.exists():
                records = load_completed_raw(raw_path, cases, expected_model)
                print(json.dumps({"resumed": raw_path.name, "records": len(records)}, sort_keys=True), flush=True)
            else:
                judge = CompositeJudge(); pipeline = factory(pipeline_backend)
                records = evaluate_cases(pipeline, cases, judge, coordinator)
            metrics = compute_behavioral_metrics(records)
            raw_counts = metrics["raw_counts"]
            if (raw_counts["total"], raw_counts["attacks"], raw_counts["benign"]) != (expected_total, expected_attacks, expected_benign):
                raise AssertionError(f"{name} incomplete counts: {raw_counts}")
            paired_records.setdefault(run, {})[name] = records
            if not (args.resume and raw_path.exists()):
                raw_path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
            summaries.setdefault(name, []).append(metrics)
    statistical_tests = {"method": "paired_exact_mcnemar", "comparisons": {}}
    for name in baselines:
        if name == "HETE UIR-v2 Security": continue
        statistical_tests["comparisons"][name] = [paired_mcnemar(paired_records[run][name], paired_records[run]["HETE UIR-v2 Security"]) for run in range(args.runs)]
    stats_name = "development_statistical_tests.json" if args.split == "development" else "statistical_tests.json"
    (args.results / stats_name).write_text(json.dumps(statistical_tests, indent=2) + "\n", encoding="utf-8")
    expected_size = 1600 if args.split == "development" else 320
    failures = sum(metrics["inference_failures"]["count"] for runs in summaries.values() for metrics in runs)
    publication_eligible = (args.backend == "phi35-transformers" and not args.allow_fallback and args.runs >= 3
                            and len(cases) == expected_size and expected_attacks > 0 and expected_benign > 0
                            and failures == 0 and len(summaries) == 5 and all(len(runs) == args.runs for runs in summaries.values()))
    manifest = {"benchmark": "HETE UIR Security Benchmark v2", "split": args.split, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "backend": args.backend, "model": args.model if args.backend == "ollama" else "microsoft/Phi-3.5-mini-instruct", "runtime": live, "fallback_allowed": args.allow_fallback, "publication_eligible": publication_eligible, "runs": args.runs, "seed": args.seed, "expected_counts": {"total": expected_total, "attacks": expected_attacks, "benign": expected_benign}, "dataset_path": str(args.dataset), "dataset_sha256": __import__("hashlib").sha256(args.dataset.read_bytes()).hexdigest(), "summaries": summaries}
    output_name = "benchmark_metrics_summary.json" if args.split == "development" else "heldout_metrics_summary.json"
    (args.results / output_name).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"publication_eligible": manifest["publication_eligible"], "runs": args.runs, "cases": len(cases), "baselines": list(summaries)}, sort_keys=True))


if __name__ == "__main__":
    main()
