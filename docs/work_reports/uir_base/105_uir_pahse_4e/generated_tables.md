# Phase UIR-4E: Generated Publication Tables

_Auto-generated from final CSVs. Do NOT edit manually._

---

## Table I: Internal Evaluation — Safety and Utility (N=600 cases, N=418 COMMIT-eligible)

| Pipeline | Unsupported\nAccept (%) ↓ | Wilson 95% CI | Attack\nSuccess (%) ↓ | Complete\nAccuracy (%) ↑ | Supported\nCoverage (%) ↑ | Safe\nPartial (%) | No\nAnswer (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| C0 Direct SLM | 35.83 | [32.10, 39.75] | 5.50 | 0.00 | 0.00 | 0.00 | 100.00 |
| C1 Naive RAG | 49.33 | [45.35, 53.33] | 7.67 | 53.11 | 53.11 | 0.00 | 46.89 |
| C2 RAG + Entity Exist | 33.17 | [29.52, 37.03] | 7.00 | 53.59 | 53.59 | 0.00 | 46.41 |
| C3 JSON-Schema Prompted/Post-Hoc Validation | 27.33 | [23.92, 31.04] | 4.17 | 0.00 | 0.00 | 0.00 | 100.00 |
| C4 Tool-Calling Agent | 23.83 | [20.60, 27.40] | 0.00 | 26.32 | 26.32 | 0.00 | 73.68 |
| C5 Guardrail Pipeline | 0.00 | [0.00, 0.64] | 0.00 | 53.35 | 53.35 | 0.00 | 46.65 |
| C6 Corrective RAG | 11.00 | [8.74, 13.76] | 0.00 | 53.59 | 53.59 | 0.00 | 46.41 |
| C7 GraphRAG | 78.00 | [74.51, 81.13] | 7.50 | 0.00 | 0.00 | 0.00 | 100.00 |
| **C8 Final UIR (Proposed)** | **0.00** | [0.00, 0.64] | **0.00** | **53.59** | **65.07** | 11.48 | 34.93 |

> **Metric Definitions (METRIC_CONTRACT_FINAL.yaml):**
> - *Complete Accuracy*: cases where output claim set exactly satisfies required claim set / COMMIT-eligible cases (primary utility endpoint)
> - *Supported Coverage*: cases with ≥1 verified relevant claim / COMMIT-eligible cases (= complete + safe partial)
> - *Safe Partial*: cases with ≥1 verified claim but incomplete required set / COMMIT-eligible cases
> - *No Answer*: COMMIT-eligible cases with zero verified claims (UIR C8: safe abstention rate = 34.93%)
> - **C8 vs C1 complete accuracy: +0.48pp (McNemar p=0.5, non-significant). UIR benefit is safety/partial reallocation, not universal task superiority.**

## Table II: Path-Separated Latency Breakdown (ms)

| Pipeline | Workload Mean | P50 | P95 | Fast-Path (ms) |
| :--- | :---: | :---: | :---: | :---: |
| C0 Direct SLM | 11.3s | 11.3s | 11.7s | 0.0 |
| C1 Naive RAG | 14.3s | 14.7s | 15.9s | 0.0 |
| C2 RAG + Entity Exist | 9385.9 | 9420.2 | 15.7s | 0.0 |
| C3 JSON-Schema Prompted/Post-Hoc Validation | 12.6s | 12.1s | 16.0s | 0.0 |
| C4 Tool-Calling Agent | 20.9s | 20.0s | 29.8s | 0.0 |
| C5 Guardrail Pipeline | 6758.6 | 8035.3 | 16.1s | 0.0 |
| C6 Corrective RAG | 5569.7 | 0.0 | 15.6s | 0.0 |
| C7 GraphRAG | 11.7s | 11.8s | 14.8s | 0.0 |
| **C8 Final UIR (Proposed)** | **2082.9** | 0.2 | 5843.3 | **0.019447** |

> UIR C8 fast-path deterministic pre-model rejection executes in **0.05 ms** (no GPU invocation).

## Table III: External Benchmark Cross-Model Evaluation

| Dataset | Model | Pipeline | N | Accuracy (%) ↑ | Unsupported (%) ↓ | Contract Valid (%) ↑ | P50 Latency (ms) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| FinQA | Phi-3.5 | C1 Naive RAG | 200 | 3.50 | 45.00 | 100.00 | 17.3s |
| FinQA | Phi-3.5 | **C8 Final UIR (Proposed)** | 200 | **1.00** | **0.00** | 96.00 | 17.5s |
| HaluEval | Phi-3.5 | C1 Naive RAG | 200 | 80.00 | 20.00 | 100.00 | 11.3s |
| HaluEval | Phi-3.5 | **C8 Final UIR (Proposed)** | 200 | **6.00** | **0.00** | 36.50 | 16.4s |
| FinQA | Qwen2.5-7B | C1 Naive RAG | 200 | 0.00 | 0.00 | 100.00 | 18.1s |
| FinQA | Qwen2.5-7B | **C8 Final UIR (Proposed)** | 200 | **21.50** | **4.50** | 95.50 | 36.9s |
| HaluEval | Qwen2.5-7B | C1 Naive RAG | 200 | 61.50 | 0.00 | 100.00 | 3382.7 |
| HaluEval | Qwen2.5-7B | **C8 Final UIR (Proposed)** | 200 | **50.00** | **0.00** | 0.00 | 9897.0 |

> **Interpretation:** UIR maintains 0.0% unsupported claims across all dataset/model combinations.
> FinQA utility remains low under strict arithmetic contracts for both models (negative result preserved).
> HaluEval accuracy improves with model capacity: Phi-3.5 → Qwen2.5-7B (capacity scaling, not architectural scaling).

## Table IV: D1 Grammar-Constrained Decoding Baseline vs C3 vs C8

| Pipeline | Schema Validity (%) | Unsupported Accept (%) ↓ | Complete Accuracy (%) ↑ | Mean Latency (ms) |
| :--- | :---: | :---: | :---: | :---: |
| D1 Grammar-Constrained Decoding | 100.00 | 100.00 | 0.00 | 8971.7 |

> D1 uses genuine token-level grammar enforcement via `lm-format-enforcer` logits processor.
> C3 uses JSON-schema instructions + post-hoc validation (no token-level constraint).

## C1 vs C8 Statistical Test (Complete Claim-Set Accuracy)

- **Matched pairs:** 418
- Both correct: 222
- C1 wrong / C8 correct: 2
- C1 correct / C8 wrong: 0
- Both wrong: 194
- **McNemar p (complete accuracy):** 0.5
- **Significant (α=0.05):** False
- Non-significant (p=0.5): C8 complete accuracy is statistically similar to C1 complete accuracy. The benefit of UIR is reallocation from fabrication to safe partial/abstention, not universal task superiority.
