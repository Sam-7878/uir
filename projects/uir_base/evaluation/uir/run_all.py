#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--seed", type=int, default=20260807); args = parser.parse_args(); py = sys.executable
    commands = [
        [py, "projects/uir_base/evaluation/uir/generate_dataset.py", "--seed", str(args.seed), "--out", "projects/uir_base/evaluation/uir/fixtures/generated"],
        [py, "projects/uir_base/evaluation/uir/run_uir_benchmark.py", "--dataset", "projects/uir_base/evaluation/uir/fixtures/generated", "--out", "projects/uir_base/results/uir"],
        [py, "projects/uir_base/evaluation/uir/run_ablation.py", "--dataset", "projects/uir_base/evaluation/uir/fixtures/generated", "--out", "projects/uir_base/results/uir", "--seed", str(args.seed)],
        [py, "projects/uir_base/evaluation/uir/generate_uir_report.py", "--input", "projects/uir_base/results/uir", "--dataset", "projects/uir_base/evaluation/uir/fixtures/generated/dataset.jsonl", "--output", "projects/uir_base/results/uir/reports/REPORT.md"],
    ]
    for command in commands: subprocess.run(command, check=True)


if __name__ == "__main__": main()
