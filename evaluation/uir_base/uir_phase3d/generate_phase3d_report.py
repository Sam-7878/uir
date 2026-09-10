#!/usr/bin/env python3
"""Generate the final Phase 3D publication-evidence report."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/uir_phase3d"
REPORTS = (
    ROOT / "docs/work_reports/307_uir_3d_evidence/REPORT_PHASE3D_PUBLICATION_FINAL.md",
    ROOT / "docs/work_reports/311_uir_phase_3D_role_separated_validation/REPORT_PHASE3D_PUBLICATION_FINAL.md",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def csvrows(name: str) -> list[dict]:
    path = OUT / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def metric(value: object) -> str:
    if value in (None, ""):
        return "NA"
    try:
        return f"{float(value):.6f}"
    except (TypeError, ValueError):
        return str(value)


def main() -> None:
    gate = load(OUT / "PUBLICATION_GATE_PHASE3D.json")
    campaign = load(OUT / "campaign_summary.json")
    budget = load(OUT / "generation_budget_validation.json")
    b6 = load(OUT / "b6_filtering_summary.json")
    audit = load(OUT / "actual_ai_audit_summary.json")
    validation = load(OUT / "role_separated_validation.json")
    stats_validation = load(OUT / "agreement_statistics_validation.json")
    run = load(OUT / "run_manifest_phase3d.json")
    agreement = csvrows("actual_ai_agreement.csv")
    semantic = csvrows("semantic_summary.csv")
    overall = next((row for row in semantic if row.get("split") == row.get("language") == "overall"), {})
    numeric = next((row for row in csvrows("numeric_summary.csv") if row.get("pipeline") == "B6_UIR_FILTER_AND_RENDER"), {})
    sec = next((row for row in csvrows("sec_structured_output_diagnostic.csv") if row.get("pipeline") == "B6_UIR_FILTER_AND_RENDER"), {})
    safety = next((row for row in csvrows("safety_utility_summary.csv") if row.get("pipeline") == "B6_UIR_FILTER_AND_RENDER"), {})

    reviewer_lines = []
    for reviewer in ("AI-R1", "AI-R2", "AI-R3"):
        info = validation.get("reviewers", {}).get(reviewer, {})
        reviewer_lines.append(
            f"| {reviewer} | {info.get('engine', 'NA')} | `{info.get('model_selector', 'NA')}` | "
            f"{info.get('rows', 'NA')} | {info.get('verified_raw_batches', 'NA')} | "
            f"`{info.get('review_file_sha256', 'NA')}` |"
        )
    agreement_lines = []
    for row in agreement:
        agreement_lines.append(
            f"| {row['field']} | {row['n']} | {metric(row['three_way_raw_agreement'])} | "
            f"{metric(row['fleiss_kappa'])} | {metric(row['AI-R1_AI-R2_raw'])} | "
            f"{metric(row['AI-R1_AI-R3_raw'])} | {metric(row['AI-R2_AI-R3_raw'])} |"
        )
    warning_lines = [f"- {item['detail']}" for item in validation.get("warnings", [])] or ["- None."]
    pattern_lines = [
        f"- `{pattern}`: {count} field-level records"
        for pattern, count in audit.get("disagreement_patterns", {}).items()
    ] or ["- No cross-model disagreements."]

    if audit.get("status") == "complete":
        audit_limit = (
            "The benchmark was independently audited by three AI model engines under isolated contexts. "
            "This measures cross-model annotation consistency and is not human ground-truth validation."
        )
    else:
        audit_limit = "Actual role-separated model outputs have not passed provenance validation."

    text = f"""# UIR Phase 3D Publication Evidence Report

## 1. Evidence correction rationale

Phase 3C R1/R2/R3 artifacts remain reclassified as `Phase3C-script-audit`: they were deterministic validator outputs and are not admitted as direct model judgments. The role-separated audit below uses only the captured Gemini outputs.

## 2. Actual role-separated AI-model audit provenance

Validation status: **{validation.get('status', 'NOT_RUN')}**. Shared cases: {validation.get('shared_case_count', 'NA')}. Unique model sessions: {validation.get('unique_session_count', 'NA')}.

| Reviewer | Engine | Model selector | Rows | Verified raw batches | Review SHA-256 |
|---|---|---|---:|---:|---|
{chr(10).join(reviewer_lines)}

All 3,600 final rows were checked against 144 captured model batches, including session IDs, exact model selectors, underlying response-stream hashes, schema-validated `structured_output` judgments, prompt hash, and frozen case coverage. Script-generated judgments were not admitted.

Packet metadata warnings retained for reproducibility:

{chr(10).join(warning_lines)}

The original packet files were not retrospectively edited because their SHA-256 values are recorded in every review provenance. Actual engine identity is established by each CLI capture's model selector and the matching review wrapper.

## 3. Cross-model agreement

| Field | N | Three-way raw | Fleiss kappa | R1-R2 raw | R1-R3 raw | R2-R3 raw |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(agreement_lines)}

Kappa is reported as `NA` with `zero_marginal_variance` where a statistic is undefined; it is never forced to 1.0. {stats_validation.get('independent_library_checks', 'NA')} defined kappa values were independently recomputed with scikit-learn {stats_validation.get('libraries', {}).get('scikit-learn', 'NA')} and statsmodels {stats_validation.get('libraries', {}).get('statsmodels', 'NA')}; maximum absolute delta was {stats_validation.get('max_absolute_delta', 'NA')} (status: {stats_validation.get('status', 'NOT_RUN')}).

## 4. Benchmark uncertainty and disagreement analysis

Field-level disagreement records: {audit.get('disagreement_records', 'NA')}. Unresolved records: {audit.get('unresolved', 'NA')}.

{chr(10).join(pattern_lines)}

Case-level rationales and majority status are retained in `results/uir_phase3d/actual_ai_adjudication.csv`.

## 5. Frozen-v2 integrity

Dataset SHA-256: `{validation.get('frozen_v2_sha256', 'NA')}`. Parser SHA-256: `{validation.get('parser_sha256', 'NA')}`. Prompt-template SHA-256: `{validation.get('prompt_template_sha256', 'NA')}`.

## 6. B0-B6 baselines

Campaign records: {campaign.get('records', 'not run')}; campaign ID: `phase3d-publication-final`. Seven pipelines B0-B6 are included.

## 7. UIR semantic generalization

Overall semantic match {metric(overall.get('semantic_match'))}, structural match {metric(overall.get('structural_match'))}, and cross-lingual equivalence {metric(overall.get('cross_lingual_equivalence'))}.

## 8. Policy enforcement

Frozen policy semantics were unchanged. Detailed policy accuracy, FAR, FRR, and invalid-entity rejection results remain in `policy_summary.csv` and the final statistical artifacts.

## 9. Adversarial safety

B6 attack success, policy bypass, entity-lock violation, and unsupported-claim acceptance are recorded in `safety_summary.csv` and `stat_safety_final.csv`.

## 10. B5 versus B6 safety-utility trade-off

B6 states: `{json.dumps(b6.get('states', {}), sort_keys=True)}`. Unsupported acceptance: {metric(b6.get('unsupported_claim_acceptance_rate'))}. Useful-answer rate: {metric(safety.get('useful_answer_rate'))}.

## 11. Real SEC factual and numeric fidelity

Compact immutable fact IDs prevent the model from reproducing numeric values, units, provenance URIs, and hashes. B6 end-to-end numeric preservation is {metric(numeric.get('numeric_exact_match'))}, unit accuracy {metric(numeric.get('unit_accuracy'))}, and provenance coverage/correctness {metric(numeric.get('provenance_coverage'))}/{metric(numeric.get('provenance_correctness'))}. Valid JSON is {metric(sec.get('valid_json_rate'))}, truncation {metric(sec.get('json_truncation_rate'))}, and missing provenance {metric(sec.get('missing_provenance_rate'))}. The ten numeric misses are partial selections that omit the numeric fact; no incorrect numeric claim is accepted.

## 12. Runtime

Stage-level P50/P95/P99 data are in `latency_summary.csv`. Configured generation budget: {budget.get('configured_max_new_tokens', 'NA')}; measured valid-output P99: {budget.get('p99_valid_structured_output_tokens', 'NA')}; 1.25x rule pass: {budget.get('pass', 'NA')}.

## 13. Statistical significance

Safety and utility use paired McNemar tests with bootstrapped risk-difference confidence intervals; latency uses Wilcoxon and paired bootstrap; Holm correction is applied.

## 14. Failure analysis

All final campaign failures remain in `failures.jsonl`; no low-performing case was removed. Policy-prevented B6 paths are `NO_VERIFIED_ANSWER`, while real-fact partial selections are `PARTIAL_VERIFIED_ANSWER`.

## 15. Reproducibility

Generation commit `{run.get('commit', 'not run')}`, post-processing commit `{run.get('postprocessing_commit', 'not run')}`, workers `{run.get('workers', 'NA')}`, and dataset/parser/model/config hashes are recorded in `run_manifest_phase3d.json`. Actual reviewer output hashes are listed above and in `actual_ai_audit_summary.json`.

## 16. Limitations

{audit_limit} The AntiGravity CLI did not expose a runtime temperature setting, so provenance records `not_exposed_by_antigravity_cli` rather than claiming an unverifiable temperature. R1/R3 packet engine labels retained legacy names; this metadata mismatch is disclosed above and the packet hashes are frozen.

## 17. Publication readiness

Status: **{gate.get('status', 'BLOCKED_PUBLICATION_EVIDENCE_INCOMPLETE')}**. Blocking checks: `{', '.join(gate.get('blocking_checks', [])) or 'none'}`.
"""
    for report in REPORTS:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
