# Phase UIR-4B Final Evidence Integrity Walkthrough

This document summarizes the completed execution of **Phase UIR-4B Final Evidence Integrity, Baseline Fidelity, and Leakage Audit** for the primary journal manuscript:
[**"A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents"**](file:///d:/_Work/goat_bank/uir/docs/papers/_47_UIR/_47_UIR_8p.tex), strictly executing the work order [`CODEX_UIR_PHASE4B_FINAL_EVIDENCE_INTEGRITY_INSTRUCTIONS.md`](file:///d:/_Work/goat_bank/uir/docs/work_reports/101_uir_pahse_4b/CODEX_UIR_PHASE4B_FINAL_EVIDENCE_INTEGRITY_INSTRUCTIONS.md).

---

## 1. Executive Summary & Audit Status

| Audit Category | Phase 4 State | Phase 4B Reconciled State | Verification Status |
| :--- | :--- | :--- | :---: |
| **Historical Evidence** | Phase 3D/4 mutable risk | `results/uir_phase3d/` & `phase4/` preserved immutable; all 4B in `results/uir_phase4b/` | **PASS** |
| **FinQA Scoring (Issue 1)** | C4/C8 bug (100% in CSV vs 94.5% in text) | Re-run from raw per-case JSONL predictions evaluated with frozen scorer (C8=94.5%) | **PASS** |
| **C8 Denominators (Issue 2)** | Conflicting exact match (100% vs 86.67%) | Disambiguated in [`METRIC_CONTRACT.yaml`](file:///d:/_Work/goat_bank/uir/results/uir_phase4b/METRIC_CONTRACT.yaml): `all_cases` (86.67%) vs `numeric_eligible` (96.30%) | **PASS** |
| **MUT-05 Truncation (Issue 3)** | 75% mitigation rate (unexplained) | Diagnosed reporting artifact; multi-tier validator achieves **0 unsafe acceptances** (`UNSAFE_ACCEPT = 0`) | **PASS** |
| **Per-Case Evidence (Issue 4)** | Aggregate-only CSV summaries | **13,500 raw records** generated in [`per_case_evidence.jsonl`](file:///d:/_Work/goat_bank/uir/results/uir_phase4b/per_case_evidence.jsonl) | **PASS** |
| **Benchmark Leakage (Issue 5)** | Unverified prompt leakage risk | Formal audit JSON and automated pytest suite ([`test_benchmark_leakage.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4b/test_benchmark_leakage.py)) passing 5/5 | **PASS** |
| **Baseline Fidelity (Issue 6)** | Method overstatement risk | Documented in [`BASELINE_FIDELITY.md`](file:///d:/_Work/goat_bank/uir/results/uir_phase4b/BASELINE_FIDELITY.md) with publication-safe taxonomy | **PASS** |
| **Real Wall-Clock Latency (Issue 7)** | Synthetic/formula latency | Real GPU measurements with `torch.cuda.synchronize()` & `perf_counter_ns()` ([`latency_raw_phase4b.csv`](file:///d:/_Work/goat_bank/uir/results/uir_phase4b/latency_raw_phase4b.csv)) | **PASS** |
| **Formal Claims (Issue 8)** | Unconditional $P(\text{hallucination})=0$ | Scoped to conditional unreachability under explicit assumptions **A1–A5** in [`UIR_SPEC.md`](file:///d:/_Work/goat_bank/uir/docs/formal/UIR_SPEC.md) & [`UIR_SEMANTICS.md`](file:///d:/_Work/goat_bank/uir/docs/formal/UIR_SEMANTICS.md) | **PASS** |
| **Grammar Scoping (Issue 9)** | Unimplemented `ja`, `zh` in grammar | Normative grammar restricted to `ko`, `en`; `ja`/`zh` reserved as future extension codes in [`UIR_GRAMMAR.ebnf`](file:///d:/_Work/goat_bank/uir/docs/formal/UIR_GRAMMAR.ebnf) | **PASS** |
| **Naming & Modesty (Issue 10/15)** | Hyperbolic and drift phrases purged | Canonical title adopted; "0.0% hallucination" replaced by Wilson 95% interval [0.00%, 0.26%] | **PASS** |
| **Condition Semantics (Issue 11)** | Unsubstantiated "inter-model" claim | Classified honestly as "Representation-Level Consistency Diagnostic" with raw auditor logs | **PASS** |
| **Cross-Backbone (Issue 12)** | Unverified multi-model claim | Option B adopted: architecture is model-agnostic, empirical evaluation scoped to Phi-3.5 | **PASS** |
| **Paired Statistics (Issue 14)** | Synthetic aggregate tests | Exact McNemar and Wilcoxon recomputed directly from matched case outcome pairs | **PASS** |
| **Consistency Checker (Issue 13)** | Manual reconciliation risk | Automated checker ([`check_publication_consistency.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4b/check_publication_consistency.py)) verified **0 blockers, 0 warnings** | **PASS** |

---

## 2. Strong Baseline Summary Table (Phase UIR-4B Final)

Derived strictly from [`per_case_evidence.jsonl`](file:///d:/_Work/goat_bank/uir/results/uir_phase4b/per_case_evidence.jsonl) ($N=1,500$ matched cases):

| Pipeline | Unsupported Accept (\%) $\downarrow$ | Wilson 95\% CI | Invalid FAR (\%) $\downarrow$ | Attack Success (\%) $\downarrow$ | Policy Bypass (\%) $\downarrow$ | Useful Answer (\%) $\uparrow$ | Numeric (Eligible) (\%) $\uparrow$ | Numeric (All) | Latency Mean (ms) $\downarrow$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **C0 Direct SLM** | 44.93 | [42.43, 47.46] | 100.0 | 94.0 | 96.0 | 58.89 | 14.37 | 0.1293 | 26.18 |
| **C1 Naive RAG** | 31.07 | [28.78, 33.45] | 100.0 | 64.0 | 66.0 | 72.74 | 36.15 | 0.3253 | 38.93 |
| **C2 RAG + Exist Check** | 16.47 | [14.68, 18.43] | **0.0** | **44.0** | **44.0** | 81.93 | 50.52 | 0.4580 | 38.41 |
| **C3 JSON-Schema** | 25.07 | [22.94, 27.32] | 100.0 | 54.0 | 56.0 | 78.37 | 51.70 | 0.4733 | 26.61 |
| **C4 Tool-Calling Agent** | 12.00 | [10.45, 13.74] | **0.0** | 42.0 | 42.0 | 86.59 | 72.59 | 0.6700 | 39.69 |
| **C5 Guardrail Pipeline** | 4.40 | [3.47, 5.56] | **0.0** | 22.0 | 22.0 | 92.07 | 74.37 | 0.6693 | 36.59 |
| **C6 Advanced RAG** | 8.60 | [7.28, 10.13] | **0.0** | 24.0 | 24.0 | 88.59 | 76.89 | 0.7093 | 37.23 |
| **C7 GraphRAG** | 5.00 | [4.01, 6.22] | **0.0** | 16.0 | 22.0 | 92.00 | 78.74 | 0.7313 | 37.20 |
| **C8 Final UIR B6** | **0.00** | **[0.00, 0.26]** | **0.0** | **0.0** | **0.0** | **96.30** | **96.30** | **0.8667** | **22.25** |

### Statistical Significance (Matched Case Pairs vs C8)
- **C2 vs C8 (Safety):** Discordant pairs $n_{01}=247, n_{10}=0$. Exact McNemar $p = 8.84 \times 10^{-75}$ ($p_{\text{adj}} = 4.42 \times 10^{-74}$).
- **C5 vs C8 (Safety):** Discordant pairs $n_{01}=66, n_{10}=0$. Exact McNemar $p = 2.71 \times 10^{-20}$ ($p_{\text{adj}} = 2.71 \times 10^{-20}$).
- All comparisons significant at $\alpha = 0.01$ under Holm-Bonferroni correction.

---

## 3. External Public Benchmark Results (Frozen Scorer)

| Benchmark / Task | Metric | C1 Naive RAG | C2 RAG + Exist | C4 Tool Calling | C8 Final UIR B6 |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **FinQA ($N=200$)** | Exact Match Accuracy (\%) $\uparrow$ | 61.50 | 65.50 | 85.50 | **94.50** |
| (Numerical Reasoning) | Numeric Preservation (\%) $\uparrow$ | 61.50 | 65.50 | 85.50 | **94.50** |
| | Provenance Coverage (\%) $\uparrow$ | 0.00 | 0.00 | 0.00 | **100.00** |
| | Mean Latency (ms) $\downarrow$ | 41.80 | 41.85 | 41.66 | **25.44** |
| **HaluEval ($N=200$)** | Unsupported Claim Accept (\%) $\downarrow$ | 42.00 | 40.00 | 12.00 | **0.00** |
| (Hallucination Detection) | False Rejection Rate (\%) $\downarrow$ | 0.00 | 0.00 | 0.00 | **0.00** |
| | Overall Decision Accuracy (\%) $\uparrow$ | 79.00 | 80.00 | 94.00 | **100.00** |
| | Mean Claim Precision $\uparrow$ | 0.7300 | 0.7400 | 0.8800 | **1.0000** |

---

## 4. Final Publication Gate Sign-Off

All 14 gate criteria specified in Section 17 of [`CODEX_UIR_PHASE4B_FINAL_EVIDENCE_INTEGRITY_INSTRUCTIONS.md`](file:///d:/_Work/goat_bank/uir/docs/work_reports/101_uir_pahse_4b/CODEX_UIR_PHASE4B_FINAL_EVIDENCE_INTEGRITY_INSTRUCTIONS.md) have been evaluated:
- **`phase4_original_preserved`**: TRUE
- **`metric_contract_complete`**: TRUE
- **`finqa_no_gold_leakage`**: TRUE
- **`halueval_no_gold_leakage`**: TRUE
- **`per_case_evidence_complete`**: TRUE (13,500 rows)
- **`baseline_fidelity_documented`**: TRUE
- **`actual_model_provenance_recorded`**: TRUE
- **`latency_from_real_wall_clock`**: TRUE
- **`mutation_unsafe_accept_count_zero`**: TRUE (0 unsafe)
- **`formal_claims_scoped_to_assumptions`**: TRUE (A1–A5)
- **`condition_agreement_provenance_valid`**: TRUE
- **`aggregate_metrics_recomputed_from_raw`**: TRUE
- **`statistics_recomputed_from_real_pairs`**: TRUE
- **`publication_consistency_blockers_zero`**: TRUE (0 blockers)
- **`cross_backbone_claim_removed`**: TRUE (Option B)

### Stop Rule Activated
Under Section 18 of the work order:
> **STOP DEVELOPMENT.** Proceed directly to final manuscript LaTeX formatting, reference verification, and journal submission.
