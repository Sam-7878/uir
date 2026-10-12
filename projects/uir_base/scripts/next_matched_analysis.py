"""Paired development statistics and measured timing, never historical speedup."""
from collections import Counter, defaultdict
import json
import numpy as np
from scipy.stats import binomtest
from projects.uir_base.scripts import revision_audit as a
from projects.uir_base.scripts.next_release import csv_rows


def paired(rows, families, *, seed=20261012, repetitions=10000):
    groups = defaultdict(dict)
    for row in rows:
        if row["commit_eligible"]:
            if row["case_id"] in groups[row["pipeline"]]:
                raise ValueError("Duplicate paired case")
            groups[row["pipeline"]][row["case_id"]] = row
    target = groups["DETERMINISTIC_TRUSTED_FIXTURE"]
    result = []
    for condition, group in sorted(groups.items()):
        if condition == "DETERMINISTIC_TRUSTED_FIXTURE":
            continue
        if group.keys() != target.keys():
            raise ValueError("Unpaired cohort")
        for metric in ("complete", "safe_claim_answered"):
            counts = Counter(); clusters = defaultdict(list)
            for cid in sorted(target):
                x, y = bool(target[cid][metric]), bool(group[cid][metric])
                counts[x, y] += 1
                if cid not in families:
                    raise ValueError("Missing source-family lineage")
                clusters[families[cid]].append(int(y) - int(x))
            values = np.array([(sum(v), len(v)) for v in clusters.values()], dtype=float)
            rng = np.random.default_rng(seed)
            draws = rng.integers(0, len(values), size=(repetitions, len(values)))
            sampled = values[draws].sum(axis=1)
            ci = np.quantile(sampled[:, 0] / sampled[:, 1], [.025, .975])
            n01, n10 = counts[False, True], counts[True, False]
            p = float(binomtest(min(n01, n10), n01 + n10).pvalue) if n01 + n10 else 1.
            result.append({"condition": condition, "reference": "DETERMINISTIC_TRUSTED_FIXTURE", "metric": metric,
                           "N": len(target), "N_families": len(clusters), "n01": n01, "n10": n10,
                           "risk_difference": (n01 - n10) / len(target), "ci_low": float(ci[0]), "ci_high": float(ci[1]),
                           "p_exact": p, "p_holm": None, "seed": seed, "bootstrap_repetitions": repetitions,
                           "family": "six_exploratory_matched_development_comparisons", "interpretation": "not equivalence; independence caveat applies"})
    running = 0.
    for rank, row in enumerate(sorted(result, key=lambda r: r["p_exact"])):
        running = max(running, min(1., row["p_exact"] * (len(result) - rank)))
        row["p_holm"] = running
    return result


def analyze(root):
    out = root / "fresh_matched"
    protocol = json.loads((root / "fresh_matched_protocol.json").read_text())
    rows = csv_rows(out / "matched_case_results.csv")
    for row in rows:
        for field in ("commit_eligible", "complete", "safe_claim_answered"):
            if row[field] not in {"True", "False"}:
                raise ValueError("Invalid boolean label")
            row[field] = row[field] == "True"
    families = {r["case_id"]: r["source_family_id"] for r in csv_rows(root / "source_family_manifest.csv")}
    spec = protocol["statistics"]
    a.write_csv(out / "matched_paired_statistics.csv", paired(rows, families, seed=spec["seed"], repetitions=spec["bootstrap_repetitions"]))
    captures = a.read(out / "raw_requests_responses.jsonl")
    timings = []
    for name, predicate in (("first_load_inclusive", lambda r: r["model_invoked"] and r["cold_load_inclusive"] is True),
                            ("warm_model_requests", lambda r: r["model_invoked"] and r["cold_load_inclusive"] is False),
                            ("early_rejection", lambda r: not r["model_invoked"]),
                            ("deterministic_template", lambda r: True)):
        values = [r["gate_duration_ms"] + r["template_duration_ms"] if name == "deterministic_template"
                  else r["request_duration_ms"] for r in captures if predicate(r)]
        timings.append({"scope": name, "N": len(values), "p50_ms": float(np.quantile(values, .5)) if values else None,
                        "p95_ms": float(np.quantile(values, .95)) if values else None,
                        "p99_ms": float(np.quantile(values, .99)) if values else None,
                        "unit": "one measured sequential request/stage", "repetitions_per_request": 1,
                        "claim": "descriptive only; no transformer acceleration, repeated-latency or historical batch comparison"})
    a.write_csv(out / "request_latency_summary.csv", timings)
