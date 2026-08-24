"""Master Orchestrator: Run Benchmark, Ablation, and Generate Publication Reports."""
from __future__ import annotations

import sys
from pathlib import Path

from .generate_security_report import generate_reports
from .run_ablation_study import run_ablation_experiments
from .run_security_benchmark import run_full_security_benchmark


def main() -> None:
    print("=================================================================")
    print("  HETE UIR-v2 Zero-Trust Security Benchmark Suite Execution")
    print("=================================================================\n")

    # Step 1: Run 5 Baselines Evaluation
    print(">>> STEP 1: Running 5 Baselines on 1,600 Benchmark Cases...")
    run_full_security_benchmark()

    # Step 2: Run 7 Component Ablation Study
    print("\n>>> STEP 2: Running 7 Component Ablation Study...")
    run_ablation_experiments()

    # Step 3: Generate Publication Reports and Tables
    print("\n>>> STEP 3: Generating Publication Reports and CSV Tables...")
    generate_reports()

    print("\n=================================================================")
    print("  ALL BENCHMARKS, ABLATIONS, AND REPORTS COMPLETED SUCCESSFULLY!")
    print("=================================================================")


if __name__ == "__main__":
    main()
