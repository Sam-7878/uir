"""R11 preregistered paired-family analysis and descriptive measured latency."""
import csv
import json
import numpy as np
from .common import OUT, csvfile, load, read, write


def run():
    protocol = load(OUT / "repr_ablation_protocol_v1.json")
    with (OUT / "dev_matched_results.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    conditions = protocol["conditions"]
    paired = {(r["condition"], r["case_id"]): r for r in rows}
    first = [r for r in rows if r["condition"] == conditions[0]]
    if len(paired) != len(rows) or len(first) * 2 != len(rows): raise ValueError("BROKEN_PAIRED_COHORT")
    families = sorted({r["family"] for r in first})
    values = {f: np.array([int(r["joint_conformance"] == "True") - int(paired[conditions[1], r["case_id"]]["joint_conformance"] == "True")
                         for r in first if r["family"] == f]) for f in families}
    rng = np.random.default_rng(protocol["seed"])
    differences = []
    for _ in range(10000):
        sampled = rng.choice(families, size=len(families), replace=True)
        differences.append(float(np.concatenate([values[f] for f in sampled]).mean()))
    ci = np.quantile(differences, [0.025, 0.975])
    observed = float(np.concatenate(list(values.values())).mean())
    csvfile(OUT / "cluster_bootstrap_results.csv", [{"comparison": "UIR_minus_equivalent_specialized", "endpoint": "joint_conformance",
            "N_cases": len(first), "N_families": len(families), "difference": observed, "ci_low": ci[0], "ci_high": ci[1],
            "seed": protocol["seed"], "bootstrap_reps": 10000, "primary_comparison_family_N": 1,
            "interpretation": "synthetic conformance difference, not equivalence proof/generalization or causal accuracy improvement"}])
    latencies = read(OUT / "latency_instrumentation.jsonl")
    summaries = []
    for condition in conditions:
        for kind in ("initial", "warm_guard_only"):
            values = [r["duration_ms"] for r in latencies if r["condition"] == condition and (r["repetition"] == 0 if kind == "initial" else r["repetition"] > 0)]
            summaries.append({"condition": condition, "kind": kind, "N_measurements": len(values), "p50_ms": np.quantile(values, .5),
                              "p95_ms": np.quantile(values, .95), "p99_ms": np.quantile(values, .99),
                              "inference_calls": 0, "scope": "initial includes frontend plus two backend checks; warm only common guard; imports excluded; neither is GPU cold-start"})
    csvfile(OUT / "latency_summary_vNext.csv", summaries)
    write(OUT / "statistical_limits.json", {"generic_speed_advantage_claimed": False, "unknown_source_dependencies": True,
          "family_mean_difference": observed, "N_repeated_warm_guard_calls_per_compilable_request": 5,
          "model_latency": "new renderer call-level captures descriptive once per condition; no transformer acceleration claim"})
    print(observed, ci.tolist())


if __name__ == "__main__":
    run()
