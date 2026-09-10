#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def read_jsonl(paths: list[Path]) -> list[dict]:
    return [json.loads(line) for path in paths for line in path.read_text(encoding="utf-8").splitlines() if line]


def mean(values) -> float:
    items = list(values); return sum(items) / len(items) if items else 0.0


def population_variance(values: list[float]) -> float:
    average = mean(values); return mean((value - average) ** 2 for value in values)


def rate(group: list[dict], key: str) -> float:
    if key == "validator_rejection_rate":
        return sum(row["output_validation"] == "rejected" for row in group) / len(group)
    if key == "latency_us":
        return mean(row["latency"]["pipeline_total_us"] for row in group)
    return mean(row["metrics"][key] for row in group)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", nargs="+", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("results/uir_slm"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(args.raw)
    metrics = ["claim_precision", "unsupported_claim_rate", "latency_us", "validator_rejection_rate"]
    for mode, filename in (("det-repeat", "cross_run_variance.csv"), ("stochastic-final", "cross_seed_variance.csv")):
        selected = [row for row in rows if row["run_id"].startswith(mode)]
        grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for row in selected:
            grouped[(row["pipeline"], row["run_id"])].append(row)
        output = []
        for pipeline in sorted({key[0] for key in grouped}):
            for metric in metrics:
                values = [rate(group, metric) for (name, _), group in grouped.items() if name == pipeline]
                output.append({"pipeline": pipeline, "metric": metric, "runs": len(values), "mean": mean(values), "variance": population_variance(values), "minimum": min(values, default=0.0), "maximum": max(values, default=0.0)})
        with (args.out / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["pipeline", "metric", "runs", "mean", "variance", "minimum", "maximum"])
            writer.writeheader(); writer.writerows(output)


if __name__ == "__main__":
    main()
