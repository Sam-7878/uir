"""Single-component and targeted behavioral ablation study."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from llm_trust.inference.ollama_client import OllamaClient
from llm_trust.inference.phi35_transformers import Phi35TransformersBackend
from .judges import CompositeJudge
from .metrics_v2 import compute_behavioral_metrics
from .run_security_benchmark_v2 import DATASET, RESULTS, evaluate_case, load_dataset, verify_live_ollama
from .baselines.uir_v2_security import UirV2SecurityPipeline

TARGETS = {
    "-entity_verifier": {"nonexistent_entity", "gaslighting_false_premise"},
    "-policy_engine": {"direct_prompt_injection", "jailbreak_policy_override"},
    "-context_firewall": {"indirect_prompt_injection"},
    "-provenance": {"poisoned_retrieval_evidence"},
    "-capability_gate": {"excessive_agency_tool_escalation"},
    "-output_guard": {"sensitive_data_exfiltration"},
    "-resource_guard": {"resource_exhaustion"},
}


def configurations(backend: OllamaClient) -> Dict[str, UirV2SecurityPipeline]:
    return {
        "Full UIR-v2 Security": UirV2SecurityPipeline(backend),
        "-entity_verifier": UirV2SecurityPipeline(backend, enable_entity_verifier=False),
        "-policy_engine": UirV2SecurityPipeline(backend, enable_policy_engine=False),
        "-context_firewall": UirV2SecurityPipeline(backend, enable_context_firewall=False),
        "-provenance": UirV2SecurityPipeline(backend, enable_provenance=False),
        "-capability_gate": UirV2SecurityPipeline(backend, enable_capability_gate=False),
        "-output_guard": UirV2SecurityPipeline(backend, enable_output_guard=False),
        "-resource_guard": UirV2SecurityPipeline(backend, enable_resource_guard=False),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("phi35-transformers", "ollama"), default="phi35-transformers"); parser.add_argument("--model", default="phi3.5:latest"); parser.add_argument("--model-path"); parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--runs", type=int, default=3); parser.add_argument("--max-cases", type=int); parser.add_argument("--allow-fallback", action="store_true")
    args = parser.parse_args()
    if args.backend == "ollama":
        live = None if args.allow_fallback else verify_live_ollama(args.endpoint, args.model)
        backend = OllamaClient(model_name=args.model, endpoint=args.endpoint, enable_deterministic_fallback=args.allow_fallback, timeout_seconds=60)
    else:
        if args.allow_fallback: raise ValueError("fallback applies only to Ollama")
        live = {"local_transformers_snapshot": args.model_path or "default Phi-3.5 cache"}; backend = Phi35TransformersBackend(args.model_path)
    cases = load_dataset(DATASET); cases = cases[:args.max_cases] if args.max_cases else cases
    raw_dir = RESULTS / "raw_runs"; raw_dir.mkdir(parents=True, exist_ok=True)
    summary: Dict[str, Any] = {"full": [], "knockouts": {}, "targeted": {}}
    for run in range(args.runs):
        for name, pipeline in configurations(backend).items():
            records = [evaluate_case(pipeline, case, CompositeJudge()) for case in cases]
            raw = raw_dir / f"ablation-{run:02d}-{name.replace(' ', '_')}.jsonl"
            raw.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in records), encoding="utf-8")
            metrics = compute_behavioral_metrics(records)
            if name == "Full UIR-v2 Security": summary["full"].append(metrics)
            else:
                summary["knockouts"].setdefault(name, []).append(metrics)
                targeted = [item for item in records if item["attack_class"] in TARGETS[name]]
                summary["targeted"].setdefault(name, []).append(compute_behavioral_metrics(targeted))
    full = summary["full"][0]
    deltas = {}
    for name, runs in summary["knockouts"].items():
        current = runs[0]
        deltas[name] = {"delta_e2e_asr": current["e2e_asr_overall"]["rate"] - full["e2e_asr_overall"]["rate"], "delta_mcr": current["mcr_overall"]["rate"] - full["mcr_overall"]["rate"], "delta_frr": current["frr"]["rate"] - full["frr"]["rate"], "delta_utility": current["benign_task_success"]["rate"] - full["benign_task_success"]["rate"], "delta_latency_ms": current["latency_ms"]["mean"] - full["latency_ms"]["mean"], "targeted_degradation_observed": summary["targeted"][name][0]["e2e_asr_overall"]["rate"] > 0 or summary["targeted"][name][0]["mcr_overall"]["rate"] > 0}
    manifest = {"study": "single_component_ablation_v2", "timestamp_utc": datetime.now(timezone.utc).isoformat(), "backend": args.backend, "model": args.model if args.backend == "ollama" else "microsoft/Phi-3.5-mini-instruct", "runtime": live, "runs": args.runs, "fallback_allowed": args.allow_fallback, "publication_eligible": not args.allow_fallback and args.runs >= 3 and len(cases) == 1600, "dataset_sha256": hashlib.sha256(DATASET.read_bytes()).hexdigest(), "results": summary, "deltas": deltas}
    RESULTS.mkdir(parents=True, exist_ok=True); (RESULTS / "ablation_metrics_summary.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"publication_eligible": manifest["publication_eligible"], "configurations": len(configurations(backend))}, sort_keys=True))


if __name__ == "__main__": main()
