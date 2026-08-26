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


def verify_live_ollama(endpoint: str, model: str) -> Dict[str, Any]:
    response = requests.get(endpoint.rstrip("/") + "/api/tags", timeout=5)
    response.raise_for_status()
    names = [item.get("name", "") for item in response.json().get("models", [])]
    if model not in names and not any(name.split(":", 1)[0] == model.split(":", 1)[0] for name in names):
        raise RuntimeError(f"Phi model '{model}' is not available from {endpoint}; discovered={names}")
    return {"endpoint": endpoint, "models": names}


def evaluate_case(baseline: Any, case: Dict[str, Any], judge: CompositeJudge) -> Dict[str, Any]:
    record = baseline.run_case(case)
    prohibited = {"attack_succeeded", "is_safe", "policy_violated", "dlp_violation"} & set(record)
    if prohibited:
        raise AssertionError(f"tested baseline wrote judge-owned fields: {sorted(prohibited)}")
    if not record.get("resource_budget"):
        record["resource_budget"] = case.get("attack_goal", {}).get("bounds", {"max_input_tokens": 4096, "max_output_tokens": 1024, "max_retrievals": 5, "max_tool_calls": 0, "max_depth": 3, "timeout_ms": 10000})
    return {**record, **judge.evaluate(case, record)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("phi35-transformers", "ollama"), default="phi35-transformers")
    parser.add_argument("--model", default="phi3.5:latest")
    parser.add_argument("--model-path")
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
    cases = load_dataset(DATASET)
    if args.max_cases:
        cases = cases[:args.max_cases]
    baselines = {"Vanilla SLM": VanillaSlmBaseline, "Naive RAG": NaiveRagBaseline, "Prompt-only Guardrail": PromptGuardBaseline, "UIR-v1": UirV1Baseline, "HETE UIR-v2 Security": UirV2SecurityPipeline}
    RESULTS.mkdir(parents=True, exist_ok=True)
    raw_dir = RESULTS / "raw_runs"; raw_dir.mkdir(exist_ok=True)
    summaries: Dict[str, Any] = {}
    paired_records: Dict[int, Dict[str, list[Dict[str, Any]]]] = {}
    for run in range(args.runs):
        random.seed(args.seed + run)
        for name, factory in baselines.items():
            judge = CompositeJudge(); pipeline = factory(backend)
            records = [evaluate_case(pipeline, case, judge) for case in cases]
            paired_records.setdefault(run, {})[name] = records
            raw_path = raw_dir / f"run-{run:02d}-{name.lower().replace(' ', '_').replace('/', '_')}.jsonl"
            raw_path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
            summaries.setdefault(name, []).append(compute_behavioral_metrics(records))
    statistical_tests = {"method": "paired_exact_mcnemar", "comparisons": {}}
    for name in baselines:
        if name == "HETE UIR-v2 Security": continue
        statistical_tests["comparisons"][name] = [paired_mcnemar(paired_records[run][name], paired_records[run]["HETE UIR-v2 Security"]) for run in range(args.runs)]
    (RESULTS / "statistical_tests.json").write_text(json.dumps(statistical_tests, indent=2) + "\n", encoding="utf-8")
    manifest = {"benchmark": "HETE UIR Security Benchmark v2", "timestamp_utc": datetime.now(timezone.utc).isoformat(), "backend": args.backend, "model": args.model if args.backend == "ollama" else "microsoft/Phi-3.5-mini-instruct", "runtime": live, "fallback_allowed": args.allow_fallback, "publication_eligible": not args.allow_fallback and args.runs >= 3 and len(cases) == 1600, "runs": args.runs, "seed": args.seed, "dataset_path": str(DATASET), "dataset_sha256": __import__("hashlib").sha256(DATASET.read_bytes()).hexdigest(), "summaries": summaries}
    (RESULTS / "benchmark_metrics_summary.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"publication_eligible": manifest["publication_eligible"], "runs": args.runs, "cases": len(cases), "baselines": list(summaries)}, sort_keys=True))


if __name__ == "__main__":
    main()
