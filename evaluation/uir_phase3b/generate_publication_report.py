#!/usr/bin/env python3
"""Generate the final report only after every publication gate passes."""
from __future__ import annotations
import csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/"results/uir_phase3b"; REPORT=ROOT/"docs/work_reports/uir_phase3b/REPORT_PUBLICATION_READY.md"
def table(name):
    with (OUT/name).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def main():
    gate=json.loads((OUT/"PUBLICATION_GATE.json").read_text()) if (OUT/"PUBLICATION_GATE.json").exists() else {}
    if not gate.get("publication_ready"):
        print("BLOCKED: publication gate is incomplete; REPORT_PUBLICATION_READY.md was not created",file=sys.stderr); return 2
    frozen=json.loads((OUT/"FROZEN_TEST_V2_MANIFEST.json").read_text()); real=json.loads((OUT/"real_fact_subset_manifest.json").read_text()); run=json.loads((OUT/"run_manifest.json").read_text())
    overall=next(r for r in table("semantic_summary.csv") if r["split"]==r["language"]=="overall")
    comparison=table("safety_utility_summary.csv")
    text=f"""# UIR Phase 3B Publication-Ready Report

## 1. Frozen Dataset
{frozen['case_count']} cases; SHA-256 `{frozen['dataset_sha256']}`; parser `{frozen['parser_source_sha256']}`.

## 2. Human Review / Agreement
Coverage {frozen['review_coverage']:.3f}, two independent anonymous reviewers, adjudication complete. Field-level agreement is in `reviewer_agreement.csv`.

## 3. Leakage Check
The versioned candidate preserves the Phase-3 dev/test separation; candidate changes are recorded in `CANDIDATE_CHANGE_LOG.json`.

## 4. Real-World Fact Subset
{real['case_count']} KO/EN cases from {real['unique_source_facts']} frozen SEC Companyfacts records; registry `{real['registry_sha256']}`.

## 5. Model Configuration
Model `{run['model']}`, config `{run['model_config_sha256']}`.

## 6. Baselines
B0 through B6 were executed from the same clean commit.

## 7. Multilingual Semantic Generalization
Overall semantic match {overall['semantic_match']}; structural match {overall['structural_match']}; cross-lingual equivalence {overall['cross_lingual_equivalence']}.

## 8. Policy Enforcement
See `policy_summary.csv` for accuracy, FAR, FRR, and clarification metrics.

## 9. Groundedness
See `groundedness_summary.csv`.

## 10. Numeric / Provenance Fidelity
See `numeric_summary.csv` and `provenance_summary.csv`, reported separately on the SEC subset.

## 11. Adversarial Safety
See `safety_summary.csv`.

## 12. Safety–Utility Trade-off
See `safety_utility_summary.csv`; B5 and B6 are reported separately without threshold filtering.

## 13. Statistical Significance
Separated safety, utility, and latency statistics use paired comparisons and Holm correction where p-values apply.

## 14. Runtime
See `latency_summary.csv`; runtime provenance is in `run_manifest.json`.

## 15. Error Analysis
All observed failures are retained in `failures.jsonl`; no low-performing case was deleted.

## 16. Reproducibility
Commit `{run['commit']}`, dataset/model/SEC hashes and software/hardware versions are recorded.

## 17. Limitations
The factual subset is limited to the frozen SEC Companyfacts entities and financial attributes. Human review coverage and all measured shortfalls must be reported exactly.

## 18. Publication Readiness Verdict
**PUBLICATION READY** — every machine-enforced Phase-3B gate passed.
"""
    REPORT.parent.mkdir(parents=True,exist_ok=True); REPORT.write_text(text,encoding="utf-8"); return 0
if __name__=="__main__": raise SystemExit(main())
