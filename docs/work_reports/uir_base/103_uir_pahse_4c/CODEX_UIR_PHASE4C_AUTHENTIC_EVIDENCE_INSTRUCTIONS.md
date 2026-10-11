# CODEX Work Order — Phase UIR-4C
## Authentic Model Inference and Official Benchmark Reproduction

### Target manuscript
**A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents**

### Status before Phase 4C
The UIR architecture, formal specification, policy engine, typed condition AST, mutation safety logic, and Phase-3D evidence are sufficiently mature.

**No new UIR architecture features are requested in Phase 4C.**

Phase 4C exists because an independent audit of the uploaded Phase-4B archive found that several results labeled as publication-grade empirical evidence are not yet supported by authentic raw model executions or authentic official benchmark cases.

The purpose of this phase is:

> Replace simulated/template evaluation artifacts with reproducible, actual model inference over frozen real inputs.

---

# 0. Preserve Phase 3D / 4 / 4B

Do not overwrite:

```text
results/uir_phase3d/
results/uir_phase4/
results/uir_phase4b/
```

Create:

```text
results/uir_phase4c/
evaluation/uir_phase4c/
docs/work_reports/uir_phase4c/
```

Treat Phase-4B as:

```text
phase4b_evidence_audit_prototype
```

until Phase-4C authentic inference is complete.

---

# 1. Publication-Blocking Findings From Independent Audit

## BLOCKER 1 — Strong-baseline “raw model outputs” are templates, not case-specific generations

The uploaded Phase-4B:

```text
per_case_evidence.jsonl
```

contains 13,500 rows, but inspection shows:

### C0
All 1,500 rows use the exact same raw output:

```text
Direct SLM generated assertion without factual retrieval.
```

### C1
All 1,500 rows use the exact same raw output:

```text
RAG context prepended: generated answer based on retrieved documents.
```

### C3
All 1,500 rows use the same JSON template.

Several other baselines contain empty or deterministic placeholder output text.

This means the Phase-4B strong-baseline metric table is not admissible as evidence of actual per-case Phi-3.5 behavior.

Phase 4C must execute the actual baseline pipelines.

---

## BLOCKER 2 — Per-case latency in the main evidence appears synthetic

The per-case evidence contains small discrete latency grids such as:

```text
24.2
25.2
26.2
27.2
28.2 ms
```

rather than raw measured wall-clock values.

Although `latency_raw_phase4b.csv` may contain a separate GPU microbenchmark, the manuscript cannot combine:
- simulated outcome records,
- separate model timing measurements,
and describe them as one end-to-end per-case experiment.

Phase 4C must record outcome and latency from the **same real invocation**.

---

## BLOCKER 3 — The “FinQA” evaluation subset is not demonstrably official FinQA test data

The Phase-4B prediction files contain IDs such as:

```text
FINQA-TEST-0000
```

and only a small number of repeated question templates.

Examples include questions about fiscal year **2024**.

The official FinQA dataset is the EMNLP 2021 dataset and its official sample IDs are report-derived IDs. The Phase-4B archive does not contain the original official source rows needed to map these generated questions back to FinQA.

Therefore:

```text
external_finance_results_phase4b.csv
```

must not be cited as FinQA performance until official FinQA examples are used.

---

## BLOCKER 4 — The “HaluEval” subset is not demonstrably official HaluEval data

The current Phase-4B prediction set contains repeated custom regulatory templates such as:

```text
Under Financial Regulations, what requirement is imposed by ...
```

and:

```text
Does ... permit organizations to ...
```

The official HaluEval benchmark contains released QA/dialogue/summarization/general hallucination examples and their original benchmark fields.

The current custom regulatory cases may remain useful as an **internal adversarial benchmark**, but they must not be called HaluEval unless exact source-example provenance is established.

---

## BLOCKER 5 — FinQA/HaluEval result generation must use actual model output, not target-controlled success simulation

For every external benchmark prediction, the model must generate its prediction from runtime-allowed input.

Forbidden generation logic includes any form of:

```python
if success:
    prediction = gold
else:
    prediction = modified_gold
```

or probabilistic corruption of the gold answer to obtain a target accuracy.

The gold answer/program/label may only be read after prediction by the scoring stage.

---

# 2. Phase-4C Scientific Objective

After Phase 4C, every primary empirical number in the manuscript must satisfy:

```text
Official or frozen input
    ↓
Actual pipeline execution
    ↓
Actual model/tool output
    ↓
Immutable raw response
    ↓
Independent scorer
    ↓
Aggregate metric
```

No metric may be created by assigning desired success/failure probabilities.

---

# 3. Actual Model Execution Harness

Create:

```text
evaluation/uir_phase4c/run_actual_baselines.py
```

Use the local:

```text
microsoft/Phi-3.5-mini-instruct
```

configuration already frozen in the model manifest.

For every model-invoking pipeline:

```text
C0
C1
C2 where valid entity reaches model
C3
C4
C5 where request passes pre-rail
C6
C7
C8 where policy permits rendering
```

perform actual `model.generate()` or the real inference API used by the project.

Do not synthesize response strings.

---

# 4. Capture Raw Inference Provenance

For every actual invocation capture:

```json
{
  "case_id": "...",
  "pipeline": "...",
  "prompt_sha256": "...",
  "prompt_text_or_content_ref": "...",
  "retrieved_context_ids": [],
  "tool_calls": [],
  "policy_decision": "...",
  "verified_fact_ids": [],
  "generation": {
    "model": "microsoft/Phi-3.5-mini-instruct",
    "hf_revision": "...",
    "seed": 42,
    "do_sample": false,
    "max_new_tokens": 128,
    "raw_response": "...",
    "raw_response_sha256": "...",
    "input_tokens": 0,
    "output_tokens": 0,
    "finish_reason": "..."
  },
  "final_output": "...",
  "timing": {
    "start_ns": 0,
    "end_ns": 0,
    "end_to_end_ms": 0.0,
    "model_ms": 0.0,
    "retrieval_ms": 0.0,
    "policy_ms": 0.0,
    "validation_ms": 0.0
  }
}
```

If storage size is a concern:
- save full prompt/response in content-addressed files,
- store hashes/references in JSONL.

---

# 5. Authentic Strong-Baseline Campaign

Do not immediately rerun all 1,500 × 9 if compute time is excessive.

Use a staged process.

## Stage A — Authenticity smoke test

Run:

```text
100 shared cases × C0–C8
```

Verify:
- model response diversity,
- actual token counts,
- real latency,
- scorer behavior,
- no gold leakage.

Gate:

```text
AUTHENTICITY_SMOKE_PASS
```

Only then run full campaign.

## Stage B — Full matched campaign

Preferred:

```text
1,500 shared cases × C0–C8
```

If runtime is prohibitive, use a pre-registered stratified subset:

```text
>= 600 shared cases
```

with:
- valid benign,
- invalid entity,
- policy violation,
- adversarial,
- condition-heavy,
- numeric/provenance

all represented.

Freeze subset before model execution.

---

# 6. Baseline Fidelity

Phase-4B correctly identified several baselines as approximations.

Retain publication-safe names.

### C3

If using a custom constrained decoder:

```text
grammar-guided structured-output baseline
```

Do not call it Outlines unless Outlines is actually used.

### C4

If tools are local deterministic mock APIs:

```text
tool-calling agent with authoritative local tools
```

This is acceptable if actual model tool selection/arguments are generated by the model.

If tool calls are predetermined by case labels, it is not a valid tool-agent baseline.

### C5

Use:

```text
guardrail-style baseline
```

unless official NeMo Guardrails is actually run.

### C6

Use:

```text
corrective-retrieval baseline
```

unless faithful CRAG reproduction is used.

### C7

Use:

```text
graph-structured RAG baseline
```

unless faithful Microsoft GraphRAG or another cited GraphRAG implementation is actually used.

---

# 7. Tool-Calling Baseline Must Be Real

C4 is a critical reviewer baseline.

The model must actually produce or select:
- tool name,
- arguments,
- call sequence.

Required trace:

```json
{
  "model_tool_request": {
    "name": "...",
    "arguments": {}
  },
  "tool_result": {},
  "model_final_response": "..."
}
```

A deterministic script that always calls `lookup_entity(case_id)` based on known benchmark metadata is not a model tool-calling agent.

---

# 8. Official FinQA Reproduction

Use the official FinQA repository/dataset.

## 8.1 Download/freeze official data

Record:
- repository URL,
- exact Git commit,
- file path,
- file SHA-256.

Preserve original fields and original FinQA example IDs.

Do not rewrite them into synthetic `FINQA-TEST-xxxx` examples.

## 8.2 Select evaluation split

Preferred:
- official public test data for reproducible academic evaluation.

Pre-register a subset if full evaluation is too expensive.

Recommended:

```text
N >= 200
```

but selected from the actual official test split.

Keep:
- original question,
- pre_text,
- post_text,
- table,
- original ID.

Scoring-only:
- program,
- exe_ans,
- gold_inds.

## 8.3 FinQA input policy

C1/C2/C4/C8 may see only information allowed by the declared experiment.

If using gold supporting facts for a special oracle experiment, label it explicitly:

```text
oracle-evidence condition
```

Do not mix it with normal end-to-end retrieval results.

## 8.4 Official-style metrics

At minimum report:

```text
execution accuracy
```

If generating reasoning programs, also report:

```text
program accuracy
```

If UIR answers numerically without reproducing FinQA program syntax, report:
- official execution accuracy where compatible,
- UIR numeric answer accuracy,
but explain metric comparability.

---

# 9. Official HaluEval Reproduction

Use official released HaluEval data.

Choose one or more official tasks:

```text
QA
knowledge-grounded dialogue
summarization
```

Prefer QA for the first reproducible experiment.

Preserve original fields such as:
- knowledge,
- question,
- right_answer,
- hallucinated_answer

according to the official release.

The model’s task must match the official evaluation setup.

Do not replace official HaluEval samples with custom regulatory questions.

The custom regulatory adversarial benchmark may be retained separately as:

```text
HETE-Regulatory-Adversarial-v1
```

and described as project-created.

---

# 10. External Benchmark Case-Level Audit

For every FinQA/HaluEval case create:

```text
source_dataset
source_original_id
source_file_sha256
source_row_hash
runtime_fields
scoring_only_fields
pipeline_prompt_hash
raw_model_response_hash
prediction
score
```

Create:

```text
OFFICIAL_BENCHMARK_PROVENANCE.json
```

Gate:

```text
every external prediction maps to one official source row
```

---

# 11. Remove Gold-Driven Prediction Logic

Search repository for suspicious patterns involving:

```text
ground_truth
official_ground_truth
gold
exe_ans
right_answer
hallucinated_answer
success_probability
success_rate
target_accuracy
```

Any code that reads gold fields before generation must be reviewed.

Create:

```text
GOLD_ACCESS_AUDIT.md
```

For every access to a gold field state:
- file,
- function,
- reason,
- pre-generation or post-generation,
- allowed/forbidden.

Publication gate requires:

```text
forbidden_pre_generation_gold_access = 0
```

---

# 12. Rebuild Per-Case Evidence From Real Outputs

Create:

```text
results/uir_phase4c/per_case_evidence_actual.jsonl
```

Do not copy Phase-4B placeholder outputs.

Authenticity checks:

```text
C0 unique_raw_output_count > 1
C1 unique_raw_output_count > 1
C3 unique_raw_output_count > 1
```

More importantly:
- each hash must correspond to actual captured inference.

Create automatic detector:

```text
detect_placeholder_evidence.py
```

Flag:
- identical responses repeated across implausibly many unrelated cases,
- deterministic latency grids,
- placeholder phrases,
- missing token IDs/counts,
- response hashes not backed by actual capture.

---

# 13. Couple Outcome and Latency Evidence

The latency reported for a case must come from the same invocation whose answer was scored.

Do not:
- measure model speed on one prompt set,
- score synthetic answers on another,
- combine them into one pipeline row.

For rejected/no-model cases:
- explicitly set `model_invoked=false`,
- model latency = 0,
- end-to-end latency remains measured.

---

# 14. Real Statistical Analysis

After authentic inference:

Recompute from actual matched outcomes.

## Safety
```text
McNemar exact
risk difference
Wilson/Newcombe CI
Holm correction
```

## Utility / correctness
```text
paired bootstrap CI
McNemar when binary
```

## Latency
```text
Wilcoxon signed-rank
paired bootstrap
```

Do not reuse any Phase-4B p-value.

---

# 15. Revisit the “0 observed unsupported acceptance” Claim

C8 may still produce zero observed unsupported acceptance if the deterministic acceptance transition system enforces it.

If so, report two distinct facts:

### Architectural property
Under assumptions A1–A5:

```text
unsupported claims are unreachable in accepted output
```

### Empirical observation
On actual Phase-4C generated outputs:

```text
0 / N unsupported claims were accepted
```

with Wilson CI.

Do not conflate these two claims.

---

# 16. Formal UIR Work Is Frozen

Do not add new formal features.

Keep:
- EBNF,
- typed AST,
- big-step policy semantics,
- A1–A5 assumptions,
- INV-1 to INV-5.

Only correct a formal document if Phase-4C finds a direct mismatch with implemented code.

---

# 17. Condition-Semantics Diagnostic

The current Phase-4B condition audit is correctly labeled as heuristic/representation-level.

Keep it as:

```text
Representation-Level Consistency Diagnostic
```

Do not call R1/R2/R3 AI-model reviewers.

If desired, a real model audit may be added later, but it is **not required** for Phase 4C publication gate.

---

# 18. Cross-Backbone Scope

Keep Option B:

```text
The architecture is model-agnostic by interface design,
but empirical generation results are reported for Phi-3.5-mini-instruct.
```

No second backbone is required in this phase.

---

# 19. Phase-4C Required Deliverables

```text
results/uir_phase4c/
├── ACTUAL_INFERENCE_MANIFEST.json
├── OFFICIAL_BENCHMARK_PROVENANCE.json
├── GOLD_ACCESS_AUDIT.md
├── BASELINE_FIDELITY_PHASE4C.md
├── authenticity_smoke_results.csv
├── per_case_evidence_actual.jsonl
├── strong_baseline_summary_actual.csv
├── finqa_predictions_actual_C1.jsonl
├── finqa_predictions_actual_C2.jsonl
├── finqa_predictions_actual_C4.jsonl
├── finqa_predictions_actual_C8.jsonl
├── finqa_results_actual.csv
├── halueval_predictions_actual_C1.jsonl
├── halueval_predictions_actual_C2.jsonl
├── halueval_predictions_actual_C4.jsonl
├── halueval_predictions_actual_C8.jsonl
├── halueval_results_actual.csv
├── latency_raw_actual.csv
├── resource_raw_actual.csv
├── stat_safety_actual.csv
├── stat_utility_actual.csv
├── stat_latency_actual.csv
├── PUBLICATION_CONSISTENCY_PHASE4C.md
└── run_manifest_phase4c.json
```

Work report:

```text
docs/work_reports/uir_phase4c/
REPORT_PHASE4C_AUTHENTIC_EVIDENCE.md
```

---

# 20. Mandatory Authenticity Tests

Add tests that fail if:

```text
all C0 responses identical
all C1 responses identical
placeholder phrase detected
raw_response_sha256 missing
model_invoked=true but token count missing
tool baseline has no model-produced tool request
external source ID has no official-source mapping
FinQA fiscal/question row not found in official frozen source
HaluEval row not found in official frozen source
gold field accessed before generation
latency record lacks measured start/end timestamp
```

---

# 21. Publication Consistency Gate

Before manuscript drafting:

```text
phase4c_actual_model_generation_complete = true
placeholder_evidence_count = 0
official_finqa_source_mapping_complete = true
official_halueval_source_mapping_complete = true
forbidden_gold_access_count = 0
tool_calling_baseline_is_model_driven = true
per_case_outcome_latency_coupled = true
aggregate_metrics_from_actual_raw = true
statistics_from_actual_pairs = true
mutation_unsafe_accept_count = 0
publication_consistency_blockers = 0
```

Expected status:

```text
READY_FOR_FINAL_MANUSCRIPT_AUTHENTIC
```

---

# 22. Stop Rule

Once:

```text
READY_FOR_FINAL_MANUSCRIPT_AUTHENTIC
```

is reached:

**STOP ALL DEVELOPMENT.**

Proceed to:
1. final SCI manuscript preview Markdown,
2. PI review,
3. section-by-section LaTeX,
4. verified references,
5. target journal formatting/submission.

No new architecture, language, domain, GAT, policy-synthesis, coding, or biology work belongs in this manuscript.
