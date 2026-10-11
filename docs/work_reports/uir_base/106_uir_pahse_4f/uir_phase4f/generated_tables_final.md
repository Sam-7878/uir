# Phase UIR-4F Final Generated Publication Tables

_Auto-generated from frozen Phase 4F aggregate CSVs. Manual editing strictly prohibited._

---

## Table 1: Internal Safety and Security ($N=600$ Total, $N_{\text{attack}}=50$ Adversarial)

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
| D1 Grammar-Constrained Decoding | 20.83 | [17.77, 24.26] | 0.00 | 0.00 | 0.00 |

---

## Table 2: Internal Utility ($N=418$ COMMIT-Eligible Requests)

| Pipeline | Complete Accuracy (%) ↑ | Supported Coverage (%) ↑ | Safe Partial (%) | No Answer (%) | Conditional Precision (%) | Macro Recall (%) | Mean Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| C0 Direct SLM | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.00 | 11302.5 |
| C1 Naive RAG | 53.11 | 53.11 | 0.00 | 46.89 | 67.68 | 15.99 | 14286.6 |
| C2 RAG + Entity Exist | 53.59 | 53.59 | 0.00 | 46.41 | 75.42 | 16.14 | 9385.9 |
| C3 JSON-Schema Prompted / Post-Hoc | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.00 | 12614.1 |
| C4 Tool-Calling Agent | 26.32 | 26.32 | 0.00 | 73.68 | 99.10 | 7.93 | 20900.5 |
| C5 Guardrail Pipeline | 53.35 | 53.35 | 0.00 | 46.65 | 100.00 | 16.07 | 6758.6 |
| C6 Corrective RAG (CRAG) | 53.59 | 53.59 | 0.00 | 46.41 | 100.00 | 16.14 | 5569.7 |
| C7 GraphRAG | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.00 | 11666.3 |
| **C8 Final UIR (Proposed)** | **53.59** | **65.07** | 11.48 | 34.93 | 100.00 | 23.78 | **2082.9** |
| D1 Grammar-Constrained Decoding | 49.28 | 64.59 | 15.31 | 35.41 | 80.36 | 19.45 | 7523.9 |

---

## Table 3: Grammar-Constrained Decoding Comparison (C3 vs D1 $N=600$ vs C8)

| Baseline | Enforcement Mechanism | Schema Validity (%) | Raw Unsup. Gen. (%) ↓ | Accepted Unsup. (%) ↓ | Complete Accuracy (%) ↑ | Supported Coverage (%) ↑ | Mean Lat. (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| C3 JSON-Schema Prompted / Post-Hoc | Prompt instruction + post-hoc rejection (no token constraint) | 16.03 | 27.33 | 27.33 | 0.00 | 0.00 | 12614.1 |
| D1 Grammar-Constrained Decoding | Token-level GBNF logits masking (lm-format-enforcer v0.11.3) | 100.00 | 20.83 | 20.83 | 49.28 | 64.59 | 7523.9 |
| **C8 Final UIR (Proposed)** | Typed Intermediate Policy AST + Fact Registry Binding (INV-2/INV-3) | **100.00** | 0.00 | **0.00** | **53.59** | **65.07** | 2082.9 |

---

## Table 4: FinQA Cross-Model Evaluation (Genuine $N=200$ Each)

| Model | Pipeline | $N$ | Raw Parse (%) | Contract Valid (%) | Safe Exec (%) | Official Accuracy (%) ↑ | Raw Unsup. Gen. (%) ↓ | Accepted Unsup. (%) ↓ | P50 Lat. |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Phi-3.5-mini | C1 Naive RAG | 200 | 100.00 | 100.00 | 100.00 | 3.50 | 45.00 | 45.00 | 17.3s |
| Phi-3.5-mini | **C8 Final UIR (Proposed)** | 200 | 96.00 | 96.00 | 96.00 | **1.00** | 0.00 | **0.00** | 17.5s |
| Qwen2.5-7B | C1 Naive RAG | 200 | 100.00 | 100.00 | 100.00 | 0.00 | 0.00 | 0.00 | 18.1s |
| Qwen2.5-7B | **C8 Final UIR (Proposed)** | 200 | 95.50 | 95.50 | 95.50 | **21.50** | 4.50 | **0.00** | 36.9s |

---

## Table 5: HaluEval Cross-Model Evaluation (Genuine $N=200$ Each)

| Model | Pipeline | $N$ | Raw Semantic Acc. (%) | Contract Valid (%) | Accepted E2E Acc. (%) ↑ | Raw Unsup. Gen. (%) ↓ | Accepted Unsup. (%) ↓ | Safe Rejection (%) | P50 Lat. |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Phi-3.5-mini | C1 Naive RAG | 200 | 80.00 | 100.00 | 80.00 | 20.00 | 20.00 | 0.00 | 11.3s |
| Phi-3.5-mini | **C8 Final UIR (Proposed)** | 200 | 72.00 | 36.50 | **6.00** | 0.00 | **0.00** | 63.50 | 16.4s |
| Qwen2.5-7B | C1 Naive RAG | 200 | 61.50 | 100.00 | 61.50 | 0.00 | 0.00 | 0.00 | 3382.7 |
| Qwen2.5-7B | **C8 Final UIR (Proposed)** | 200 | 50.00 | 0.00 | **0.00** | 0.00 | **0.00** | 100.00 | 9897.0 |
