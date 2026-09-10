"""Run Ablation Experiments (7 Component Ablations on Full 1,600 Cases)."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from llm_trust.inference.ollama_client import OllamaClient
from .baselines.uir_v2_security import UirV2SecurityPipeline
from .metrics import compute_metrics
from .run_security_benchmark import load_dataset


RESULTS_DIR = Path(__file__).parents[2] / "results" / "llm_security"


def run_ablation_experiments() -> Dict[str, Any]:
    cases = load_dataset()
    print(f"Loaded {len(cases)} cases for ablation study.")

    backend = OllamaClient(model_name="phi3.5:latest", enable_deterministic_fallback=True)

    ablations: Dict[str, UirV2SecurityPipeline] = {
        "Full UIR-v2 Security": UirV2SecurityPipeline(backend),
        "-entity_verifier": UirV2SecurityPipeline(backend, enable_entity_verifier=False),
        "-policy_engine": UirV2SecurityPipeline(backend, enable_policy_engine=False),
        "-context_firewall": UirV2SecurityPipeline(backend, enable_context_firewall=False),
        "-provenance": UirV2SecurityPipeline(backend, enable_provenance=False),
        "-capability_gate": UirV2SecurityPipeline(backend, enable_capability_gate=False),
        "-output_guard": UirV2SecurityPipeline(backend, enable_output_guard=False),
        "-resource_guard": UirV2SecurityPipeline(backend, enable_resource_guard=False),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ablation_raw_path = RESULTS_DIR / "raw_ablation_results.jsonl"
    ablation_summary_path = RESULTS_DIR / "ablation_metrics_summary.json"

    ablation_summaries: Dict[str, Any] = {}

    start_total = time.perf_counter()

    with open(ablation_raw_path, "w", encoding="utf-8") as out_f:
        for name, pipeline in ablations.items():
            print(f"Evaluating ablation configuration: [{name}]...")
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=8) as executor:
                records = list(executor.map(pipeline.run_case, cases))

            for rec in records:
                rec["ablation_name"] = name
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            metrics = compute_metrics(records)
            ablation_summaries[name] = metrics.to_dict()
            print(f"  -> {name}: ASR={metrics.asr_overall*100:.1f}%, Utility={metrics.utility_rate*100:.1f}%, Avg Latency={metrics.avg_latency_ms:.1f}ms")

    elapsed_s = time.perf_counter() - start_total

    manifest = {
        "study_name": "HETE UIR-v2 Component Ablation Study",
        "dataset_cases": len(cases),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed_s, 2),
        "ablation_summaries": ablation_summaries,
    }

    with open(ablation_summary_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nAblation study completed in {elapsed_s:.2f}s. Results saved to {ablation_summary_path}")
    return manifest


if __name__ == "__main__":
    run_ablation_experiments()
