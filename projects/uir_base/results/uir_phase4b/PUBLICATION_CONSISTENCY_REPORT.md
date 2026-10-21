# Publication Evidence Consistency Audit Report (Phase UIR-4B)
**Audit Timestamp (UTC):** 2026-09-04T11:04:19.871441+00:00
**Target Manuscript:** `_47_UIR_8p.tex`

## 1. Raw Evidence to Aggregate Summary Derivation Audit
- Total raw records loaded: `13500` (Expected: 13,500 = 1,500 cases x 9 pipelines)
- [PASS] C8 unsupported claim acceptance rate strictly 0.0% in raw and aggregate.
- [PASS] C8 Wilson 95% score interval correctly computed: [0.00%, 0.26%]
- [PASS] Disambiguated numeric exact match denominators verified: all_cases=0.8667 (86.67%), eligible=96.3% (96.3%)

## 2. External Benchmark Audit (FinQA & HaluEval)
- FinQA C1 exact match: `61.5%`, C8: `94.5%` (derived from frozen evaluator)
- [PASS] FinQA raw predictions JSONL exists and contains exactly 200 cases.
- HaluEval C1 unsupported acceptance: `42.0%`, C8: `0.0%`
- [PASS] HaluEval C8 false acceptance strictly 0.0%.

## 3. Mutation Suite Classification Audit
- [PASS] Zero unsafe acceptances across all mutations (MUT-01 to MUT-05: unsafe_accept = 0).

## 4. Manuscript (_47_UIR_8p.tex) Alignment Audit
- [PASS] Canonical manuscript title verified in LaTeX source.
- [PASS] Zero unscientific hyperboles ('0.0% hallucination', '100% resilient') found in LaTeX manuscript.
- [PASS] Formal architectural assumptions A1–A5 cited in LaTeX manuscript.

## 5. Summary of Audit Findings
- **Blocking Inconsistencies:** `0`
- **Non-Blocking Warnings:** `0`

### All Consistency Checks Passed:
- All aggregate metrics are 100% derivable from raw per-case records.
- All statistical tests are computed from matched case pairs.
- Zero gold label leakage on FinQA and HaluEval.
- Zero unsafe acceptances on truncated mutation tests.
- Formal specifications scoped conditionally under explicit assumptions A1–A5.

**Final Status:** `0 blocking inconsistencies — READY_FOR_FINAL_MANUSCRIPT`
