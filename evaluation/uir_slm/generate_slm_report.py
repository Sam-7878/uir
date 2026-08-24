#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def table(rows: list[dict], fields: list[str]) -> str:
    if not rows:
        return "_No records._"
    header = "| " + " | ".join(fields) + " |"
    rule = "|" + "|".join("---" for _ in fields) + "|"
    body = ["| " + " | ".join(str(row.get(field, "")) for field in fields) + " |" for row in rows]
    return "\n".join([header, rule, *body])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results/uir_slm"))
    parser.add_argument("--uir-records", type=Path, default=Path("results/uir_slm/frozen_uir_core.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("docs/work_reports/301_uir_phase_2/REPORT_SLM.md"))
    args = parser.parse_args()
    manifest = json.loads((args.results / "run_manifest.json").read_text(encoding="utf-8"))
    frozen = json.loads((args.results / "frozen_test_manifest.json").read_text(encoding="utf-8"))
    model = json.loads((args.results / "model_manifest.json").read_text(encoding="utf-8"))
    core = [json.loads(line) for line in args.uir_records.read_text(encoding="utf-8").splitlines() if line]
    frozen_rows = [json.loads(line) for line in Path("evaluation/uir_external/frozen_test_v1.jsonl").read_text(encoding="utf-8").splitlines() if line]
    failures = [json.loads(line) for line in (args.results / "failures.jsonl").read_text(encoding="utf-8").splitlines() if line]
    baseline = csv_rows(args.results / "baseline_comparison.csv")
    generalization = csv_rows(args.results / "generalization_split_summary.csv")
    numeric = csv_rows(args.results / "numeric_summary.csv")
    adversarial = csv_rows(args.results / "adversarial_summary.csv")
    variance = csv_rows(args.results / "cross_seed_variance.csv")
    statistics = csv_rows(args.results / "statistical_tests.csv")
    latency = csv_rows(args.results / "latency_summary.csv")
    core_latency = csv_rows(args.results / "core_latency_summary.csv")
    expected_by_id = {row["case_id"]: row for row in frozen_rows}; pairs = {}
    for row in core:
        pair_id = expected_by_id[row["case_id"]].get("pair_id")
        if pair_id: pairs.setdefault(pair_id, []).append(row)
    cle = sum(bool(len(rows) == 2 and rows[0].get("semantic_digest") and rows[0].get("semantic_digest") == rows[1].get("semantic_digest")) for rows in pairs.values()) / len(pairs)
    expected_reject = [row for row in core if row["expected_outcome"] == "REJECT"]; expected_commit = [row for row in core if row["expected_outcome"] == "COMMIT"]
    core_summary = {"cases": len(core), "structural_match": sum(row["exact_structural_match"] for row in core) / len(core), "semantic_match": sum(row["semantic_match"] for row in core) / len(core), "cle": cle, "policy_accuracy": sum(row["expected_policy_decision"] == row["actual_policy_decision"] for row in core) / len(core), "far": sum(row["actual_outcome"] == "COMMIT" for row in expected_reject) / len(expected_reject), "frr": sum(row["actual_outcome"] != "COMMIT" for row in expected_commit) / len(expected_commit), "outcome_accuracy": sum(row["correct"] for row in core) / len(core)}
    by_pipeline = {row["pipeline"]: row for row in baseline}; b5 = by_pipeline["B5_FULL_UIR_OUTPUT_VALIDATION"]; b0 = by_pipeline["B0_DIRECT_SLM"]
    failure_counts = Counter(row["error_type"] for row in failures)
    sections = [
        "# Phase UIR-2 SCI Evaluation Report",
        f"## 1. Summary\n\nA frozen external test, real SEC fact registry, real local Phi-3.5 renderer, B0–B5 baselines, groundedness, numeric, adversarial, generalization, robustness, statistics, and runtime evidence were evaluated without changing the frozen set after hashing. B5 reduced accepted unsupported-claim rate from {float(b0['unsupported_claim_acceptance_rate']):.3f} (B0) to {float(b5['unsupported_claim_acceptance_rate']):.3f}, but its outcome accuracy was only {float(b5['outcome_accuracy']):.3f} and claim recall {float(b5['claim_recall']):.6f}. The result supports a safety-enforcement claim, not a general utility-superiority claim.",
        f"## 2. Clean Baseline Commit\n\nSource commit: `{manifest['source_commit']}`. Worktree clean at recorded run start: `{manifest['worktree_clean_at_start']}`.",
        f"## 3. Frozen Test Dataset and Hash\n\nCases: {frozen['case_count']}; SHA-256: `{frozen['dataset_sha256']}`; human review status: `{frozen.get('human_review_status', 'not_recorded')}`.",
        f"## 4. Local SLM Configuration\n\nConfigured model: `{model['configured_model']}`. The complete Ollama model response and configuration digest are preserved in `model_manifest.json`.",
        "## 5. Real/Frozen Fact Registry\n\nThe registry is a hashed snapshot derived from the official SEC XBRL Companyfacts API. Evaluation reads only the frozen JSONL snapshot.",
        "## 6. Baseline Pipelines B0–B5\n\n" + table(baseline, ["pipeline", "cases", "claim_precision", "claim_recall", "unsupported_claim_rate", "unsupported_claim_acceptance_rate", "outcome_accuracy"]),
        "## 7. Generalization Splits\n\n" + table(generalization, ["split", "language", "cases", "semantic_match", "policy_accuracy", "outcome_accuracy"]),
        "## 8. Claim-Level Metrics\n\nClaims are normalized into entity, attribute, numeric, relation, temporal, and provenance dimensions and matched exactly against frozen verified claims.",
        "## 9. Numeric Fidelity\n\n" + table(numeric, ["pipeline", "numeric_type", "cases", "numeric_exact_match", "unit_accuracy", "sign_accuracy", "relative_change_accuracy"]),
        "## 10. Adversarial Results\n\n" + table(adversarial, ["pipeline", "cases", "attack_success_rate", "policy_bypass_rate", "unsupported_claim_acceptance_rate", "renderer_invocation_on_reject_rate"]),
        "## 11. Cross-Seed Results\n\n" + table(variance, ["pipeline", "metric", "runs", "mean", "variance", "minimum", "maximum"]),
        "## 12. Statistical Tests\n\n" + table(statistics, ["comparison", "metric", "discordant", "p_value", "risk_difference", "mean_delta", "ci95_low", "ci95_high"]),
        "## 13. Runtime Results\n\n" + table(latency, ["pipeline", "cases", "mean_us", "p50_us", "p95_us", "p99_us", "prompt_eval_mean_us", "generation_mean_us", "validator_mean_us"]) + "\n\n### Deterministic Core Stages\n\n" + table(core_latency, ["stage", "cases", "mean_us", "p50_us", "p95_us", "p99_us"]),
        "## 14. Failures / Error Taxonomy\n\n" + table([{"error_type": key, "count": value} for key, value in sorted(failure_counts.items())], ["error_type", "count"]),
        "## 15. Generated Artifacts\n\nAll raw outputs, normalized claims, CSV summaries, manifests, and failure records are under `results/uir_slm/`.",
        "## 16. Reproduction Commands\n\n```bash\nsource ../.venv/bin/activate\ncargo test --workspace --all-features\npython evaluation/uir_external/validate_frozen_set.py\npython evaluation/uir_slm/run_slm_campaign.py --help\npython evaluation/uir_slm/aggregate_results.py --help\n```",
        "## 17. Limitations\n\nThe frozen set was programmatically curated but not manually reviewed, only one local SLM and one host were evaluated in P0, and SEC values reflect the snapshot date rather than a timeless ground truth. Two preliminary stochastic wrappers were invalidated after shell interpolation/config-path defects; their rows were excluded by run-id allowlisting, and `repeated_runs_selected.jsonl` contains only the 5 deterministic and 5 corrected stochastic runs used in variance tables.",
        "## 18. Recommended Paper Claims\n\nThe strongest supported claim is that post-generation exact claim validation prevents acceptance of unsupported claims and deterministic UIR/policy checks prevent invalid-entity and policy-attack renderer invocation. The data does not support claiming overall task superiority: frozen semantic coverage, claim recall, and B5 outcome accuracy are low. Claims must remain limited to this model, frozen data, host, and confidence tests; do not generalize Phi-3.5 results to all SLMs or describe prompt constraints as enforcement.",
        "## Core UIR Snapshot\n\n" + table([core_summary], list(core_summary)),
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n\n".join(sections) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
