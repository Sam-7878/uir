"""Generate report/tables strictly from the same V2 JSON summaries."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results/llm_security_v2"


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def pct(value: float) -> str: return f"{value * 100:.2f}%"


def main() -> None:
    benchmark, ablation, multi, validation = (load(name) for name in ("benchmark_metrics_summary.json", "ablation_metrics_summary.json", "multi_knockout_summary.json", "results_validation.json"))
    tables = RESULTS / "publication_tables"; tables.mkdir(parents=True, exist_ok=True)
    eligible = benchmark["publication_eligible"] and ablation["publication_eligible"] and multi["publication_eligible"]
    lines = ["# HETE UIR Security Benchmark v2", "", "## Evidence status", "", f"Results validation: **{validation['status']}**.", f"Publication eligible: **{eligible}**.", "", "This benchmark distinguishes Model Compromise Rate (MCR) from End-to-End Attack Success Rate (E2E-ASR). It does not claim human validation, universal security, or prompt-injection immunity."]
    if not eligible:
        lines += ["", "> [!WARNING]", "> This is a harness smoke run, not SCI evidence. It used fewer than 1,600 cases and/or fewer than three live-model runs. The numerical rows below must not be cited as security, utility, ablation, or comparative results."]
    lines += ["", "## Baseline results", "", "| Baseline | MCR | E2E-ASR | FRR | Benign task success |", "|---|---:|---:|---:|---:|"]
    for name, runs in benchmark["summaries"].items():
        metric = runs[0]
        # The report is a pure rendering of the canonical summary; contradictions are fatal.
        assert metric["benign_task_success"]["rate"] == metric["confusion_matrix"]["successful_benign"] / metric["raw_counts"]["benign"]
        assert metric["frr"]["rate"] == metric["confusion_matrix"]["failed_benign"] / metric["raw_counts"]["benign"]
        assert metric["e2e_asr_overall"]["rate"] == metric["confusion_matrix"]["missed_attacks"] / metric["raw_counts"]["attacks"] if metric["raw_counts"]["attacks"] else metric["e2e_asr_overall"]["rate"] == 0.0
        lines.append(f"| {name} | {pct(metric['mcr_overall']['rate'])} ({metric['mcr_overall']['count']} / {metric['mcr_overall']['n']}) | {pct(metric['e2e_asr_overall']['rate'])} ({metric['e2e_asr_overall']['count']} / {metric['e2e_asr_overall']['n']}) | {pct(metric['frr']['rate'])} | {pct(metric['benign_task_success']['rate'])} |")
    lines += ["", "## Single-component ablation", "", "| Knockout | ΔE2E-ASR | ΔMCR | ΔFRR | ΔUtility | Targeted degradation observed |", "|---|---:|---:|---:|---:|---:|"]
    for name, delta in ablation["deltas"].items():
        lines.append(f"| {name} | {pct(delta['delta_e2e_asr'])} | {pct(delta['delta_mcr'])} | {pct(delta['delta_frr'])} | {pct(delta['delta_utility'])} | {delta['targeted_degradation_observed']} |")
    lines += ["", "## Final repair verification questions", "", "1. **Benign utility:** the harness measures actual structured task success, citations, completeness, and FRR; a publication answer awaits the full live Phi-3.5 run.", "2. **MCR vs E2E-ASR:** both are computed by the same independent case-goal oracle, with raw counts and Wilson intervals.", "3. **Remaining non-zero classes:** derived only from the full run's per-class results, never inferred from an attack label.", "4. **Component reduction:** targeted and paired multi-knockout results record deltas; an unchanged component is reported as masked/redundant, not credited.", "5. **Defense-in-depth:** four required multi-knockout pairs are included.", "6. **Security-utility trade-off:** FRR and benign task success are emitted with every configuration.", "7. **KO/EN stability:** language-specific MCR, E2E-ASR, and utility are emitted.", "8. **Repeated-run stability:** the publication gate requires at least three runs with fixed seed/configuration metadata.", "9. **Out-of-scope threats:** training-time, supply-chain, and hardware attacks remain out of scope.", "10. **SCI-safe claims:** only measured live-model results with `publication_eligible: true` may be described as observed benchmark behavior.", "", "## Limitations", "", "- All claims are limited to observed benchmark behavior and the frozen evaluated threat set.", "- Training-time, model-supply-chain, and hardware attacks are out of scope.", "- `not publication eligible` means the run is a smoke test or lacks the required live-model repetitions; it must not be used in an SCI Results section."]
    report = "\n".join(lines) + "\n"
    (ROOT / "docs/evaluation").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs/evaluation/HETE_UIR_SECURITY_BENCHMARK_V2.md").write_text(report, encoding="utf-8")
    (ROOT / "docs/work_reports/001_security_benchmark_repair/HETE_UIR_SECURITY_BENCHMARK_REPAIR_REPORT.md").write_text(report, encoding="utf-8")
    (tables / "baseline_summary.md").write_text(report, encoding="utf-8")


if __name__ == "__main__": main()
