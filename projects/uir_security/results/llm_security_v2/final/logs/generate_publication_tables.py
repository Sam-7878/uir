from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from statistics import mean


RESULTS = Path(__file__).resolve().parents[1]
TABLES = RESULTS / "publication_tables"


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean_rate(runs: list[dict], key: str) -> float:
    return mean(float(run[key]["rate"]) for run in runs)


def write_csv(name: str, fieldnames: list[str], rows: list[dict]) -> None:
    path = TABLES / name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    baseline = load("heldout_metrics_summary.json")
    ablation = load("heldout_ablation_metrics_summary.json")
    multi = load("heldout_multi_knockout_summary.json")
    stats = load("statistical_tests.json")

    baseline_rows = []
    for name, runs in baseline["summaries"].items():
        baseline_rows.append(
            {
                "baseline": name,
                "runs": len(runs),
                "mcr_mean": mean_rate(runs, "mcr_overall"),
                "e2e_asr_mean": mean_rate(runs, "e2e_asr_overall"),
                "frr_mean": mean_rate(runs, "frr"),
                "benign_utility_mean": mean_rate(runs, "benign_task_success"),
                "inference_failures": sum(int(run["inference_failures"]["count"]) for run in runs),
                "latency_ms_mean": mean(float(run["latency_ms"]["mean"]) for run in runs),
            }
        )
    write_csv(
        "heldout_baseline_summary.csv",
        list(baseline_rows[0]),
        baseline_rows,
    )

    ablation_rows = []
    for name, delta in ablation["deltas"].items():
        ablation_rows.append(
            {
                "knockout": name,
                "delta_e2e_asr": delta["delta_e2e_asr"],
                "delta_mcr": delta["delta_mcr"],
                "delta_frr": delta["delta_frr"],
                "delta_utility": delta["delta_utility"],
                "targeted_delta_e2e_asr": delta["targeted_delta_e2e_asr"],
                "targeted_delta_mcr": delta["targeted_delta_mcr"],
                "targeted_degradation_observed": delta["targeted_degradation_observed"],
            }
        )
    write_csv("heldout_ablation_summary.csv", list(ablation_rows[0]), ablation_rows)

    multi_rows = []
    for name, runs in multi["results"].items():
        multi_rows.append(
            {
                "paired_knockout": name,
                "runs": len(runs),
                "mcr_mean": mean_rate(runs, "mcr_overall"),
                "e2e_asr_mean": mean_rate(runs, "e2e_asr_overall"),
                "frr_mean": mean_rate(runs, "frr"),
                "benign_utility_mean": mean_rate(runs, "benign_task_success"),
                "inference_failures": sum(int(run["inference_failures"]["count"]) for run in runs),
            }
        )
    write_csv("heldout_multi_knockout_summary.csv", list(multi_rows[0]), multi_rows)

    stat_rows = []
    for comparison, runs in stats["comparisons"].items():
        for run_index, result in enumerate(runs):
            stat_rows.append(
                {
                    "comparison": comparison,
                    "run": run_index,
                    "n": result["n"],
                    "baseline_only_successes": result["baseline_only_successes"],
                    "full_only_successes": result["full_only_successes"],
                    "mcnemar_exact_p": result["mcnemar_exact_p"],
                    "baseline_risk": result["baseline_risk"],
                    "comparison_risk": result["comparison_risk"],
                    "absolute_risk_reduction": result["absolute_risk_reduction"],
                    "relative_risk": result["relative_risk"],
                }
            )
    write_csv("heldout_mcnemar_comparisons.csv", list(stat_rows[0]), stat_rows)

    source_names = [
        "heldout_metrics_summary.json",
        "heldout_ablation_metrics_summary.json",
        "heldout_multi_knockout_summary.json",
        "statistical_tests.json",
    ]
    table_names = sorted(path.name for path in TABLES.glob("*.csv"))
    provenance = {
        "sources": {name: digest(RESULTS / name) for name in source_names},
        "tables": {name: digest(TABLES / name) for name in table_names},
    }
    (TABLES / "table_provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    (TABLES / "README.md").write_text(
        "# Publication tables\n\n"
        "These tables are deterministic renderings of the frozen held-out JSON summaries. "
        "Use `table_provenance.json` to verify every source and table SHA-256 digest.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
