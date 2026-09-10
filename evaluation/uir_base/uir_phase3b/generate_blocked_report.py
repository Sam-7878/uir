#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/"results/uir_phase3b"; REPORT=ROOT/"docs/work_reports/uir_phase3b/REPORT_PHASE3B_BLOCKED.md"
def main():
    gate=json.loads((OUT/"PUBLICATION_GATE.json").read_text()); real=json.loads((OUT/"real_fact_subset_manifest.json").read_text())
    text=f"""# UIR Phase 3B Status Report

## Outcome

Publication freeze automation is implemented, but final publication evidence is correctly blocked.

## Completed

- Parser implementation remains frozen; Phase-3B changed evaluation instrumentation only.
- Candidate v2.0 preserves 1,200 cases and records pre-review pairing/policy-text corrections in an audit log.
- Independent R1/R2 sheets use only `1`, `0`, or `NA`; no judgments are prefilled.
- Field-level raw agreement and Cohen's kappa, adjudication, correction audit, dataset hashing, and freeze gates are implemented.
- Real SEC subset: {real['case_count']} cases, KO/EN 100 each, hash `{real['dataset_sha256']}`.
- B0--B6 runner, B6 FILTER_AND_RENDER, final metrics/statistics, clean-run provenance, and publication report gate are implemented.

## Blocking checks

{chr(10).join('- '+x for x in gate['blocking_checks'])}

## Required human action

Two independent reviewers must complete the review sheets without seeing each other's judgments. Disagreements and agreed-invalid ground truth fields must then be adjudicated and committed. Only after that may `review_and_freeze.py --freeze` and `run_publication_campaign.py` run.

## Integrity statement

No reviewer values, agreement scores, frozen-v2 metrics, or final SLM results were fabricated. `REPORT_PUBLICATION_READY.md` is not generated while any gate is incomplete.
"""
    REPORT.parent.mkdir(parents=True,exist_ok=True); REPORT.write_text(text,encoding="utf-8")
if __name__=="__main__":main()
