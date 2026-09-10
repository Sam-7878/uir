#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

RESULTS = Path("results/uir_slm")
REQUIRED = {
    "run_manifest.json", "model_manifest.json", "frozen_test_manifest.json",
    "outputs_raw.jsonl", "claims_raw.jsonl", "metric_summary.csv", "model_summary.csv",
    "baseline_comparison.csv", "groundedness_summary.csv", "numeric_summary.csv",
    "adversarial_summary.csv", "generalization_split_summary.csv", "cross_run_variance.csv",
    "cross_seed_variance.csv", "latency_summary.csv", "statistical_tests.csv", "failures.jsonl",
}


def rows(name: str) -> list[dict]:
    return [json.loads(line) for line in (RESULTS / name).read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    missing = sorted(REQUIRED - {path.name for path in RESULTS.iterdir()})
    assert not missing, f"missing required results: {missing}"
    expected = [("frozen_primary.jsonl", 6000, 1000), ("numeric_primary.jsonl", 1200, 200), ("adversarial_primary.jsonl", 1800, 300)]
    checks = {}
    for name, count, per_pipeline in expected:
        data = rows(name); keys = {(row["run_id"], row["case_id"], row["pipeline"], row["seed"]) for row in data}; pipelines = Counter(row["pipeline"] for row in data)
        assert len(data) == len(keys) == count
        assert set(pipelines.values()) == {per_pipeline}
        checks[name] = {"rows": count, "unique_keys": len(keys)}
    repeated = rows("repeated_runs_selected.jsonl")
    for prefix in ("det-repeat", "stochastic-final"):
        selected = {(row["run_id"], row["case_id"], row["pipeline"], row["seed"]) for row in repeated if row["run_id"].startswith(prefix)}
        assert len(selected) == 300, (prefix, len(selected))
    assert len(repeated) == 600
    manifest = json.loads((RESULTS / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["worktree_clean_at_start"] and manifest["status"] == "complete"
    frozen = json.loads((RESULTS / "frozen_test_manifest.json").read_text(encoding="utf-8"))
    assert manifest["frozen_dataset_sha256"] == frozen["dataset_sha256"]
    print(json.dumps({"status": "passed", "checks": checks, "clean_start": True, "frozen_sha256": frozen["dataset_sha256"]}, sort_keys=True))


if __name__ == "__main__": main()
