#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--seed", type=int, default=20260807); args = parser.parse_args(); py = sys.executable
    commands = [
        [py, "evaluation/uir/generate_dataset.py", "--seed", str(args.seed), "--out", "evaluation/uir/fixtures/generated"],
        [py, "evaluation/uir/run_uir_benchmark.py", "--dataset", "evaluation/uir/fixtures/generated", "--out", "results/uir"],
        [py, "evaluation/uir/run_ablation.py", "--dataset", "evaluation/uir/fixtures/generated", "--out", "results/uir", "--seed", str(args.seed)],
        [py, "evaluation/uir/generate_uir_report.py", "--input", "results/uir", "--dataset", "evaluation/uir/fixtures/generated/dataset.jsonl", "--output", "docs/work_reports/300_uir/REPORT.md"],
    ]
    for command in commands: subprocess.run(command, check=True)


if __name__ == "__main__": main()
