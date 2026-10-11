# Phase UIR-4F Final Metric Closure Walkthrough

## Executive Summary
Phase UIR-4F has achieved final empirical closure across all metric semantics, baseline completeness, and external benchmark acceptance as mandated by the [Work Order](file:///d:/_Work/goat_bank/uir/docs/work_reports/106_uir_pahse_4f/UIR_PHASE4F_FINAL_METRIC_CLOSURE_WORK_ORDER.md).

**Final Phase Status:** `READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL`  
**Development Status:** `STOP_RULE_INVOKED_PER_SECTION_16` (All development permanently halted)  
**Quality Gate Check (v2):** **0 BLOCKERS, 0 WARNINGS**

---

## 1. Resolution of the 4 Phase-4E Publication Blockers

| Blocker | Description | Root Cause | Resolution & Final Verified Evidence |
| :--- | :--- | :--- | :--- |
| **BLOCKER A** | D1 constrained decoding baseline had only $N=2$ | Phase 4E only piloted 2 cases | Executed [`run_constrained_decoding_600.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4f/run_constrained_decoding_600.py) on all 600 internal cases ($N_{\text{commit}}=418$). Proved schema validity = 100.0%, unsupported claims = 65.83%, complete accuracy = 0.0%. |
| **BLOCKER B** | Attack success had incompatible denominators | Mixed $N=50$ adversarial denominator with $N=600$ total workload denominator | Separated into **`Adversarial ASR (N=50)`** (C0=66%, C1=92%, C2=84%, C3=50%, C8=0.00%) and **`Workload Attack Incidence (N=600)`** (C1=7.67%, C8=0.00%) in [`security_final.csv`](file:///d:/_Work/goat_bank/uir/results/uir_phase4f/security_final.csv). |
| **BLOCKER C** | Raw unsupported generation mixed with accepted unsupported claims | Qwen FinQA C8 had 9 raw invalid extractions (4.5%) counted as unsupported claims | Proved all 9 raw cases were contract-invalid and **REJECTED** by the UIR safety boundary. `accepted_unsupported_claim_count_C8 == 0` strictly verified. |
| **BLOCKER D** | HaluEval semantic accuracy reported even when contract validity was 0% | Conflated raw model Yes/No diagnostic accuracy with end-to-end accepted system utility | Separated in [`halueval_external_final.csv`](file:///d:/_Work/goat_bank/uir/results/uir_phase4f/halueval_external_final.csv): Qwen C8 has `raw_semantic_accuracy = 50.0%`, `contract_validity = 0.0%`, `accepted_e2e_accuracy = 0.0%`, `safe_rejection = 100.0%`, `accepted_unsupported = 0.0%`. |

---

## 2. Definitive Publication Tables

### Table 1: Internal Safety and Security ($N=600$ Total, $N_{\text{attack}}=50$ Adversarial)

| Pipeline | Accepted Unsupported Claims (%) ↓ | Wilson 95% CI | Adversarial ASR ($N=50$) (%) ↓ | Invalid Entity FAR (%) ↓ | Policy Bypass (%) ↓ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| C0 Direct SLM | 35.83 | [32.10, 39.75] | 66.00 | 0.00 | 0.00 |
| C1 Naive RAG | 49.33 | [45.35, 53.33] | 92.00 | 0.00 | 0.00 |
| C2 RAG + Entity Exist | 33.17 | [29.52, 37.03] | 84.00 | 0.00 | 0.00 |
| C3 JSON-Schema Prompted / Post-Hoc | 27.33 | [23.92, 31.04] | 50.00 | 0.00 | 0.00 |
| C4 Tool-Calling Agent | 23.83 | [20.60, 27.40] | 0.00 | 0.00 | 0.00 |
| C5 Guardrail Pipeline | 0.00 | [0.00, 0.64] | 0.00 | 0.00 | 0.00 |
| C6 Corrective RAG (CRAG) | 11.00 | [8.74, 13.76] | 0.00 | 0.00 | 0.00 |
| C7 GraphRAG | 78.00 | [74.51, 81.13] | 90.00 | 0.00 | 0.00 |
| **C8 Final UIR (Proposed)** | **0.00** | [0.00, 0.64] | **0.00** | **0.00** | **0.00** |
| D1 Grammar-Constrained Decoding | 65.83 | [61.95, 69.52] | 66.00 | 0.00 | 0.00 |

---

### Table 2: Internal Utility ($N=418$ COMMIT-Eligible Requests)

| Pipeline | Complete Accuracy (%) ↑ | Supported Coverage (%) ↑ | Safe Partial (%) | No Answer (%) | Conditional Precision (%) | Macro Recall (%) | Mean Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| C0 Direct SLM | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.00 | 11,302.5 |
| C1 Naive RAG | 53.11 | 53.11 | 0.00 | 46.89 | 67.68 | 15.99 | 14,286.6 |
| C2 RAG + Entity Exist | 53.59 | 53.59 | 0.00 | 46.41 | 75.42 | 16.14 | 9,385.9 |
| C3 JSON-Schema Prompted / Post-Hoc | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.00 | 12,614.1 |
| C4 Tool-Calling Agent | 26.32 | 26.32 | 0.00 | 73.68 | 99.10 | 7.93 | 20,900.5 |
| C5 Guardrail Pipeline | 53.35 | 53.35 | 0.00 | 46.65 | 100.00 | 16.07 | 6,758.6 |
| C6 Corrective RAG (CRAG) | 53.59 | 53.59 | 0.00 | 46.41 | 100.00 | 16.14 | 5,569.7 |
| C7 GraphRAG | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.00 | 11,666.3 |
| **C8 Final UIR (Proposed)** | **53.59** | **65.07** | 11.48 | 34.93 | 100.00 | 23.78 | **2,082.9** |
| D1 Grammar-Constrained Decoding | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.00 | 7,523.9 |

---

### Table 3: Grammar-Constrained Decoding Comparison (C3 vs D1 $N=600$ vs C8)

| Baseline | Enforcement Mechanism | Schema Validity (%) | Raw Unsup. Gen. (%) ↓ | Accepted Unsup. (%) ↓ | Complete Accuracy (%) ↑ | Supported Coverage (%) ↑ | Mean Lat. (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **C3 JSON-Schema** | Post-Hoc Validation (No Logits Masking) | 16.03 | 27.33 | 27.33 | 0.00 | 0.00 | 12,614.1 |
| **D1 Constrained Decoding** | Token-Level GBNF Masking (`lm-format-enforcer`) | **100.00** | 65.83 | 65.83 | 0.00 | 0.00 | 7,523.9 |
| **C8 Final UIR (Proposed)** | Typed Policy AST + Fact Registry Binding | **100.00** | **0.00** | **0.00** | **53.59** | **65.07** | **2,082.9** |

---

### Table 4: FinQA Cross-Model Evaluation (Genuine $N=200$ Each)

| Model | Pipeline | $N$ | Raw Parse (%) | Contract Valid (%) | Safe Exec (%) | Official Accuracy (%) ↑ | Raw Unsup. Gen. (%) ↓ | Accepted Unsup. (%) ↓ | P50 Lat. |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Phi-3.5-mini | C1 Naive RAG | 200 | 100.00 | 100.00 | 100.00 | 3.50 | 45.00 | 45.00 | 17.3s |
| Phi-3.5-mini | **C8 Final UIR (Proposed)** | 200 | 96.00 | 96.00 | 96.00 | **1.00** | 0.00 | **0.00** | 17.5s |
| Qwen2.5-7B | C1 Naive RAG | 200 | 100.00 | 100.00 | 100.00 | 0.00 | 0.00 | 0.00 | 18.1s |
| Qwen2.5-7B | **C8 Final UIR (Proposed)** | 200 | 95.50 | 95.50 | 95.50 | **21.50** | 4.50 | **0.00** | 36.9s |

---

### Table 5: HaluEval Cross-Model Evaluation (Genuine $N=200$ Each)

| Model | Pipeline | $N$ | Raw Semantic Acc. (%) | Contract Valid (%) | Accepted E2E Acc. (%) ↑ | Raw Unsup. Gen. (%) ↓ | Accepted Unsup. (%) ↓ | Safe Rejection (%) | P50 Lat. |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Phi-3.5-mini | C1 Naive RAG | 200 | 80.00 | 100.00 | 80.00 | 20.00 | 20.00 | 0.00 | 11.3s |
| Phi-3.5-mini | **C8 Final UIR (Proposed)** | 200 | 72.00 | 36.50 | **6.00** | 0.00 | **0.00** | 63.50 | 16.4s |
| Qwen2.5-7B | C1 Naive RAG | 200 | 61.50 | 100.00 | 61.50 | 0.00 | 0.00 | 0.00 | 3,382.7ms |
| Qwen2.5-7B | **C8 Final UIR (Proposed)** | 200 | 50.00 | 0.00 | **0.00** | 0.00 | **0.00** | 100.00 | 9,897.0ms |

---

## 3. Consistency Audit Results (v2)

```bash
$ python uir/evaluation/uir_phase4f/check_publication_consistency_v2.py
========================================================================
PHASE UIR-4F PUBLICATION CONSISTENCY CHECKER V2
========================================================================
[CHECK] Prior phases immutability...                         ✅ PASS
[CHECK] D1 constrained decoding baseline (N=600)...          ✅ PASS
[CHECK] Security metric denominators (BLOCKER B)...          ✅ PASS
[CHECK] External metrics separation (BLOCKER C & D)...       ✅ PASS
[CHECK] Qwen provenance metadata...                         ✅ PASS
[CHECK] Generated tables consistency with CSVs...            ✅ PASS
========================================================================
BLOCKERS: 0
WARNINGS: 0
========================================================================
RESULT: READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL
```

---

## 4. Section 16 Stop Rule Declaration

All quality gates have achieved 100% compliance.
In accordance with Section 16 of the Work Order:
> Once `READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL` is reached: **STOP ALL DEVELOPMENT.**

All active development is permanently ceased. The codebase and empirical evidence package are frozen and ready for the final SCI manuscript preview and submission drafting.
