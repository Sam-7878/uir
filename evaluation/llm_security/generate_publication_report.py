"""Render the final publication report exclusively from validated JSON evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean, pstdev


def load(path: Path) -> dict: return json.loads(path.read_text(encoding="utf-8"))
def pct(value: float) -> str: return f"{100 * value:.2f}%"
def digest(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()


def mean_rate(runs: list[dict], metric: str) -> float: return mean(run[metric]["rate"] for run in runs)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--results", type=Path, required=True); parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    source_names = ["publication_manifest.json", "benchmark_metrics_summary.json", "heldout_metrics_summary.json", "ablation_metrics_summary.json", "heldout_ablation_metrics_summary.json", "multi_knockout_summary.json", "heldout_multi_knockout_summary.json", "statistical_tests.json", "judge_validation.json"]
    data = {name: load(args.results / name) for name in source_names}
    primary = data["heldout_metrics_summary.json"]; ablation = data["heldout_ablation_metrics_summary.json"]
    hete_runs = primary["summaries"]["HETE UIR-v2 Security"]
    mcr = mean_rate(hete_runs, "mcr_overall"); e2e = mean_rate(hete_runs, "e2e_asr_overall")
    utility = mean_rate(hete_runs, "benign_task_success"); frr = mean_rate(hete_runs, "frr")
    containment = (mcr - e2e) / mcr if mcr else None
    per_class = hete_runs[0]["by_attack_class"]
    max_class_e2e = max(item["e2e_asr"]["rate"] for item in per_class.values())
    weakest = [name for name, item in per_class.items() if item["e2e_asr"]["rate"] == max_class_e2e]
    largest = max(
        ablation["deltas"],
        key=lambda name: max(
            ablation["deltas"][name]["targeted_delta_e2e_asr"],
            ablation["deltas"][name]["targeted_delta_mcr"],
        ),
    )
    lines = ["# HETE UIR-v2 Publication Security Benchmark", "", "## Publication gate", "", "This report is generated from the frozen JSON evidence package. Manuscript use is allowed only when strict `results_validation.json` reports publication eligibility.", "", "## Held-out baseline comparison", "", "| Baseline | MCR | E2E-ASR | FRR | Benign utility | Mean latency (ms) |", "|---|---:|---:|---:|---:|---:|"]
    for name, runs in primary["summaries"].items():
        lines.append(f"| {name} | {pct(mean_rate(runs, 'mcr_overall'))} | {pct(mean_rate(runs, 'e2e_asr_overall'))} | {pct(mean_rate(runs, 'frr'))} | {pct(mean_rate(runs, 'benign_task_success'))} | {mean(run['latency_ms']['mean'] for run in runs):.2f} |")
    containment_text = pct(containment) if containment is not None else "not applicable (no HETE model compromises observed)"
    weakest_text = ", ".join(weakest) if max_class_e2e else "none; every held-out attack class was 0.00%"
    largest_delta = ablation["deltas"][largest]
    lines += ["", "## Required final questions", "", f"1. HETE UIR-v2 MCR: **{pct(mcr)}**.", f"2. HETE UIR-v2 E2E-ASR: **{pct(e2e)}**.", f"3. Downstream deterministic-gate containment: **{containment_text}**.", f"4. Retained benign utility: **{pct(utility)}**.", f"5. FRR: **{pct(frr)}**.", f"6. Weakest held-out attack class by E2E-ASR: **{weakest_text}** (maximum {pct(max_class_e2e)} in run 0; all runs remain in JSON).", f"7. Largest measured threat-specific single-knockout effect: **{largest}** (targeted ΔE2E-ASR {pct(largest_delta['targeted_delta_e2e_asr'])}; targeted ΔMCR {pct(largest_delta['targeted_delta_mcr'])}).", "8. Defense-in-depth masking is reported by the four paired knockout configurations in `heldout_multi_knockout_summary.json`."]
    ko = mean(run["by_language"]["KO"]["utility"]["rate"] for run in hete_runs); en = mean(run["by_language"]["EN"]["utility"]["rate"] for run in hete_runs)
    lines += [f"9. KO/EN benign utility: **{pct(ko)} / {pct(en)}**; inferential comparisons must use the raw paired records.", "10. Baseline comparisons and exact McNemar tests are shown above and in `statistical_tests.json`.", f"11. Valid-request mean latency and token totals are recorded per run; held-out run-0 mean is **{hete_runs[0]['latency_ms']['mean']:.2f} ms**."]
    attack_latency = mean(item["latency_ms_mean"] for item in per_class.values()); benign_latency = hete_runs[0]["latency_ms"]["mean"]
    lines += [f"12. Mean attack-class latency is **{attack_latency:.2f} ms** versus overall **{benign_latency:.2f} ms**; early-termination interpretation is limited to class-specific raw records.", f"13. Three-run HETE E2E-ASR spread: mean **{pct(e2e)}**, population SD **{pct(pstdev(run['e2e_asr_overall']['rate'] for run in hete_runs))}**."]
    development = data["benchmark_metrics_summary.json"]["summaries"]["HETE UIR-v2 Security"]
    dev_e2e = mean_rate(development, "e2e_asr_overall")
    judge = data["judge_validation.json"]
    lines += [f"14. Development vs held-out HETE E2E-ASR: **{pct(dev_e2e)} / {pct(e2e)}**.", "15. Residual out-of-scope risks include training-time compromise, model supply-chain compromise, hardware attacks, and threats outside the frozen taxonomy.", "", "## Prompt-only Guardrail appendix", "", "The exact invariant system prompt is defined by `PromptGuardBaseline.HARDENED_SYSTEM_PROMPT`; it is identical across every case and is preserved in the committed source.", "", "## Evidence limitations", "", "- Non-zero residual attack rates are retained and must not be hidden.", "- Infrastructure failures are excluded from security verdicts and independently gate publication.", f"- Judge validation was `{judge['review_type']}` over {judge['reviewed_count']} cases with {pct(judge['agreement_rate'])} agreement. It was Codex AI-assisted evidence review; no human reviewer is claimed."]
    report = "\n".join(lines) + "\n"
    evaluation_path = args.repo_root / "docs/evaluation/HETE_UIR_SECURITY_BENCHMARK_V2_FINAL.md"
    work_path = args.repo_root / "docs/work_reports/HETE_UIR_PUBLICATION_BENCHMARK_FINAL_REPORT.md"
    evaluation_path.parent.mkdir(parents=True, exist_ok=True); work_path.parent.mkdir(parents=True, exist_ok=True)
    evaluation_path.write_text(report, encoding="utf-8"); work_path.write_text(report, encoding="utf-8")
    provenance = {"sources": {name: digest(args.results / name) for name in source_names}, "reports": {str(evaluation_path): digest(evaluation_path), str(work_path): digest(work_path)}}
    (args.results / "report_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(evaluation_path), "heldout_mcr": mcr, "heldout_e2e_asr": e2e}, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
