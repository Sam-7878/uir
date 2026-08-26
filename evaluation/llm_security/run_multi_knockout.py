"""Defense-in-depth masking study for paired component knockouts."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from llm_trust.inference.ollama_client import OllamaClient
from llm_trust.inference.phi35_transformers import Phi35TransformersBackend
from .batch_execution import BatchCoordinator
from .baselines.uir_v2_security import UirV2SecurityPipeline
from .judges import CompositeJudge
from .metrics_v2 import compute_behavioral_metrics
from .run_security_benchmark_v2 import DATASET, RESULTS, evaluate_cases, load_completed_raw, load_dataset, verify_live_ollama

PAIRS = {
    "-context_firewall -output_guard": {"enable_context_firewall": False, "enable_output_guard": False},
    "-policy_engine -capability_gate": {"enable_policy_engine": False, "enable_capability_gate": False},
    "-provenance -entity_verifier": {"enable_provenance": False, "enable_entity_verifier": False},
    "-entity_verifier -output_guard": {"enable_entity_verifier": False, "enable_output_guard": False},
}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--backend", choices=("phi35-transformers", "ollama"), default="phi35-transformers"); parser.add_argument("--model", default="phi3.5:latest"); parser.add_argument("--model-path"); parser.add_argument("--endpoint", default="http://127.0.0.1:11434"); parser.add_argument("--runs", type=int, default=3); parser.add_argument("--max-cases", type=int); parser.add_argument("--allow-fallback", action="store_true")
    parser.add_argument("--dataset", type=Path, default=DATASET); parser.add_argument("--results", type=Path, default=RESULTS); parser.add_argument("--split", choices=("development", "heldout"), default="development"); parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--resume", action="store_true", help="Reuse only complete, ordered, failure-free, case-fingerprinted raw artifacts.")
    args = parser.parse_args()
    if args.backend == "ollama":
        live = None if args.allow_fallback else verify_live_ollama(args.endpoint, args.model); backend = OllamaClient(model_name=args.model, endpoint=args.endpoint, enable_deterministic_fallback=args.allow_fallback, timeout_seconds=60)
    else:
        if args.allow_fallback: raise ValueError("fallback applies only to Ollama")
        live = {"local_transformers_snapshot": args.model_path or "default Phi-3.5 cache"}; backend = Phi35TransformersBackend(args.model_path)
    coordinator = BatchCoordinator(backend, args.batch_size) if args.backend == "phi35-transformers" else None; pipeline_backend = coordinator or backend
    cases = load_dataset(args.dataset); cases = cases[:args.max_cases] if args.max_cases else cases
    expected_attacks = sum(c["attack_class"] != "valid_benign" for c in cases); expected_benign = len(cases) - expected_attacks
    raw_dir = args.results / "raw_runs"; raw_dir.mkdir(parents=True, exist_ok=True)
    study = {}
    for name, config in PAIRS.items():
        study[name] = []
        for run in range(args.runs):
            pipeline = UirV2SecurityPipeline(pipeline_backend, **config)
            raw = raw_dir / f"{args.split}-multi-{name.replace(' ', '_')}-run-{run:02d}.jsonl"
            expected_model = args.model if args.backend == "ollama" else "microsoft/Phi-3.5-mini-instruct"
            if args.resume and raw.exists():
                records = load_completed_raw(raw, cases, expected_model)
                print(json.dumps({"resumed": raw.name, "records": len(records)}, sort_keys=True), flush=True)
            else:
                records = evaluate_cases(pipeline, cases, CompositeJudge(), coordinator)
                raw.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records), encoding="utf-8")
            study[name].append(compute_behavioral_metrics(records))
    expected_size = 1600 if args.split == "development" else 320
    failures = sum(m["inference_failures"]["count"] for runs in study.values() for m in runs)
    eligible = (args.backend == "phi35-transformers" and not args.allow_fallback and args.runs >= 3 and len(cases) == expected_size and expected_attacks > 0 and expected_benign > 0 and failures == 0 and len(study) == 4 and all(len(runs) == args.runs for runs in study.values()))
    result = {"study": "multi_knockout_masking_v2", "split": args.split, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "backend": args.backend, "model": args.model if args.backend == "ollama" else "microsoft/Phi-3.5-mini-instruct", "runtime": live, "runs": args.runs, "fallback_allowed": args.allow_fallback, "publication_eligible": eligible, "expected_counts": {"total": len(cases), "attacks": expected_attacks, "benign": expected_benign}, "dataset_sha256": __import__("hashlib").sha256(args.dataset.read_bytes()).hexdigest(), "results": study}
    args.results.mkdir(parents=True, exist_ok=True); output_name = "multi_knockout_summary.json" if args.split == "development" else "heldout_multi_knockout_summary.json"; (args.results / output_name).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"publication_eligible": result["publication_eligible"], "pairs": len(PAIRS)}, sort_keys=True))


if __name__ == "__main__": main()
