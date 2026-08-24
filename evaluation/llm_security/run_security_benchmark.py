"""Run Complete Security Benchmark (5 Baselines on 1,600 Cases)."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from llm_trust.inference.ollama_client import OllamaClient
from .attacks.generator import generate_and_save_dataset
from .baselines import (
    NaiveRagBaseline,
    PromptGuardBaseline,
    UirV1Baseline,
    UirV2SecurityPipeline,
    VanillaSlmBaseline,
)
from .metrics import compute_metrics


DATASET_PATH = Path(__file__).parent / "datasets" / "security_benchmark_1600.jsonl"
RESULTS_DIR = Path(__file__).parents[2] / "results" / "llm_security"


def load_dataset() -> List[Dict[str, Any]]:
    if not DATASET_PATH.exists():
        generate_and_save_dataset(DATASET_PATH)
    cases = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def run_full_security_benchmark() -> Dict[str, Any]:
    cases = load_dataset()
    print(f"Loaded {len(cases)} benchmark cases from {DATASET_PATH.name}")

    backend = OllamaClient(model_name="phi3.5:latest", enable_deterministic_fallback=True)

    baselines = {
        "Vanilla SLM": VanillaSlmBaseline(backend),
        "Naive RAG": NaiveRagBaseline(backend),
        "Prompt-only Guardrail": PromptGuardBaseline(backend),
        "UIR-v1": UirV1Baseline(backend),
        "HETE UIR-v2 Security": UirV2SecurityPipeline(backend),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    raw_results_path = RESULTS_DIR / "raw_benchmark_results.jsonl"
    metrics_summary_path = RESULTS_DIR / "benchmark_metrics_summary.json"

    all_raw_records: List[Dict[str, Any]] = []
    baseline_summaries: Dict[str, Any] = {}

    start_total = time.perf_counter()

    with open(raw_results_path, "w", encoding="utf-8") as out_f:
        for name, baseline in baselines.items():
            print(f"Running evaluation for baseline: [{name}] across {len(cases)} cases...")
            baseline_records: List[Dict[str, Any]] = []
            for i, case in enumerate(cases):
                rec = baseline.run_case(case)
                rec["baseline_name"] = name
                baseline_records.append(rec)
                all_raw_records.append(rec)
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            metrics = compute_metrics(baseline_records)
            baseline_summaries[name] = metrics.to_dict()
            print(f"  -> {name}: ASR={metrics.asr_overall*100:.1f}%, Utility={metrics.utility_rate*100:.1f}%, Avg Latency={metrics.avg_latency_ms:.1f}ms")

    elapsed_s = time.perf_counter() - start_total

    manifest = {
        "benchmark_name": "HETE UIR-v2 Zero-Trust Security Benchmark",
        "dataset_cases": len(cases),
        "dataset_path": str(DATASET_PATH),
        "evaluated_baselines": list(baselines.keys()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed_s, 2),
        "summaries": baseline_summaries,
    }

    with open(metrics_summary_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nBenchmark completed in {elapsed_s:.2f}s. Results saved to {RESULTS_DIR}")
    return manifest


if __name__ == "__main__":
    run_full_security_benchmark()
