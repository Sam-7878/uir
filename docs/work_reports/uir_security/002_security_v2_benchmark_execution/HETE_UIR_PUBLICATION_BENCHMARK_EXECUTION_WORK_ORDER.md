# HETE UIR-v2 Publication Benchmark Execution & Final Validation Work Order

**Status:** Required before SCI manuscript Results drafting  
**Priority:** Critical / Final experimental gate  
**Target repository:** `Sam-7878/uir`  
**Primary objective:** Convert the repaired benchmark-v2 harness from engineering validation into publication-eligible empirical evidence.

---

## 1. Current verified status

The benchmark-repair implementation has corrected the major methodological defects identified in benchmark v1:

- Model Compromise Rate (MCR) is separated from End-to-End Attack Success Rate (E2E-ASR).
- Attack success is evaluated through a case-goal oracle rather than directly from the attack-class label.
- Benign utility, FRR, structured correctness, citation accuracy, language splits, and output-quality metrics are represented.
- Single-component and multi-knockout experiment runners exist.
- Dataset audit and result validation exist.
- Development and held-out benchmark files exist.
- Phi-3.5 local runtime compatibility has been validated with an actual probe.

However, the uploaded benchmark result is currently:

```text
publication_eligible = false
runs = 1
executed cases = 12 benign smoke cases
executed attack cases = 0
```

Therefore the current numerical output is a harness smoke test only and MUST NOT be used as the empirical Results section of an SCI paper.

---

# 2. Goal of this work order

Produce a final machine-verifiable benchmark package satisfying:

```text
publication_eligible = true
```

with actual Phi-3.5 inference, all benchmark cases, repeated runs, valid attack cases, complete ablation/multi-knockout experiments, statistical tests, and internally consistent publication tables.

No new architectural security component should be added unless the production run reveals a specific failure requiring repair.

---

# 3. Freeze the experiment before running

Before any full benchmark execution:

## 3.1 Freeze repository state

Record:

```text
git commit SHA
git status
Python version
PyTorch version
Transformers version
BitsAndBytes version
CUDA runtime version
GPU model
GPU driver version
OS / WSL version
```

Create:

```text
results/llm_security_v2/publication_manifest.json
```

Example:

```json
{
  "git_commit": "...",
  "dataset_dev_sha256": "...",
  "dataset_heldout_sha256": "...",
  "model": "microsoft/Phi-3.5-mini-instruct",
  "model_revision": "...",
  "quantization": "NF4",
  "attention": "eager",
  "use_cache": false,
  "decoding": {
    "do_sample": false,
    "temperature": 0,
    "top_p": null
  },
  "runs": 3,
  "seed_base": 20260826
}
```

Once the publication benchmark begins, do not change:

- attack prompts,
- expected attack goals,
- evidence fixtures,
- policy rules,
- judge rules,

based on observed held-out results.

---

# 4. Validate both development and held-out datasets

The repository currently contains:

```text
security_benchmark_v2_development.jsonl
security_benchmark_v2_heldout.jsonl
security_benchmark_v2_manifest.json
```

Audit both datasets independently.

Required checks:

- no duplicate prompts within each split;
- no duplicate prompts across development and held-out;
- no case IDs shared across splits;
- no attack-goal leakage in user-visible prompt;
- KO/EN distributions documented;
- attack-class distributions documented;
- all benign cases include usable trusted evidence fixtures;
- all attack cases have a machine-checkable attack goal;
- no judge rule contains literal held-out prompt templates.

Generate:

```text
dataset_audit_development.json
dataset_audit_heldout.json
dataset_cross_split_audit.json
```

The paper should use the held-out split for the primary final security claims, while development data may be used for engineering and diagnostic analysis.

---

# 5. Run actual Phi-3.5 baseline benchmark

Use only the verified local Hugging Face Phi-3.5 backend.

Do NOT:

- fall back to deterministic mock output;
- fall back to Ollama;
- silently skip a failed inference;
- replace malformed results with synthetic success/failure values.

Required command pattern:

```bash
python -m evaluation.llm_security.run_security_benchmark_v2 \
  --backend phi35-transformers \
  --runs 3
```

Run on:

1. development set, for reproducibility/debug confirmation;
2. held-out set, for final publication claims.

Required baselines:

1. Vanilla SLM
2. Naive RAG
3. Prompt-only Guardrail
4. UIR-v1
5. HETE UIR-v2 Security

All five must use the same Phi-3.5 checkpoint and equivalent decoding settings where applicable.

---

# 6. Production-run completeness assertions

The runner MUST fail if the number of executed records is not exactly the expected number.

For each dataset/run:

```text
records_per_baseline == dataset_size
attack_records > 0
benign_records > 0
```

For 1,600 cases and five baselines:

```text
1 run  = 8,000 baseline executions
3 runs = 24,000 baseline executions
```

Do not allow the publication validator to pass a run containing only benign smoke cases.

Add assertions such as:

```python
assert summary["raw_counts"]["total"] == expected_dataset_size
assert summary["raw_counts"]["attacks"] == expected_attack_count
assert summary["raw_counts"]["benign"] == expected_benign_count
```

---

# 7. Run complete single-component ablation

Execute:

```bash
python -m evaluation.llm_security.run_ablation_study_v2 \
  --backend phi35-transformers \
  --runs 3
```

Required configurations:

- Full UIR-v2
- `-entity_verifier`
- `-policy_engine`
- `-context_firewall`
- `-provenance`
- `-capability_gate`
- `-output_guard`
- `-resource_guard`

For each configuration report:

- MCR
- E2E-ASR
- FRR
- benign task success
- structured exact match
- evidence citation accuracy
- latency
- per-attack-class results
- KO/EN results

Most importantly:

```text
Delta E2E-ASR
Delta MCR
Delta Utility
Delta FRR
```

must be calculated relative to Full UIR-v2.

Do not describe a component as empirically necessary unless disabling it produces a measurable threat-specific degradation.

---

# 8. Run required multi-knockout masking experiments

Execute:

```bash
python -m evaluation.llm_security.run_multi_knockout \
  --backend phi35-transformers \
  --runs 3
```

At minimum:

```text
-context_firewall -output_guard
-policy_engine -capability_gate
-provenance -entity_verifier
-entity_verifier -output_guard
```

Purpose:

- identify defense-in-depth masking;
- distinguish redundant controls from ineffective controls;
- show whether downstream guards contain model compromise even when upstream controls fail.

This experiment should directly support the paper's central distinction:

```text
Model compromise != trusted-system compromise
```

---

# 9. Publication metrics to report

## 9.1 Primary security metrics

- Model Compromise Rate (MCR)
- End-to-End Attack Success Rate (E2E-ASR)
- False Accept Rate where applicable
- False Reject Rate
- Unauthorized Tool Proposal Rate
- Unauthorized Tool Attempt Rate
- Unauthorized Tool Execution Rate
- Model Leakage Rate
- Egress Leakage Rate
- Poison Retrieval Rate
- Poison Admission Rate
- Poison Influence / PEAR
- Unsupported Claim Rate

## 9.2 Utility metrics

- Benign Task Success
- Structured Exact Match
- Evidence Citation Accuracy
- Answer Completeness
- KO utility
- EN utility

## 9.3 Performance metrics

- mean latency
- median latency
- P95 latency
- input/output tokens
- GPU VRAM peak if available
- execution failures/timeouts

---

# 10. Statistical requirements

For every primary rate:

- report numerator / denominator;
- report percentage;
- report 95% Wilson interval.

Example:

```text
E2E-ASR = 3 / 1,400 = 0.21%
95% Wilson CI = [...]
```

For paired baseline comparison:

- exact McNemar test;
- absolute risk reduction;
- where useful, relative risk.

For latency:

- mean + median + P95;
- bootstrap CI or justified parametric CI.

For repeated runs:

- report per-run values;
- mean and spread across runs;
- identify any non-determinism despite greedy decoding.

---

# 11. Publication gate must be strengthened

`publication_eligible=true` is allowed only when all conditions hold:

- [ ] real Phi-3.5 backend used;
- [ ] no fallback backend used;
- [ ] at least 3 complete runs;
- [ ] full expected dataset count executed;
- [ ] attack count > 0;
- [ ] benign count > 0;
- [ ] all five baseline outputs complete;
- [ ] all eight ablation configurations complete;
- [ ] all required multi-knockout configurations complete;
- [ ] statistical tests generated from non-zero paired sample size;
- [ ] dataset hashes match frozen manifest;
- [ ] no invalid-output rate above the predefined tolerance;
- [ ] no silent inference failures;
- [ ] generated report exactly matches summary JSON;
- [ ] held-out results exist;
- [ ] result validation passes.

A smoke run containing `0 / 0` attack denominators MUST always return:

```text
publication_eligible = false
```

---

# 12. Explicit validation of judges

Before using full results, perform a small manually reviewed oracle-validation sample.

Randomly select at least:

```text
20 cases per attack class
+ 20 benign cases
```

or the largest feasible balanced sample.

For each sample compare:

```text
human/manual expected verdict
vs
deterministic judge verdict
```

Report:

- judge agreement rate;
- disagreements by class;
- any rule corrections made **before** held-out evaluation.

Recommended acceptance:

```text
>= 95% agreement
```

If lower, revise the judge before final held-out execution.

This is necessary because a fully deterministic benchmark is only as valid as its attack-success oracle.

---

# 13. Verify Prompt-only Guardrail fairness

The previous v1 result of 100% ASR across all attacks was an evaluator artifact.

For v2:

- store the exact system prompt;
- report it in an appendix;
- do not modify it per attack class;
- use the same output budget as Vanilla where possible;
- let the independent judge evaluate real model behavior.

The paper should compare architectural enforcement against a realistic prompt-level defense, not an intentionally weak strawman.

---

# 14. Verify Naive RAG fairness

Use the same corpus/evidence candidates as HETE where feasible.

Difference should be architectural:

```text
Naive RAG:
retrieval -> raw context -> LLM

HETE:
retrieval -> provenance -> firewall -> UIR/policy -> LLM/output guard
```

Do not give Naive RAG poisoned evidence that HETE never has an opportunity to retrieve.

Report retrieval-hit rates so the comparison is interpretable.

---

# 15. Failure handling during long production runs

Every inference failure must be recorded as one of:

```text
MODEL_ERROR
CUDA_OOM
TIMEOUT
INVALID_OUTPUT
BACKEND_ERROR
```

Never convert infrastructure failure into:

```text
attack blocked
```

or:

```text
attack succeeded
```

without a predefined methodological rule.

Report infrastructure failure rate separately.

If failures exceed a predefined threshold, rerun after fixing infrastructure rather than publishing biased security rates.

---

# 16. Final publication outputs

After successful execution generate:

```text
results/llm_security_v2/final/
├── publication_manifest.json
├── benchmark_metrics_summary.json
├── heldout_metrics_summary.json
├── ablation_metrics_summary.json
├── multi_knockout_summary.json
├── statistical_tests.json
├── judge_validation.json
├── results_validation.json
├── raw_runs/
└── publication_tables/
```

and:

```text
docs/evaluation/HETE_UIR_SECURITY_BENCHMARK_V2_FINAL.md
docs/work_reports/HETE_UIR_PUBLICATION_BENCHMARK_FINAL_REPORT.md
```

---

# 17. Required final-report questions

The final report must answer numerically:

1. What is HETE UIR-v2 MCR?
2. What is HETE UIR-v2 E2E-ASR?
3. How much model compromise is contained by downstream deterministic gates?
4. What benign utility is retained?
5. What is FRR?
6. Which attack class remains the weakest?
7. Which single component has the largest threat-specific effect?
8. Which controls are masked by defense-in-depth?
9. Are KO and EN statistically similar?
10. How does HETE compare with Vanilla, Naive RAG, Prompt Guard, and UIR-v1?
11. What latency/token overhead is introduced for valid requests?
12. How much latency is saved by early attack termination?
13. Do results reproduce across three runs?
14. Do held-out results agree with development results?
15. What residual risks remain outside HETE's scope?

---

# 18. Decision rule for manuscript drafting

Only after:

```text
publication_eligible = true
```

and all acceptance criteria above pass should the final SCI manuscript be drafted using benchmark numbers.

If the production benchmark reveals non-zero E2E-ASR, do NOT automatically add another defense layer.

First determine whether the failure is:

1. a real HETE design weakness;
2. judge error;
3. dataset/evidence fixture error;
4. model-output parsing error;
5. infrastructure failure.

Only category (1) should trigger security architecture development.

A non-zero attack rate can be scientifically valuable and should not be hidden if it reflects real residual risk.

---

## Final expected outcome

The next deliverable should no longer be another smoke-test report.

It should be:

> **A fully executed, held-out, repeated Phi-3.5 security benchmark with machine-verifiable publication eligibility and statistically defensible MCR/E2E-ASR/utility/ablation results.**
