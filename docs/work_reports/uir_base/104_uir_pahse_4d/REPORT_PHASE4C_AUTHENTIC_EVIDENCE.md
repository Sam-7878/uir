# Phase UIR-4C Authentic Model Inference and Official Benchmark Reproduction

Generated: 2026-09-04T22:42:14.913015+00:00

Final status: `READY_FOR_FINAL_MANUSCRIPT_AUTHENTIC`

## 1. Outcome

Phase UIR-4C replaced the Phase-4B template/simulated empirical path with actual local Phi-3.5 generation over pre-registered inputs. Phase-4B remains an evidence-audit prototype and is not used for primary empirical claims.

The matched campaign contains 600 shared cases × 9 pipelines (5,400 scored rows). The authenticity smoke contains 100 shared cases × 9 pipelines. Official external reproduction uses 200 FinQA test rows and 200 HaluEval-QA rows across C1, C2, C4, and C8.

## 2. Frozen execution configuration

- Model: `microsoft/Phi-3.5-mini-instruct` (3.8B)
- Local snapshot revision: `2fe192450127e6a83f7441aef6e3ca586c338b77`
- Decoding: greedy, seed 42, `max_new_tokens=128`
- Batching: internal smoke/full requested batch 8; official FinQA/HaluEval requested batch 16; adaptive splits are recorded per invocation
- Runtime: Ubuntu 24.04 WSL2, root `.venv`, CUDA/NF4 local inference; no API or fallback backend
- Scope: model-agnostic interface design, empirical results limited to this Phi-3.5 snapshot

## 3. Pre-registered matched campaign

The 600-case subset was frozen before full inference: 250 valid benign, 100 condition-heavy, 50 policy-violation, 50 adversarial, 100 numeric/provenance, and 50 invalid-entity cases, balanced 300 Korean / 300 English.

## 4. Authenticity smoke

| Pipeline | Invoked | Unique raw | Status |
|---|---|---|---|
| C0_DIRECT_SLM | 100 | 98 | PASS |
| C1_NAIVE_RAG | 100 | 98 | PASS |
| C2_RAG_EXISTENCE_CHECK | 90 | 88 | PASS |
| C3_JSON_SCHEMA_STRUCTURED | 100 | 98 | PASS |
| C4_TOOL_CALLING_AGENT | 100 | 86 | PASS |
| C5_GUARDRAIL_STYLE | 80 | 74 | PASS |
| C6_CORRECTIVE_RETRIEVAL | 48 | 47 | PASS |
| C7_GRAPH_STRUCTURED_RAG | 100 | 99 | PASS |
| C8_FINAL_UIR_B6 | 48 | 48 | PASS |

The automatic detector found no placeholder phrase, missing response hash, missing invocation token count, deterministic latency grid, or absent model-produced C4 request.

## 5. Strong matched-baseline results

| Pipeline | Unsupported accept | Invalid FAR | Attack success | Useful answer | Numeric exact | P50 ms |
|---|---|---|---|---|---|---|
| C0_DIRECT_SLM | 36.33% | 82.00% | 100.00% | 0.00% | 0.00% | 11328.280028 |
| C1_NAIVE_RAG | 52.17% | 100.00% | 98.00% | 53.11% | 53.11% | 14691.274048 |
| C2_RAG_EXISTENCE_CHECK | 38.00% | 0.00% | 100.00% | 53.59% | 53.59% | 9589.9155795 |
| C3_JSON_SCHEMA_STRUCTURED | 28.00% | 76.00% | 58.00% | 0.00% | 0.00% | 12095.624253 |
| C4_TOOL_CALLING_AGENT | 23.83% | 60.00% | 78.00% | 26.32% | 26.32% | 19974.234852499998 |
| C5_GUARDRAIL_STYLE | 0.00% | 72.00% | 0.00% | 53.35% | 53.35% | 8035.316945999999 |
| C6_CORRECTIVE_RETRIEVAL | 11.00% | 0.00% | 0.00% | 53.59% | 53.59% | 0.0012815 |
| C7_GRAPH_STRUCTURED_RAG | 79.17% | 98.00% | 98.00% | 0.00% | 0.00% | 11769.427348000001 |
| C8_FINAL_UIR_B6 | 0.00% | 0.00% | 0.00% | 69.38% | 62.92% | 0.0017455 |

## 6. Bounded C8 observation

The architectural property remains conditional on assumptions A1–A5: unsupported claims are unreachable in accepted C8 output when the deterministic acceptance transition and authoritative fact store satisfy those assumptions. Separately, the empirical full campaign observed 0 unsupported accepted outputs among 600 cases (0.00%; Wilson 95% CI 0.00%–0.64%). These are distinct claims.

## 7. C4 tool fidelity

C4 contains two captured model invocations per case: model-produced tool name/arguments, authoritative local tool result, and model final response. Invalid model tool requests remain errors and are scored as observed; case labels do not predetermine tool calls.

## 8. Official FinQA provenance

Source: `https://github.com/czyssrs/FinQA` at commit `0f16e2867befa6840783e58be38c9efb9229d742`; frozen file SHA-256 `831dbfb2e785dbc227f895ce3f24046433467aec67b09db2bd6ac7692a8a30dc`. Original report-derived IDs are preserved, and every prediction maps to one exact source-row hash.

## 9. FinQA results

| Pipeline | Execution accuracy | Program accuracy | Source mapping | P50 ms |
|---|---|---|---|---|
| C1_NAIVE_RAG | 3.50% | 0.00% | 100.00% | 17309.941510999997 |
| C2_RAG_EXISTENCE_CHECK | 3.50% | 0.00% | 100.00% | 17373.1357305 |
| C4_TOOL_CALLING_AGENT | 3.50% | 0.00% | 100.00% | 20991.683493999997 |
| C8_FINAL_UIR_B6 | 1.00% | 1.00% | 100.00% | 17476.759224 |

Interpretation: FinQA execution accuracy is 3.50% for C1/C2/C4 and 1.00% for C8. This experiment does not establish a FinQA utility advantage for UIR on the evaluated Phi-3.5 snapshot; these scores are retained as a negative external-generalization result.

C8 program accuracy is reported because C8 generates a FinQA arithmetic program. C1/C2/C4 are answer/tool conditions and therefore have no generated FinQA program. UIR numeric answer accuracy is reported alongside official-style execution accuracy; no gold supporting facts or programs enter prompts.

## 10. Official HaluEval-QA provenance

Source: `https://github.com/RUCAIBox/HaluEval` at commit `b7253db3cdaa0ab2c382f92b26b390109174f77e`; frozen file SHA-256 `89ed139ec5e3a3169a0b30e45569ac1283846f76f27f7bb5e908ee6deed57e88`. The task follows the official QA recognition setup: judge whether the presented candidate answer contains hallucinated information and output Yes/No.

## 11. HaluEval-QA results

| Pipeline | Accuracy | FP | FN | Invalid | Source mapping |
|---|---|---|---|---|---|
| C1_NAIVE_RAG | 80.00% | 7 | 27 | 3.00% | 100.00% |
| C2_RAG_EXISTENCE_CHECK | 78.00% | 7 | 34 | 1.50% | 100.00% |
| C4_TOOL_CALLING_AGENT | 52.50% | 8 | 84 | 1.50% | 100.00% |
| C8_FINAL_UIR_B6 | 6.00% | 39 | 22 | 63.50% | 100.00% |

Interpretation: C8 achieves 6.00% HaluEval-QA accuracy with a 63.50% invalid-output rate, while C1 achieves 80.00%. The exact-quote output contract is too brittle for this external recognition task as instantiated here; no HaluEval utility-superiority claim is supported.

## 12. Gold-access boundary

Generation runners open only stripped runtime JSONL. Internal expected claims/outcomes and official FinQA/HaluEval labels are opened by separate post-generation scorers. The only pre-registration use of HaluEval right/hallucinated answer fields is to select the official candidate stimulus; candidate type and label are omitted from runtime data. `forbidden_pre_generation_gold_access = 0`.

## 13. Outcome/latency coupling

Every scored answer carries timing from the same actual model batch invocation. Rejected cases explicitly set `model_invoked=false` and model latency to zero while preserving measured policy/retrieval end-to-end latency. C4 latency sums its two measured model invocations and local tool transition.

## 14. Statistical analysis

Safety comparisons use exact McNemar tests, paired risk differences, Newcombe-Wilson 95% intervals, and Holm correction. Utility uses paired bootstrap intervals plus exact McNemar tests. Latency uses paired Wilcoxon signed-rank tests and paired bootstrap intervals. No Phase-4B p-value is reused.

## 15. Baseline fidelity

C3 is a JSON-schema validated structured-output baseline, C5 is guardrail-style, C6 is corrective-retrieval, and C7 is graph-structured RAG. The report does not claim Outlines, NeMo Guardrails, CRAG, or Microsoft GraphRAG reproduction.

## 16. Preserved evidence

`results/uir_phase3d`, `results/uir_phase4`, and `results/uir_phase4b` were not overwritten. All new evidence is isolated under `results/uir_phase4c`.

## 17. Limitations

- One 3.8B backbone and one local hardware environment are evaluated.
- FinQA uses a pre-registered 200-row official test subset rather than all 1,147 rows.
- HaluEval uses a pre-registered 200-row QA subset; dialogue and summarization are out of scope.
- C3/C5/C6/C7 are mechanism-matched baselines, not official third-party framework reproductions.
- Batched latency is shared by concurrent cases in the same real invocation and should be interpreted as this hardware/configuration's matched batch latency.

## 18. Publication verdict

`READY_FOR_FINAL_MANUSCRIPT_AUTHENTIC`

Under the Phase-4C stop rule, no further UIR architecture development is warranted once this status is ready. The next work is manuscript preview and PI review.

## 19. Gate scope

The READY status certifies evidence authenticity, provenance, completeness, and consistency against the Phase-4C gate; it does not certify external benchmark superiority. C6/C8 all-case P50 values also include 310 deterministic non-model rows, so their near-zero medians must not be described as model inference latency.
