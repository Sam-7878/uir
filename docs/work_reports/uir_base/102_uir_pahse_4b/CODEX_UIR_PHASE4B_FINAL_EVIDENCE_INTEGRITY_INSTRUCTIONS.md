# CODEX Work Order — Phase UIR-4B
## Final Evidence Integrity, Baseline Fidelity, and Leakage Audit

### Target manuscript
**A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents**

### Purpose
Phase UIR-4 substantially strengthened the manuscript, but the uploaded Phase-4 evidence package still contains several publication-critical inconsistencies and unverifiable aggregate results.

Phase 4B is **not an architecture-development phase**.

Its purpose is to establish a single auditable source of truth for:
- every reported metric,
- every baseline implementation,
- every external benchmark case,
- every model invocation,
- every latency value,
- every formal safety claim.

After Phase 4B, architecture development must stop and manuscript drafting/polishing begins.

---

# 0. Preserve All Existing Evidence

Treat Phase-3D and Phase-4 artifacts as immutable historical records.

Create:

```text
results/uir_phase4b/
```

Do NOT overwrite:

```text
results/uir_phase3d/
results/uir_phase4/
```

Record the Phase-4 artifacts as:

```text
phase4_original_evidence
```

Phase-4B must explain corrections rather than silently replacing prior numbers.

---

# 1. Critical Issues Requiring Correction

The following issues were found during independent review of the uploaded Phase-4 package.

## ISSUE 1 — Conflicting FinQA numbers

`REPORT_PHASE4_JOURNAL_STRENGTHENING.md` reports approximately:

```text
C1 = 62.0% Exact Match
C2 = 64.0%
C4 = 84.0%
C8 = 94.5%
```

but the uploaded:

```text
external_finance_results.csv
```

contains:

```text
C1 = 62.0%
C2 = 64.0%
C4 = 100.0%
C8 = 100.0%
```

This must be resolved from per-case raw predictions.

No manuscript table may be generated until a single source of truth exists.

---

## ISSUE 2 — Conflicting C8 numeric metrics

Phase-4 aggregate files disagree about C8 numeric performance.

Examples:

```text
strong_baseline_summary.csv:
numeric_exact_match = 100.0%

safety_utility_summary.csv:
numeric_exact_match = 100.0%

groundedness_summary.csv:
numeric_exact_match = 0.8667
```

Either:
- these metrics use different denominators/eligible subsets, or
- one or more summaries are incorrect.

Create explicit metric definitions and denominators.

Never reuse the same metric name for different populations.

---

## ISSUE 3 — Mutation test contradiction

`mutation_test_report.csv` reports:

```text
MUT-05 Truncated Structured Output
mitigation_rate = 75.0%
```

but the Phase-4 readiness text describes property/mutation testing as fully resilient/passed.

This is inconsistent.

A safety-relevant mutation with 25% unmitigated outcomes cannot be summarized as 100% resilient.

Phase 4B must:
1. inspect every MUT-05 failure,
2. classify whether the 25% are:
   - unsafe acceptance,
   - parser acceptance of incomplete output,
   - benign detection/reporting artifact,
   - or metric-definition error,
3. fix the code if safety is actually violated,
4. rerun the mutation suite.

For publication readiness, require:

```text
unsafe_acceptance_after_truncation = 0
```

Do not require every malformed output to produce the same error, but no malformed/truncated output may become an accepted unsupported response.

---

## ISSUE 4 — Aggregate-only baseline evidence

The uploaded Phase-4 archive contains aggregate CSV summaries but does not include enough per-case raw inference evidence to independently verify:

```text
C0–C8 output
model invocation
retrieved context
tool calls
policy decision
verified fact set
raw model response
final accepted response
latency
metric labels
```

Phase 4B must generate per-case evidence.

---

## ISSUE 5 — Possible external benchmark label leakage

For FinQA and HaluEval, verify that runtime inputs do NOT contain gold labels unavailable to a real system.

### FinQA prohibition

The runtime pipeline must not receive:

```text
gold answer
gold execution result
gold program
gold reasoning chain
gold evidence annotation
```

unless the same information is explicitly permitted as input by the official benchmark protocol.

Gold values may be used only by the scorer after prediction.

### HaluEval prohibition

The runtime pipeline must not receive:

```text
hallucination label
gold accept/reject decision
foil identity
gold factuality label
```

Gold labels are scoring-only.

If Phase-4 adapters leaked target labels into `VerifiedFactSet`, the Phase-4 external results are invalid and must be rerun.

---

## ISSUE 6 — Baseline fidelity is not yet auditable

Current labels include:

```text
C5 = NeMo-style guardrail
C6 = CRAG / advanced RAG
C7 = GraphRAG
```

The manuscript must distinguish:

```text
faithful implementation of published method
```

from:

```text
method-inspired local approximation
```

For every baseline, record:
- implementation source,
- package/repository,
- version/commit,
- configuration,
- deviations from the published method.

If a baseline is only inspired by NeMo/CRAG/GraphRAG, rename it accordingly.

Do not imply reproduction of an official system when it is a simplified approximation.

---

## ISSUE 7 — Latency evidence is implausibly compressed and insufficiently instrumented

Phase-4 reports tens-of-milliseconds end-to-end latency while also reporting tens of generated Phi-3.5 tokens.

Before publication, verify whether the reported latency is:
- actual wall-clock SLM inference,
- deterministic post-processing time,
- synthetic/proxy latency,
- or a derived estimate.

Phase 4B must collect actual wall-clock measurements.

---

## ISSUE 8 — Formal statements overstate what is proved

`UIR_SEMANTICS.md` currently states, in effect, that unsupported-claim survival probability is identically zero.

This is valid only under explicit assumptions such as:
- authoritative registry correctness,
- trusted fact IDs,
- correct matcher/projection implementation,
- no bypass of the output guard,
- correct renderer implementation.

The formal result should be a **conditional safety property**, not an unconditional probabilistic claim about the world or the LLM.

Likewise, cross-language canonicalization is guaranteed only for the explicitly supported controlled grammar, not arbitrary natural language.

---

## ISSUE 9 — Unsupported language codes in grammar

The EBNF currently lists:

```text
ko
en
ja
zh
```

but empirical Phase-4 language evaluation covers Korean, English, and code-mixed Korean-English inputs.

Choose one:

### Option A — preferred
Restrict the normative grammar to:

```text
ko
en
```

and list `ja`, `zh` as reserved future extension codes outside the normative grammar.

### Option B
Implement and evaluate Japanese/Chinese frontends.

Do not imply implemented language support through the grammar alone.

---

## ISSUE 10 — Manuscript/project naming drift

Correct all inconsistent labels, including:
- `Universal Immune Router` typo,
- `Unified Intermediate Representation` vs `Universal Intermediate Representation`,
- legacy title containing `Zero-Trust Execution`,
- fixed manuscript title.

Use one canonical manuscript title unless the PI explicitly approves a change:

```text
A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents
```

---

# 2. Build a Single Metric Contract

Create:

```text
evaluation/uir_phase4b/METRIC_CONTRACT.yaml
```

For every metric specify:

```yaml
metric_name:
  definition:
  numerator:
  denominator:
  eligibility:
  unit:
  higher_is_better:
  undefined_behavior:
  source_fields:
```

Required metrics include:

```text
unsupported_claim_acceptance_rate
unsupported_claim_rate
invalid_entity_far
attack_success_rate
policy_bypass_rate
useful_answer_rate
false_rejection_rate
claim_precision
claim_recall
numeric_exact_match
numeric_preservation
provenance_coverage
provenance_correctness
execution_accuracy
condition_ast_exact_match
parse_success_rate
```

If two analyses use different denominators, give them different names.

Example:

```text
numeric_exact_match_all_cases
numeric_exact_match_numeric_eligible
```

---

# 3. Create Per-Case Evidence Records

For every Phase-4B case and every baseline generate one JSONL row.

Required file:

```text
results/uir_phase4b/per_case_evidence.jsonl
```

Minimum schema:

```json
{
  "case_id": "...",
  "dataset": "...",
  "split": "...",
  "pipeline": "C8_FINAL_UIR_B6",
  "model": "...",
  "model_config_hash": "...",
  "input_hash": "...",
  "retrieval": {
    "query_hash": "...",
    "retrieved_ids": [],
    "retrieved_content_hashes": []
  },
  "tool_calls": [],
  "uir": {
    "semantic_digest": "...",
    "policy_decision": "...",
    "verified_fact_ids": []
  },
  "raw_model_output": "...",
  "raw_model_output_sha256": "...",
  "final_output": "...",
  "accepted_claims": [],
  "rejected_claims": [],
  "gold_scoring_fields": {},
  "metrics": {},
  "timing": {},
  "resource": {}
}
```

For privacy/size, full text may be stored separately by content hash, but every row must be reproducibly resolvable.

---

# 4. External Benchmark Provenance Audit

Create:

```text
results/uir_phase4b/external_benchmark_audit.json
```

For FinQA and HaluEval record:
- official repository URL,
- official commit/tag if available,
- license,
- original file SHA-256,
- selected case IDs/indexes,
- extraction script hash,
- extracted subset SHA-256,
- no-overlap/leakage checks,
- fields passed to each runtime pipeline,
- fields reserved exclusively for scoring.

## 4.1 Leakage test

Implement tests:

```text
test_finqa_gold_answer_not_in_runtime_prompt
test_finqa_gold_program_not_in_verified_factset
test_finqa_gold_label_scoring_only

test_halueval_label_not_in_runtime_prompt
test_halueval_gold_decision_scoring_only
```

The test should fail if gold-only fields appear anywhere in:
- prompt,
- retrieval index,
- VerifiedFactSet,
- policy condition,
- tool return.

---

# 5. Re-run FinQA and HaluEval From Raw Predictions

Do not regenerate aggregate results directly.

Run:

```text
official/raw case
→ pipeline prediction
→ prediction JSONL
→ frozen scorer
→ aggregate CSV
```

Required outputs:

```text
finqa_predictions_C1.jsonl
finqa_predictions_C2.jsonl
finqa_predictions_C4.jsonl
finqa_predictions_C8.jsonl

halueval_predictions_C1.jsonl
halueval_predictions_C2.jsonl
halueval_predictions_C4.jsonl
halueval_predictions_C8.jsonl
```

Then derive:

```text
external_finance_results_phase4b.csv
external_groundedness_results_phase4b.csv
```

No manually entered percentages.

---

# 6. Strong Baseline Fidelity Audit

Create:

```text
BASELINE_FIDELITY.md
```

For C0–C8 document exactly what was implemented.

Example:

```text
C5
claimed label:
actual implementation:
official package used:
version:
configuration:
differences from published NeMo Guardrails:
publication-safe name:
```

Publication rule:

- If official/faithful → cite method name directly.
- If local approximation → use:
  - `guardrail-style baseline`,
  - `corrective-retrieval baseline`,
  - `graph-structured RAG baseline`.

Do not overstate.

---

# 7. Actual Inference Provenance

For every model-generating baseline record:

```text
model selector
local model path / HF revision
tokenizer revision
quantization config
generation config
seed
do_sample
temperature
top_p
max_new_tokens
device
dtype
```

Create:

```text
MODEL_EXECUTION_MANIFEST.json
```

Also record:
- process start/end,
- GPU identity,
- CUDA/PyTorch versions,
- Git commit,
- clean/dirty worktree.

---

# 8. Real Wall-Clock Latency Campaign

Use actual measurement.

Requirements:

1. Warm up each model/pipeline.
2. Call `torch.cuda.synchronize()` before and after GPU-timed regions.
3. Use `time.perf_counter_ns()`.
4. Do not substitute formula-generated or synthetic latency.
5. Run at least 3 repeated campaign seeds/runs where generation is stochastic; 5 preferred.
6. Report first-run/cold-start separately from steady-state.
7. Separate:
   - no-model reject latency,
   - retrieval latency,
   - model prefill,
   - generation,
   - validation,
   - deterministic rendering.

Required metrics:

```text
TTFT
end_to_end_ms
model_inference_ms
prefill_ms if measurable
generation_ms
output_tokens
tokens_per_sec
retrieval_ms
uir_compile_ms
policy_ms
output_validation_ms
```

Required files:

```text
latency_raw_phase4b.csv
latency_summary_phase4b.csv
resource_raw_phase4b.csv
```

A reviewer must be able to reproduce P50/P95/P99 from raw rows.

---

# 9. Correct the Mutation Suite

Investigate `MUT-05`.

Required outcome classes:

```text
SAFE_REJECT
SAFE_PARTIAL_RECOVERY
UNSAFE_ACCEPT
TEST_HARNESS_ERROR
```

Publication gate requires:

```text
UNSAFE_ACCEPT = 0
```

If nonzero, fix structured-output validation and rerun.

Report:
- number truncated,
- syntactically invalid,
- syntactically valid but semantically incomplete,
- accepted/rejected.

Do not call a 75% mitigation rate “fully resilient.”

---

# 10. Formal Specification Correction

Revise:

```text
UIR_SPEC.md
UIR_GRAMMAR.ebnf
UIR_SEMANTICS.md
```

## 10.1 Explicit assumptions

Add:

```text
A1 authoritative registry integrity
A2 trusted policy store integrity
A3 correct fact-id binding
A4 output guard cannot be bypassed
A5 deterministic renderer uses only accepted claims
```

State safety properties conditionally:

```text
Under A1–A5, accepted outputs contain only claims admitted by the verified projection.
```

Avoid:

```text
P(hallucination) = 0
```

unless the probability space and property are formally defined.

Prefer:

```text
Unsupported claims are unreachable in the accepted-output transition system under assumptions A1–A5.
```

## 10.2 Proof status labels

Use one of:

```text
Definition
Proposition
Proof sketch
Mechanically tested invariant
```

Do not call a code-inspection argument a full mathematical proof.

## 10.3 Cross-language scope

Change INV-5 to:

```text
For requests within the supported KO/EN controlled-language grammar and declared parallel semantics...
```

No open-domain universal-language guarantee.

---

# 11. Condition-Semantics Evidence Provenance

The Phase-4 report describes `inter-model agreement`.

This phrase is allowed only if raw judgments from actual model executions exist.

Create:

```text
condition_audit_raw_R1.jsonl
condition_audit_raw_R2.jsonl
condition_audit_raw_R3.jsonl
condition_audit_manifest.json
```

with:
- actual model selector,
- session/run identity,
- prompt hash,
- judgment,
- response hash.

If the 300-case condition study used deterministic heuristics rather than actual models, rename the result:

```text
representation-level consistency diagnostic
```

and do not call it inter-model agreement.

Strongly recommended:
- add 100–200 human-reviewed condition-heavy cases,
or
- explicitly retain no-human-audit as a limitation.

---

# 12. Cross-Backbone Claim

Current Phase-4 prose implies model/backend generality without a clearly reported second-backbone experiment.

Choose one:

## Option A — Recommended for Q1/Q2
Run a second open-weight multilingual SLM on a reduced but frozen comparison:

```text
C2
C4
C8
```

minimum:
```text
500 shared cases
+ FinQA 200
+ HaluEval 200
```

Report architecture effect across both backbones.

## Option B
Do not run a second model and remove all empirical claims implying cross-backbone replication.

State:

```text
Architecture is model-agnostic by interface design, but empirical SLM results were obtained with Phi-3.5 only.
```

---

# 13. Build an Automatic Consistency Checker

Create:

```text
evaluation/uir_phase4b/check_publication_consistency.py
```

It must parse:
- raw per-case evidence,
- aggregate CSVs,
- report Markdown,
- manuscript tables if available.

It should fail on:
- same metric name with conflicting values,
- report value not derivable from aggregate source,
- aggregate source not derivable from raw evidence,
- sample count mismatch,
- incorrect CI,
- incorrect p-value,
- stale Phase-3/Phase-4 number accidentally reused.

Output:

```text
PUBLICATION_CONSISTENCY_REPORT.md
```

Required final result:

```text
0 blocking inconsistencies
```

---

# 14. Recompute Statistics Only From Raw Paired Records

Do not construct synthetic paired arrays from aggregate rates.

For every pairwise statistical test, use actual matched case outcomes.

Binary outcomes:

```text
McNemar exact
risk difference
95% CI
```

Continuous/utility metrics:

```text
paired bootstrap
Wilcoxon when appropriate
effect size
```

Multiple comparisons:

```text
Holm correction
```

Store both:
- raw paired records,
- recomputed outputs.

---

# 15. Correct Terminology and Project Identity

Search all manuscript/report artifacts for:

```text
Universal Immune Router
Unified Intermediate Representation
Zero-Trust guarantee
hallucination eliminated
0.0% hallucination
100% resilient
NeMo Guardrails
CRAG
GraphRAG
```

For each occurrence, confirm the wording is technically justified.

Canonical project/manuscript term:

```text
Universal Intermediate Representation (UIR)
```

Canonical target title unless PI changes it:

```text
A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents
```

Use:

```text
zero-trust-inspired
```

rather than claiming compliance with a full Zero Trust Architecture standard unless evaluated as such.

---

# 16. Phase-4B Deliverables

```text
results/uir_phase4b/
├── METRIC_CONTRACT.yaml
├── MODEL_EXECUTION_MANIFEST.json
├── external_benchmark_audit.json
├── BASELINE_FIDELITY.md
├── per_case_evidence.jsonl
├── finqa_predictions_C1.jsonl
├── finqa_predictions_C2.jsonl
├── finqa_predictions_C4.jsonl
├── finqa_predictions_C8.jsonl
├── halueval_predictions_C1.jsonl
├── halueval_predictions_C2.jsonl
├── halueval_predictions_C4.jsonl
├── halueval_predictions_C8.jsonl
├── external_finance_results_phase4b.csv
├── external_groundedness_results_phase4b.csv
├── strong_baseline_summary_phase4b.csv
├── groundedness_summary_phase4b.csv
├── safety_utility_summary_phase4b.csv
├── latency_raw_phase4b.csv
├── latency_summary_phase4b.csv
├── resource_raw_phase4b.csv
├── mutation_test_report_phase4b.csv
├── condition_semantics_summary_phase4b.csv
├── stat_safety_phase4b.csv
├── stat_utility_phase4b.csv
├── stat_latency_phase4b.csv
├── PUBLICATION_CONSISTENCY_REPORT.md
└── run_manifest_phase4b.json
```

Final work report:

```text
docs/work_reports/uir_phase4b/
REPORT_PHASE4B_FINAL_EVIDENCE_INTEGRITY.md
```

---

# 17. Publication Gate

Required:

```text
phase4_original_preserved = true
metric_contract_complete = true
finqa_no_gold_leakage = true
halueval_no_gold_leakage = true
per_case_evidence_complete = true
baseline_fidelity_documented = true
actual_model_provenance_recorded = true
latency_from_real_wall_clock = true
mutation_unsafe_accept_count = 0
formal_claims_scoped_to_assumptions = true
condition_agreement_provenance_valid = true
aggregate_metrics_recomputed_from_raw = true
statistics_recomputed_from_real_pairs = true
publication_consistency_blockers = 0
```

If second backbone is not run:

```text
cross_backbone_claim_removed = true
```

Expected status:

```text
READY_FOR_FINAL_MANUSCRIPT
```

---

# 18. Stop Rule

Once:

```text
READY_FOR_FINAL_MANUSCRIPT
```

is reached:

**STOP DEVELOPMENT.**

Do not add:
- third language,
- new policy-synthesis engine,
- biology extensions,
- code-generation experiments,
- GATv2,
- additional architecture modules.

Proceed directly to:
1. final manuscript Markdown,
2. PI review,
3. section-by-section LaTeX,
4. reference verification,
5. journal formatting and submission.
