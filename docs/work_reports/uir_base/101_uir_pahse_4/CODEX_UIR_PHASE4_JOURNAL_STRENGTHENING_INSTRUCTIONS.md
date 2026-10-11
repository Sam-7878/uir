# CODEX Work Order — Phase UIR-4
## External Validation, Strong Baselines, Formal UIR Specification, and Journal-Grade Robustness

### Target manuscript
**A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents**

### Objective
Strengthen the already completed Phase-3D evidence so that the manuscript can withstand Q1/Q2 SCI review focused on:
1. external validity,
2. strong contemporary baselines,
3. formal specification,
4. robustness beyond controlled templates,
5. fair runtime comparison,
6. reproducibility,
7. benchmark-annotation uncertainty.

This phase MUST NOT redesign the core UIR architecture or tune against the frozen Phase-3D benchmark.

---

# 0. Preserve the Phase-3D Evidence

The following artifacts are immutable historical evidence:

```text
frozen-v2 dataset SHA-256:
9bb8a5d423b53bae14b2c699cba6b1338f0115345f94c6b4a9f93af2400d4a3c

parser SHA-256:
bee778f3e3767fdcd64d0926f27c680143d217ea1d6febcabd08aac96de321d7

Phase-3D campaign:
phase3d-publication-final
```

Do NOT:
- edit Phase-3D labels,
- remove low-performing cases,
- retune the parser on frozen-v2,
- modify old statistics,
- replace raw artifacts.

All Phase-4 results must use new experiment/version identifiers.

---

# 1. Research Questions Added in Phase 4

### RQ7 — Strong-baseline superiority
Does the final UIR pipeline provide measurable safety/utility advantages over strong alternatives such as tool-based entity validation, constrained structured generation, guardrails, and advanced retrieval?

### RQ8 — External validity
Do the observed benefits remain on public benchmarks not authored by the project team?

### RQ9 — Formal contract validity
Can the UIR schema, type system, condition semantics, and policy transitions be specified formally enough to state and mechanically test architecture invariants?

### RQ10 — Robustness
How does the UIR frontend behave under unseen paraphrases, code-switching, nested conditions, omissions, and OOD requests?

---

# 2. P0 — Strong Baseline Expansion

The most important reviewer objection is that naive RAG is too weak.

Use the SAME local SLM backbone wherever technically possible to isolate architecture effects.

Required comparison set:

```text
C0  Direct SLM
C1  Naive RAG
C2  RAG + explicit entity/existence validation tool
C3  JSON-schema / structured-output constrained generation
C4  Tool/function-calling agent with authoritative fact tools
C5  Guardrail-based pipeline
C6  Advanced retrieval baseline: Self-RAG, CRAG, or equivalent
C7  GraphRAG/KG-RAG or structured graph retrieval
C8  Final UIR B6 pipeline
```

At minimum C2, C3, C4, C5 and one of C6/C7 MUST be implemented.

## 2.1 Critical existence-check baseline

C2 is mandatory because reviewers may argue that invalid-entity safety is achieved by a trivial existence check.

C2:

```text
user request
-> standard parser/model
-> authoritative entity existence check
-> if invalid: typed reject
-> otherwise normal RAG/SLM
```

Compare C2 vs C8 on:
- invalid entity FAR,
- FRR,
- useful answer rate,
- policy violations,
- unsupported claim acceptance,
- condition handling,
- provenance,
- latency.

The paper must report honestly if C2 matches C8 on simple invalid-entity rejection.

---

# 3. P0 — External Public Benchmark Evaluation

Add at least TWO public external benchmark families.

## 3.1 Financial / numerical benchmark

Preferred candidates:

```text
FinQA
TAT-QA
ConvFinQA
```

Choose at least one.

Purpose:
- financial numerical reasoning,
- evidence selection,
- exact numeric output,
- provenance/evidence trace where available.

Do not alter official labels.

Create an adapter:

```text
external question
-> benchmark adapter
-> UIR or baseline input
-> system response
-> official metric + project metrics
```

Report both:
- official benchmark metric,
- project-specific groundedness/safety metrics.

## 3.2 Grounded-generation / hallucination benchmark

Preferred candidates:

```text
RAGTruth
HaluEval
FELM
```

Choose at least one benchmark whose license and evaluation format permit reproducible local use.

Purpose:
- unsupported claim detection,
- grounded generation,
- refusal/acceptance behavior.

## 3.3 Dataset integrity

For every external dataset record:

```text
dataset name
official source
version
split
license
download date
SHA-256
adapter commit
```

No tuning on the final test split.

---

# 4. P0 — Journal-Grade Metric Set

Use the final Phase-3D metrics consistently across all new baselines.

## Safety

```text
unsupported_claim_acceptance_rate
invalid_entity_FAR
policy_bypass_rate
attack_success_rate
renderer_on_reject_rate
```

## Utility

```text
useful_answer_rate
claim_precision
claim_recall
outcome_accuracy
FRR
coverage
partial_verified_answer_rate
```

## Factuality

```text
numeric_exact_match / numeric_preservation
unit_accuracy
citation/provenance_coverage
citation/provenance_correctness
```

## Frontend

```text
semantic_exact_match
slot_F1
condition_AST_exact_match
parse_failure_rate
NeedsClarification precision/recall
```

Do NOT report “hallucination eliminated.”

Permitted form:

```text
0 observed unsupported-claim acceptance on N evaluated cases
```

with Wilson CI.

---

# 5. P0 — Formal UIR Specification

The current JSON Schema is necessary but not sufficient for a top-tier journal.

Create:

```text
docs/formal/UIR_SPEC.md
docs/formal/UIR_GRAMMAR.ebnf
docs/formal/UIR_SEMANTICS.md
```

## 5.1 EBNF or equivalent grammar

Specify:
- requests,
- semantic intent,
- target,
- parameters,
- conditions,
- policy constraints,
- execution contract,
- output contract.

## 5.2 Typed condition AST

Formally define:

```text
EQ
NE
GT
GE
LT
LE
AND
OR
NOT
EXCEPT
```

if supported by the implementation.

Define type constraints such as:

```text
GT(Number, Number) -> Bool
AND(Bool, Bool, ...) -> Bool
NOT(Bool) -> Bool
```

Invalid typed expressions must fail before execution.

## 5.3 Operational policy semantics

Define evaluation judgments conceptually as:

```text
<UIR, Policy, Context> ⇓ Decision
```

with outcomes:

```text
Allow
Reject
Quarantine
NeedsClarification
```

## 5.4 Formal invariants

State and mechanically test at least:

### INV-1 Fail-closed execution
If policy outcome is Reject or Quarantine, the executor and renderer are never invoked.

### INV-2 Verified-claim acceptance
A final accepted factual claim must resolve to an accepted verified fact or an explicitly permitted deterministic transformation.

### INV-3 Numeric binding
A bound authoritative numeric field must equal the source fact value.

### INV-4 Semantic digest invariance
Excluded provenance fields must not change semantic digest.

### INV-5 Cross-language canonicalization
Equivalent supported-language requests should map to equivalent canonical semantic forms under the defined controlled-language coverage.

Do not claim mathematical proof beyond what is actually formalized/tested.

---

# 6. P0 — Property-Based and Mutation Testing

Add Rust property-based tests where appropriate.

Recommended tool:

```text
proptest
```

Generate:
- condition ASTs,
- policy combinations,
- metadata variations,
- invalid type combinations,
- nested Boolean structures.

Required tests:

```text
semantic digest unchanged by excluded metadata
Reject/Quarantine never reaches executor
unsupported claim never survives B6
numeric binding never mutates authoritative value
policy precedence deterministic
canonicalization stable under serialization round trip
```

Add mutation tests or targeted fault injection for:
- bypassing policy call,
- skipping entity validation,
- corrupted provenance,
- altered numeric fact,
- truncated structured output.

Produce:

```text
formal_invariant_test_report.csv
mutation_test_report.csv
```

---

# 7. P0 — Frontend Robustness / OOD Campaign

Phase-3D already provides frozen generalization results; Phase 4 must add a separate robustness stress suite without modifying frozen-v2.

Construct:

```text
ROBUSTNESS-v1
```

Recommended minimum:

```text
1,000 cases
KO >= 400
EN >= 400
code-mixed >= 200
```

Include:

```text
5 paraphrases per semantic seed where feasible
word-order variation
Korean particle variation
spacing variation
honorific/imperative variants
English preposition variation
negation
double negation
unless/except
nested conditions
coordination
ellipsis/underspecification
multi-entity requests
code-switching
OOD unsupported requests
```

Metrics:

```text
intent accuracy
slot F1
target exact match
condition AST exact match
parse failure
NeedsClarification precision
NeedsClarification recall
policy outcome accuracy
```

Keep ROBUSTNESS-v1 development and test splits separate.

Freeze the test subset before final run.

---

# 8. P0 — Condition-Semantics Investigation

The actual Phase-3D audit found materially low cross-model agreement for `conditions_valid`.

This MUST become an explicit analysis target rather than a footnote.

## 8.1 Build a condition-focused diagnostic subset

At least:

```text
300 condition-heavy cases
```

Categories:

```text
AND/OR
NOT
unless
except
nested conditions
scope ambiguity
coordination
temporal condition
mixed-language condition
implicit condition
```

## 8.2 Compare representations

Evaluate:

```text
surface-text judgment
current condition AST
normalized condition AST
explicit parenthesized DSL form
```

Goal:
Determine whether disagreement comes from:
- ambiguous source wording,
- frontend parsing,
- candidate ground truth,
- reviewer-model interpretation.

## 8.3 Optional but strongly recommended human expert audit

If feasible:

```text
100–200 condition-heavy cases
```

with at least one competent human reviewer; two are preferable.

This is not required for architecture execution, but it substantially strengthens a Q1 submission because three AI reviewers showed low condition agreement.

If no human audit is performed, state this explicitly as a limitation.

---

# 9. P0 — Fair Runtime / Resource Evaluation

Re-run all final baselines under matched conditions.

For each pipeline report:

```text
N
P50
P95
P99
TTFT
generation tokens
input tokens
tokens/sec
VRAM peak
RAM peak
CPU utilization where available
UIR overhead
retrieval overhead
validation overhead
```

Rules:

1. Same hardware.
2. Same model quantization where possible.
3. Same output-token cap.
4. Separate valid / reject / adversarial query latency.
5. Do not average fast reject cases together with long generation cases without a category breakdown.
6. Report per-output-token normalized generation latency where useful.

Produce:

```text
latency_by_category.csv
resource_summary.csv
```

---

# 10. P0 — Statistical Analysis

For every paired final comparison against C8/UIR:

## Binary outcomes
Use:

```text
McNemar
risk difference
95% CI
```

## Precision/recall/continuous utility
Use:

```text
paired/bootstrap CI
```

## Latency
Use:

```text
Wilcoxon signed-rank
paired bootstrap CI
```

Apply Holm correction where multiple comparisons are made.

Report effect sizes, not only p-values.

---

# 11. P0 — Reproducibility Package

Prepare an anonymous/publication-ready artifact package.

Minimum:

```text
README.md
environment lock files
Rust toolchain
Python requirements/lock
dataset manifests
benchmark adapters
prompt templates
UIR schema
UIR EBNF
policy fixtures
evaluation scripts
statistics scripts
reproduction commands
model manifest
hardware manifest
```

If allowed:

```text
GitHub public repository
Zenodo archival DOI
```

If public release must wait until acceptance:

```text
anonymous supplementary repository
```

No secret/internal `/hete` material may be exposed.

Only `/hete_sandbox` publication artifacts may be packaged.

---

# 12. P1 — Cross-Backbone Replication

Strongly recommended.

Repeat the final C2/C3/C4/C8 comparison on at least one additional multilingual open-weight SLM.

Purpose:
Show that UIR effects are architectural rather than Phi-3.5-specific.

Report:

```text
model
parameter size
quantization
context
hardware
same benchmark hashes
same policy engine
same UIR code
```

Do not retune policies per model unless explicitly reported as a separate experiment.

---

# 13. P1 — Multilingual Scope Decision

Current empirical language coverage is Korean + English.

Choose ONE strategy.

## Strategy A — Keep architecture scope modest
Keep KO/EN only and revise manuscript terminology to:

```text
Korean-English multilingual
```

or:

```text
bilingual / cross-lingual
```

where appropriate.

## Strategy B — Add a third language
If time permits, add a structurally different language such as Japanese or Chinese.

Requirements:
- frontend adapter,
- >= 300 frozen cases,
- parallel semantic subset,
- semantic digest equivalence,
- policy consistency.

Do not add a third language only to protect the word “Universal.”

---

# 14. P1 — Strong Cloud Upper-Bound Baseline

Optional but valuable if cost/data policy permits.

Compare a strong hosted model with:

```text
JSON schema
function/tool calling
authoritative fact tool
```

Purpose:
Answer the reviewer question:

> Could a stronger model plus tool calling reproduce the same behavior without UIR?

This is an upper-bound comparison, not a privacy-equivalent deployment baseline.

Do not send sensitive/private data.

---

# 15. Explicitly Retire Legacy GATv2 Claims

The current UIR paper should NOT reintroduce the old GATv2 causal-attention claim.

Required repository/manuscript cleanup:

```text
search for:
GATv2
attention causality
root-cause probability
78.94%
mathematical causality
```

If these occur in legacy UIR manuscript text:
- remove from core contribution,
- move unrelated material to another project,
- never interpret attention weight as causal contribution.

For the current paper, structured verified facts and policy/condition semantics are sufficient.

No new GAT development is required.

---

# 16. Phase-4 Deliverables

Create:

```text
results/uir_phase4/
├── BASELINE_MANIFEST.json
├── external_benchmark_manifest.json
├── external_finance_results.csv
├── external_groundedness_results.csv
├── strong_baseline_summary.csv
├── frontend_robustness_summary.csv
├── condition_semantics_summary.csv
├── policy_summary.csv
├── groundedness_summary.csv
├── safety_utility_summary.csv
├── latency_by_category.csv
├── resource_summary.csv
├── stat_safety.csv
├── stat_utility.csv
├── stat_latency.csv
├── formal_invariant_test_report.csv
├── mutation_test_report.csv
├── failures.jsonl
└── run_manifest.json
```

Formal documentation:

```text
docs/formal/
├── UIR_SPEC.md
├── UIR_GRAMMAR.ebnf
└── UIR_SEMANTICS.md
```

Final report:

```text
docs/work_reports/uir_phase4/REPORT_PHASE4_JOURNAL_STRENGTHENING.md
```

---

# 17. Required Final Report Structure

1. Phase-3D evidence preserved
2. Reviewer-driven motivation
3. Strong baseline definitions
4. External benchmark integrity
5. Formal UIR specification
6. Invariant/property testing
7. Multilingual frontend robustness
8. Condition-semantics analysis
9. Strong baseline results
10. External financial results
11. External groundedness results
12. Safety–utility trade-off
13. Runtime/resource fairness
14. Statistical significance
15. Cross-backbone replication, if performed
16. Reproducibility package
17. Remaining limitations
18. Manuscript-readiness verdict

---

# 18. Journal-Readiness Gate

Required before final journal manuscript polishing:

```text
strong tool/existence baseline complete
structured-output baseline complete
guardrail baseline complete
>= 1 advanced RAG/graph baseline complete
>= 2 external benchmark families complete
formal UIR grammar/type semantics complete
property/invariant tests pass
ROBUSTNESS-v1 final test frozen and complete
condition-semantic analysis complete
fair runtime comparison complete
statistical analysis complete
reproducibility package complete
```

Strongly recommended:

```text
second SLM backbone replication
human condition-heavy audit
```

---

# 19. Stop Rule

After Phase 4:

- do not add new architecture features,
- do not retune on frozen-v2,
- do not reintroduce GATv2,
- do not expand into biology, coding, or policy-synthesis research in this manuscript.

Those ideas belong to future work.

Proceed to:
1. revise manuscript claims and title/scope,
2. rebuild Related Work with verified references,
3. write final LaTeX sections,
4. prepare journal submission package.
