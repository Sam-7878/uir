import json
import os
from collections import Counter


ABLATION_CONFIGS = [
    "Full UIR-v2 Security",
    "-entity_verifier",
    "-policy_engine",
    "-context_firewall",
    "-provenance",
    "-capability_gate",
    "-output_guard",
    "-resource_guard",
]

BASELINE_NAMES = [
    "HETE UIR-v2 Security",
    "Naive RAG",
    "Prompt-only Guardrail",
    "UIR-v1",
    "Vanilla SLM",
]


def check():
    bench_file = "results/llm_security/raw_benchmark_results.jsonl"
    ablation_file = "results/llm_security/raw_ablation_results.jsonl"

    print("=== [HETE-UIR Security Evaluation Progress Monitor] ===")

    total_bench = 0
    total_ablation = 0

    # 1. Benchmark status
    if os.path.exists(bench_file):
        bench_counts: Counter = Counter()
        with open(bench_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        d = json.loads(line)
                        b = d.get("baseline_name") or d.get("baseline")
                        if b:
                            bench_counts[b] += 1
                    except Exception:
                        pass
        total_bench = sum(bench_counts.values())
        pct = total_bench / 8000 * 100 if total_bench else 0.0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"\n1. Baseline Benchmark Suite [{bar}] {pct:.1f}%  ({total_bench:,} / 8,000)")
        for b in BASELINE_NAMES:
            count = bench_counts.get(b, 0)
            status = "✅" if count >= 1600 else "⚡"
            print(f"   {status} {b:30s}: {count:5d} / 1,600 ({count / 1600 * 100:.1f}%)")
        # Show any unexpected baselines
        for b, count in sorted(bench_counts.items()):
            if b not in BASELINE_NAMES:
                print(f"   ❓ {b:30s}: {count:5d} / 1,600 ({count / 1600 * 100:.1f}%)")
    else:
        print("\n1. Baseline Benchmark Suite: Not started yet (0 / 8,000)")

    print()

    # 2. Ablation status
    if os.path.exists(ablation_file):
        ablation_counts: Counter = Counter()
        with open(ablation_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        d = json.loads(line)
                        # Field name used in run_ablation_study.py is "ablation_name"
                        c = (
                            d.get("ablation_name")
                            or d.get("ablation_config")
                            or d.get("config")
                        )
                        if c:
                            ablation_counts[c] += 1
                    except Exception:
                        pass
        total_ablation = sum(ablation_counts.values())
        pct = total_ablation / 11200 * 100 if total_ablation else 0.0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"2. Ablation Study Suite   [{bar}] {pct:.1f}%  ({total_ablation:,} / 11,200)")

        # Determine which config is currently running
        running_config = None
        for cfg in ABLATION_CONFIGS:
            cnt = ablation_counts.get(cfg, 0)
            if 0 < cnt < 1600:
                running_config = cfg
                break

        for cfg in ABLATION_CONFIGS:
            count = ablation_counts.get(cfg, 0)
            if count >= 1600:
                status = "✅"
            elif count > 0:
                status = "⚡"  # in progress
            else:
                status = "⏳"  # queued
            print(f"   {status} {cfg:30s}: {count:5d} / 1,600 ({count / 1600 * 100:.1f}%)")

        if running_config:
            remaining = 1600 - ablation_counts.get(running_config, 0)
            print(f"\n   Currently running: [{running_config}] — {remaining} cases left in this config")

        # Show any unexpected configs
        for cfg, count in sorted(ablation_counts.items()):
            if cfg not in ABLATION_CONFIGS:
                print(f"   ❓ {cfg:30s}: {count:5d}")
    else:
        print("2. Ablation Study Suite: Waiting to start (0 / 11,200)")

    # 3. Overall progress
    total_completed = total_bench + total_ablation
    grand_total = 8000 + 11200
    overall_pct = total_completed / grand_total * 100 if total_completed else 0.0
    bar = "█" * int(overall_pct / 5) + "░" * (20 - int(overall_pct / 5))
    print(f"\n{'─'*60}")
    print(f"  TOTAL PROGRESS [{bar}] {overall_pct:.1f}%")
    print(f"  {total_completed:,} / {grand_total:,} test cases completed")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    check()
