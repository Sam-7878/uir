"""Defense-in-depth masking study for paired component knockouts."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from llm_trust.inference.ollama_client import OllamaClient
from llm_trust.inference.phi35_transformers import Phi35TransformersBackend
from .baselines.uir_v2_security import UirV2SecurityPipeline
from .judges import CompositeJudge
from .metrics_v2 import compute_behavioral_metrics
from .run_security_benchmark_v2 import DATASET, RESULTS, evaluate_case, load_dataset, verify_live_ollama

PAIRS = {
    "-context_firewall -output_guard": {"enable_context_firewall": False, "enable_output_guard": False},
    "-policy_engine -capability_gate": {"enable_policy_engine": False, "enable_capability_gate": False},
    "-provenance -entity_verifier": {"enable_provenance": False, "enable_entity_verifier": False},
    "-entity_verifier -output_guard": {"enable_entity_verifier": False, "enable_output_guard": False},
}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--backend", choices=("phi35-transformers", "ollama"), default="phi35-transformers"); parser.add_argument("--model", default="phi3.5:latest"); parser.add_argument("--model-path"); parser.add_argument("--endpoint", default="http://127.0.0.1:11434"); parser.add_argument("--runs", type=int, default=3); parser.add_argument("--max-cases", type=int); parser.add_argument("--allow-fallback", action="store_true")
    args = parser.parse_args()
    if args.backend == "ollama":
        live = None if args.allow_fallback else verify_live_ollama(args.endpoint, args.model); backend = OllamaClient(model_name=args.model, endpoint=args.endpoint, enable_deterministic_fallback=args.allow_fallback, timeout_seconds=60)
    else:
        if args.allow_fallback: raise ValueError("fallback applies only to Ollama")
        live = {"local_transformers_snapshot": args.model_path or "default Phi-3.5 cache"}; backend = Phi35TransformersBackend(args.model_path)
    cases = load_dataset(DATASET); cases = cases[:args.max_cases] if args.max_cases else cases
    study = {}
    for name, config in PAIRS.items():
        study[name] = []
        for _ in range(args.runs):
            pipeline = UirV2SecurityPipeline(backend, **config)
            study[name].append(compute_behavioral_metrics([evaluate_case(pipeline, case, CompositeJudge()) for case in cases]))
    result = {"study": "multi_knockout_masking_v2", "timestamp_utc": datetime.now(timezone.utc).isoformat(), "backend": args.backend, "model": args.model if args.backend == "ollama" else "microsoft/Phi-3.5-mini-instruct", "runtime": live, "runs": args.runs, "fallback_allowed": args.allow_fallback, "publication_eligible": not args.allow_fallback and args.runs >= 3 and len(cases) == 1600, "results": study}
    RESULTS.mkdir(parents=True, exist_ok=True); (RESULTS / "multi_knockout_summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"publication_eligible": result["publication_eligible"], "pairs": len(PAIRS)}, sort_keys=True))


if __name__ == "__main__": main()
