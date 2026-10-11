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
from .batch_execution import BatchCoordinator
from .judges import CompositeJudge
from .metrics_v2 import compute_behavioral_metrics
from .run_security_benchmark_v2 import DATASET, RESULTS, evaluate_cases, load_completed_raw, load_dataset, reevaluate_records, verify_live_ollama
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
    parser.add_argument("--dataset", type=Path, default=DATASET); parser.add_argument("--results", type=Path, default=RESULTS)
    parser.add_argument("--split", choices=("development", "heldout"), default="development"); parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--resume", action="store_true", help="Reuse only complete, ordered, failure-free, case-fingerprinted raw artifacts.")
    args = parser.parse_args()
    if args.backend == "ollama":
        live = None if args.allow_fallback else verify_live_ollama(args.endpoint, args.model)
        backend = OllamaClient(model_name=args.model, endpoint=args.endpoint, enable_deterministic_fallback=args.allow_fallback, timeout_seconds=60)
    else:
        if args.allow_fallback: raise ValueError("fallback applies only to Ollama")
        live = {"local_transformers_snapshot": args.model_path or "default Phi-3.5 cache"}; backend = Phi35TransformersBackend(args.model_path)
    coordinator = BatchCoordinator(backend, args.batch_size) if args.backend == "phi35-transformers" else None
    pipeline_backend = coordinator or backend
    cases = load_dataset(args.dataset); cases = cases[:args.max_cases] if args.max_cases else cases
    expected_total = len(cases); expected_attacks = sum(c["attack_class"] != "valid_benign" for c in cases); expected_benign = expected_total - expected_attacks
    raw_dir = args.results / "raw_runs"; raw_dir.mkdir(parents=True, exist_ok=True)
    summary: Dict[str, Any] = {"full": [], "knockouts": {}, "targeted_full": {}, "targeted": {}}
    for run in range(args.runs):
        for name, pipeline in configurations(pipeline_backend).items():
            raw = raw_dir / f"{args.split}-ablation-{run:02d}-{name.replace(' ', '_')}.jsonl"
            expected_model = args.model if args.backend == "ollama" else "microsoft/Phi-3.5-mini-instruct"
            if args.resume and raw.exists():
                records = load_completed_raw(raw, cases, expected_model)
                records = reevaluate_records(cases, records, CompositeJudge())
                print(json.dumps({"resumed": raw.name, "records": len(records)}, sort_keys=True), flush=True)
            else:
                records = evaluate_cases(pipeline, cases, CompositeJudge(), coordinator)
            raw.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in records), encoding="utf-8")
            metrics = compute_behavioral_metrics(records)
            if name == "Full UIR-v2 Security":
                summary["full"].append(metrics)
                for knockout, classes in TARGETS.items():
                    targeted_full = [item for item in records if item["attack_class"] in classes]
                    summary["targeted_full"].setdefault(knockout, []).append(compute_behavioral_metrics(targeted_full))
            else:
                summary["knockouts"].setdefault(name, []).append(metrics)
                targeted = [item for item in records if item["attack_class"] in TARGETS[name]]
                summary["targeted"].setdefault(name, []).append(compute_behavioral_metrics(targeted))
    deltas = {}
    for name, runs in summary["knockouts"].items():
        per_run = []
        for index, current in enumerate(runs):
            full = summary["full"][index]
            targeted_current = summary["targeted"][name][index]; targeted_full = summary["targeted_full"][name][index]
            per_run.append({"delta_e2e_asr": current["e2e_asr_overall"]["rate"] - full["e2e_asr_overall"]["rate"], "delta_mcr": current["mcr_overall"]["rate"] - full["mcr_overall"]["rate"], "delta_frr": current["frr"]["rate"] - full["frr"]["rate"], "delta_utility": current["benign_task_success"]["rate"] - full["benign_task_success"]["rate"], "delta_latency_ms": current["latency_ms"]["mean"] - full["latency_ms"]["mean"], "targeted_delta_e2e_asr": targeted_current["e2e_asr_overall"]["rate"] - targeted_full["e2e_asr_overall"]["rate"], "targeted_delta_mcr": targeted_current["mcr_overall"]["rate"] - targeted_full["mcr_overall"]["rate"]})
        keys = per_run[0]
        deltas[name] = {key: sum(run[key] for run in per_run) / len(per_run) for key in keys}
        deltas[name]["per_run"] = per_run
        deltas[name]["targeted_degradation_observed"] = deltas[name]["targeted_delta_e2e_asr"] > 0 or deltas[name]["targeted_delta_mcr"] > 0
    expected_size = 1600 if args.split == "development" else 320
    all_metrics = summary["full"] + [m for runs in summary["knockouts"].values() for m in runs]
    failures = sum(m["inference_failures"]["count"] for m in all_metrics)
    eligible = (args.backend == "phi35-transformers" and not args.allow_fallback and args.runs >= 3 and len(cases) == expected_size
                and expected_attacks > 0 and expected_benign > 0 and failures == 0 and len(summary["knockouts"]) == 7
                and len(summary["full"]) == args.runs and all(len(runs) == args.runs for runs in summary["knockouts"].values()))
    manifest = {"study": "single_component_ablation_v2", "split": args.split, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "backend": args.backend, "model": args.model if args.backend == "ollama" else "microsoft/Phi-3.5-mini-instruct", "runtime": live, "runs": args.runs, "fallback_allowed": args.allow_fallback, "publication_eligible": eligible, "expected_counts": {"total": expected_total, "attacks": expected_attacks, "benign": expected_benign}, "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(), "results": summary, "deltas": deltas}
    args.results.mkdir(parents=True, exist_ok=True); output_name = "ablation_metrics_summary.json" if args.split == "development" else "heldout_ablation_metrics_summary.json"; (args.results / output_name).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"publication_eligible": manifest["publication_eligible"], "configurations": len(configurations(backend))}, sort_keys=True))


if __name__ == "__main__": main()
