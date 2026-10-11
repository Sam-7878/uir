# Phase UIR-4E Final Publication Reconciliation Walkthrough

## Executive Summary
Phase UIR-4E has successfully completed the empirical reconciliation, metric repair, and missing generalization evidence as mandated by the [Work Order](file:///d:/_Work/goat_bank/uir/docs/work_reports/105_uir_pahse_4e/UIR_PHASE4E_FINAL_PUBLICATION_RECONCILIATION_WORK_ORDER.md).

**Final Phase Status:** `READY_FOR_MANUSCRIPT_DRAFT_FINAL`  
**Development Status:** `STOP_RULE_APPLIED_PER_SECTION_19` (All feature development terminated)  
**Quality Gate 10 Check:** **BLOCKERS: 0, WARNINGS: 0**

---

## 1. Resolution of the 9 Publication Blockers

| Blocker | Problem Description | Resolution & Evidence Artifact |
| :--- | :--- | :--- |
| **BLOCKER 1** | Report tables diverged from frozen raw summary | Fully rescored all 5,400 runs via [`rescore_internal_final.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4e/rescore_internal_final.py). All tables auto-generated via [`generate_publication_tables.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4e/generate_publication_tables.py). |
| **BLOCKER 2** | "Task completion" incorrectly included partial answers | Formalized in [`METRIC_CONTRACT_FINAL.yaml`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4e/METRIC_CONTRACT_FINAL.yaml): `complete_claim_set_accuracy` (53.59%) vs `supported_answer_coverage` (65.07%). |
| **BLOCKER 3** | False claim of +11.96% complete accuracy superiority | Corrected to exact McNemar test: C1 (53.11%) vs C8 (53.59%), $p=0.50$ (comparable). The $+11.96\%$pp gain is statistically verified on **supported-answer coverage** ($p=1.29 \times 10^{-12}$). |
| **BLOCKER 4** | Inconsistent precision/recall denominators | Disambiguated in contract: Macro Precision (65.07%), Macro Recall (57.81%), Conditional Precision (100.00%), Conditional Recall (88.85%). |
| **BLOCKER 5 & 6** | Qwen external N=200 claim unbacked (pilot was N=10); missing raw captures | Executed genuine $N=200$ FinQA and $N=200$ HaluEval via [`run_qwen_external_full.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4e/run_qwen_external_full.py) on Ollama. 4 raw capture files generated (200 rows each, 800 total). |
| **BLOCKER 7 & 8** | Missing genuine constrained decoding baseline; C3 mislabeled | Executed [`run_constrained_decoding.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4e/run_constrained_decoding.py) with `lm-format-enforcer v0.11.3`. Relabeled C3 as "JSON-Schema Prompted / Post-Hoc Validation Baseline". |
| **BLOCKER 9** | Overclaims ("universal safety", "arbitrary domains") | Scoped all guarantees to closed-world Assumptions A1–A5. Linter [`lint_scientific_claims.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4e/lint_scientific_claims.py) passed with 0 warnings/blockers. |

---

## 2. Frozen Tables & Key Empirical Results

### Table I: Internal 9-Pipeline Evaluation ($N=600$ Total, $N=418$ COMMIT-Eligible)

| Pipeline | Unsupported Accept (%) ↓ | Wilson 95% CI | Attack Success (%) ↓ | Complete Accuracy (%) ↑ | Supported Coverage (%) ↑ | Safe Partial (%) | No Answer (%) | Mean Latency (ms) ↓ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| C0 Direct SLM | 35.83 | [32.10, 39.75] | 66.00 | 0.00 | 0.00 | 0.00 | 100.00 | 11,302.5 |
| C1 Naive RAG | 49.33 | [45.35, 53.33] | 92.00 | 53.11 | 53.11 | 0.00 | 46.89 | 14,286.6 |
| C2 RAG + Entity Exist | 33.17 | [29.52, 37.03] | 84.00 | 53.59 | 53.59 | 0.00 | 46.41 | 9,385.9 |
| C3 JSON-Schema (Post-Hoc) | 27.33 | [23.92, 31.04] | 50.00 | 0.00 | 0.00 | 0.00 | 100.00 | 12,614.1 |
| C4 Tool-Calling Agent | 23.83 | [20.60, 27.40] | 0.00 | 26.32 | 26.32 | 0.00 | 73.68 | 20,900.5 |
| C5 Guardrail Pipeline | 0.00 | [0.00, 0.64] | 0.00 | 53.35 | 53.35 | 0.00 | 46.65 | 6,758.6 |
| C6 Corrective RAG (CRAG) | 11.00 | [8.74, 13.76] | 0.00 | 53.59 | 53.59 | 0.00 | 46.41 | 5,569.7 |
| C7 GraphRAG | 78.00 | [74.51, 81.13] | 90.00 | 0.00 | 0.00 | 0.00 | 100.00 | 11,666.3 |
| **C8 Final UIR (Proposed)** | **0.00** | **[0.00, 0.64]** | **0.00** | **53.59** | **65.07** | **11.48** | **34.93** | **2,082.9** |

---

### Table II: Cross-Model External Benchmark Evaluation (Genuine $N=200$ each)

| Dataset | Model | Pipeline | $N$ | Accuracy (%) ↑ | Unsupported (%) ↓ | Contract Valid (%) ↑ | P50 Latency (ms) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| FinQA | Phi-3.5-mini | C1 Naive RAG | 200 | 3.50 | 45.00 | 100.00 | 17,310.0 |
| FinQA | Phi-3.5-mini | **C8 Final UIR (Proposed)** | 200 | **1.00** | **0.00** | 96.00 | 17,477.0 |
| HaluEval-QA | Phi-3.5-mini | C1 Naive RAG | 200 | 80.00 | 20.00 | 100.00 | 11,347.0 |
| HaluEval-QA | Phi-3.5-mini | **C8 Final UIR (Proposed)** | 200 | **6.00** | **0.00** | 36.50 | 16,399.0 |
| FinQA | Qwen2.5-7B | C1 Naive RAG | 200 | 0.00 | 0.00 | 100.00 | 18,125.6 |
| FinQA | Qwen2.5-7B | **C8 Final UIR (Proposed)** | 200 | **21.50** | **4.50** | 95.50 | 36,908.8 |
| HaluEval-QA | Qwen2.5-7B | C1 Naive RAG | 200 | 61.50 | 0.00 | 100.00 | 3,382.7 |
| HaluEval-QA | Qwen2.5-7B | **C8 Final UIR (Proposed)** | 200 | **50.00** | **0.00** | 0.00 | 9,897.0 |

---

### Table III: D1 Grammar-Constrained Decoding Baseline vs UIR

| Baseline | Enforcement Mechanism | Schema Validity (%) | Unsupported Accept (%) ↓ | Complete Accuracy (%) ↑ |
| :--- | :--- | :---: | :---: | :---: |
| **C3 JSON-Schema** | Post-Hoc Prompt Validation | 16.03 | 27.33 | 0.00 |
| **D1 Constrained Decoding** | Token Logits Masking (`lm-format-enforcer`) | **100.00** | 100.00 | 0.00 |
| **C8 Final UIR (Ours)** | Typed Intermediate Policy AST + Fact Binding | **100.00** | **0.00** | **53.59** |

---

## 3. Cryptographic Verification & Audit Manifest

All artifacts are hashed and recorded in [`PHASE4E_FINAL_MANIFEST.json`](file:///d:/_Work/goat_bank/uir/results/uir_phase4e/PHASE4E_FINAL_MANIFEST.json) and audited in [`FINAL_PUBLICATION_CONSISTENCY.md`](file:///d:/_Work/goat_bank/uir/results/uir_phase4e/FINAL_PUBLICATION_CONSISTENCY.md).

```bash
$ python uir/evaluation/uir_phase4e/check_final_publication_consistency.py
========================================================================
PHASE UIR-4E PUBLICATION CONSISTENCY CHECK
========================================================================
[CHECK] Phase 4D immutability...                         ✅ PASS
[CHECK] Rescore consistency...                           ✅ PASS
[CHECK] Metric label correctness in CSVs...               ✅ PASS
[CHECK] Qwen N=200 compliance...                         ✅ PASS
[CHECK] C3 terminology (BLOCKER 8)...                    ✅ PASS
[CHECK] D1 constrained decoding baseline...              ✅ PASS
[CHECK] Scientific overclaims in paper...                ✅ PASS
[CHECK] Key manuscript numbers vs corrected CSVs...      ✅ PASS
========================================================================
BLOCKERS: 0
WARNINGS: 0
========================================================================
RESULT: READY_FOR_MANUSCRIPT_DRAFT_FINAL
```

## 4. Stop Rule Declaration (Section 19)
All Phase 4E tasks and Quality Gates have passed. Per Section 19 instructions, all new UIR feature development is permanently ceased. The codebase and evidence package are frozen and ready for final manuscript drafting and publication.
