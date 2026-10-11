# Work Order — Phase UIR-4E
## Final Publication Reconciliation, Metric Repair, and Missing Generalization Evidence

### Target manuscript
**A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents**

### Phase objective

Phase UIR-4D substantially improved runtime validity, attack scoring, official benchmark provenance, mutation testing, and external-model evaluation. However, an independent audit of the uploaded Phase-4D archive found several **publication-blocking inconsistencies between the frozen raw evidence and the final reports**, together with two incomplete promised experiments.

Phase 4E is **not an architecture-development phase**.

Do not add new UIR features.

The purpose of Phase 4E is to:

1. establish one authoritative empirical source of truth;
2. repair utility metric semantics;
3. regenerate every paper/report table from raw case-level evidence;
4. complete or explicitly retract incomplete second-model claims;
5. complete a genuine grammar-constrained decoding baseline or remove that claim;
6. freeze one final manuscript-ready evidence package.

After Phase 4E, stop development.

---

# 0. Preserve all prior phases

Treat the following as immutable historical records:

```text
results/uir_phase3d/
results/uir_phase4/
results/uir_phase4b/
results/uir_phase4c/
results/uir_phase4d/
```

Create:

```text
results/uir_phase4e/
evaluation/uir_phase4e/
docs/work_reports/uir_phase4e/
```

Do not silently overwrite Phase-4D reports or CSVs.

Record corrections explicitly.

---

# 1. Publication blockers found in the Phase-4D archive

## BLOCKER 1 — Final report tables do not match the frozen raw summary

The uploaded:

```text
strong_baseline_summary_actual.csv
```

is internally consistent with direct recomputation from:

```text
per_case_evidence_actual.jsonl
```

but the Phase-4D Markdown reports contain materially different values.

Examples from the frozen raw summary:

```text
C0 unsupported_claim_rate = 35.83%
C1 unsupported_claim_rate = 49.33%
C2 unsupported_claim_rate = 33.17%
C3 unsupported_claim_rate = 27.33%
C4 unsupported_claim_rate = 23.83%
C5 unsupported_claim_rate = 0.00%
C6 unsupported_claim_rate = 11.00%
C7 unsupported_claim_rate = 78.00%
C8 unsupported_claim_rate = 0.00%
```

Attack-success values from the same raw evidence include:

```text
C0 = 66%
C1 = 92%
C2 = 84%
C3 = 50%
C4 = 0%
C5 = 0%
C6 = 0%
C7 = 90%
C8 = 0%
```

These values conflict with multiple final-report tables.

Therefore:

> No Phase-4D Markdown table is publication-authoritative until regenerated directly from the canonical raw evidence.

---

## BLOCKER 2 — “Task Completion” is currently misdefined

The Phase-4D work order defined task completion as:

```text
whether all required fields/claims were produced
```

However, direct inspection of `per_case_evidence_actual.jsonl` shows that the current `task_completion` metric is set to 1 even for **partial verified answers**.

For C8 over the 418 COMMIT-eligible cases:

```text
224 complete verified answers
48 partial verified answers
146 fail-closed / rejected answers
```

Therefore:

```text
supported-answer coverage = (224 + 48) / 418 = 65.07%
complete claim-set accuracy = 224 / 418 = 53.59%
false rejection / no-answer rate = 146 / 418 = 34.93%
```

Current Phase-4D prose incorrectly presents 65.07% as full task completion.

This must be corrected.

### Correct metric names

Use:

```text
complete_claim_set_accuracy
supported_answer_coverage
safe_partial_answer_rate
no_verified_answer_rate
conditional_claim_precision
macro_claim_recall
```

Do NOT call `complete + partial` coverage “task completion”.

---

## BLOCKER 3 — The claimed +11.96% complete-utility superiority is not supported

Current report compares:

```text
C1 = 53.11%
C8 = 65.07%
```

and claims:

```text
+11.96% task-completion advantage
```

But this compares C1 complete outputs against C8 complete+partial supported outputs.

Using the same **complete claim-set** definition:

```text
C1 complete accuracy = 53.11%
C8 complete accuracy = 53.59%
difference = +0.48 percentage points
```

From the current matched 418-case evidence:

```text
both correct = 222
C1 wrong / C8 correct = 2
C1 correct / C8 wrong = 0
both wrong = 194
```

The exact two-sided McNemar result is not significant (`p = 0.5`).

Therefore the final paper must not claim significant complete-task superiority over C1 from this experiment.

A defensible result is instead:

> C8 maintained nearly identical complete-answer accuracy while adding safe partial verified answers and enforcing a stricter evidence boundary.

---

## BLOCKER 4 — C8 precision/recall reporting is semantically inconsistent

Current report states that C8 precision equals recall at 65.07% and that all emitted claims are true.

Direct raw-case analysis shows:

```text
macro precision over all COMMIT cases = 65.07%
macro recall over all COMMIT cases = 57.81%
conditional precision among C8 cases with emitted claims = 100.00%
conditional recall among those emitted-answer cases ≈ 88.85%
```

This is not a contradiction once denominators are explicit, but the current report collapses them incorrectly.

The metric contract must distinguish:
- macro over all eligible requests,
- conditional over emitted-answer requests.

---

## BLOCKER 5 — Qwen2.5-7B external “N=200” claim is not supported by the archive

The final reports discuss FinQA and HaluEval as `N=200` external benchmarks across both model families.

However, the frozen:

```text
external_generalization_summary.csv
stat_generalization_actual.csv
```

show:

```text
Qwen FinQA test_cases = 10
Qwen HaluEval test_cases = 10
```

Therefore current Qwen results are only a **10-case pilot per benchmark**, not an N=200 replication.

The paper may not claim full cross-model external replication from these results.

Phase 4E must choose:

### Option A — recommended
Complete Qwen evaluation on the same frozen 200 FinQA + 200 HaluEval cases.

### Option B
Keep N=10 as a pilot and remove all strong cross-model generalization claims.

For a strong SCI submission, use Option A.

---

## BLOCKER 6 — Missing Qwen raw captures in the publication archive

The uploaded Phase-4D ZIP contains only aggregate Qwen results.

It does not contain sufficient raw Qwen per-case captures to independently verify:
- prompts,
- raw responses,
- contract parsing,
- latency,
- scoring,
- response hashes.

If Option A is selected, create full per-case Qwen evidence.

---

## BLOCKER 7 — Planned external constrained-decoding baseline is absent

The Phase-4D implementation plan specified:

```text
lm-format-enforcer v0.11.3
```

as a genuine external grammar-constrained decoding baseline.

The final archive contains no:
- `lm-format-enforcer` result file,
- raw capture,
- baseline summary,
- manifest entry.

The current C3 is a JSON-schema prompted/validated output condition; it is not evidence of actual constrained decoding unless an external logits processor was used.

Choose:

### Option A — recommended
Run a genuine grammar-constrained decoding baseline using `lm-format-enforcer` or an equivalent externally maintained package.

### Option B
Rename C3 to:

```text
JSON-schema prompted and validated output baseline
```

and remove all “structured decoding” claims.

For the strongest reviewer response, use Option A.

---

## BLOCKER 8 — C3 is mislabeled as “JSON Schema Structured Decoding”

Inspection of actual C3 model output shows ordinary free generation followed by validation/prompt instruction.

Unless logits were actually constrained during token decoding, publication-safe terminology is:

```text
JSON-schema prompted structured-output baseline
```

or:

```text
post-hoc JSON-schema validation baseline
```

Do not call it constrained decoding.

---

## BLOCKER 9 — “Universal / arbitrary-domain safety” language is too strong

Current reports contain statements equivalent to:

```text
UIR guarantees zero unsupported claims across arbitrary domains.
```

The formal system has already been correctly scoped to assumptions A1–A5.

The empirical claim must also remain bounded.

Use:

> Under assumptions A1–A5, unsupported claims are unreachable in the accepted-output transition system. Empirically, no unsupported accepted claims were observed on the evaluated internal and external cases.

Do not claim:
- universal hallucination elimination,
- arbitrary-domain guarantee,
- unassailable safety,
- model-independent real-world correctness.

---

# 2. Establish the authoritative source hierarchy

Create:

```text
results/uir_phase4e/AUTHORITATIVE_EVIDENCE_MAP.yaml
```

Hierarchy:

```text
Level 1: raw model / runtime captures
Level 2: per-case scored evidence
Level 3: aggregate CSV
Level 4: statistical CSV
Level 5: manuscript tables
Level 6: prose claims
```

Every Level N+1 artifact must be mechanically derived from Level N or explicitly reference it.

No hand-entered numerical table is allowed.

---

# 3. Freeze the metric contract

Create:

```text
evaluation/uir_phase4e/METRIC_CONTRACT_FINAL.yaml
```

Mandatory definitions:

## Complete answer

```text
complete_claim_set_accuracy =
cases where output claim set exactly satisfies required claim set
/
COMMIT-eligible cases
```

## Supported-answer coverage

```text
supported_answer_coverage =
cases with >=1 verified relevant claim
/
COMMIT-eligible cases
```

## Safe partial answer

```text
safe_partial_answer_rate =
cases with >=1 verified relevant claim but incomplete required claim set
/
COMMIT-eligible cases
```

## No verified answer

```text
no_verified_answer_rate =
COMMIT-eligible cases with no accepted answer
/
COMMIT-eligible cases
```

## Conditional precision

```text
conditional_claim_precision =
supported emitted claims
/
all emitted claims
```

computed only for cases with emitted claims.

## Macro recall

Define explicitly whether zero-answer cases contribute 0.

Do not reuse the word `task_completion` unless it exactly equals complete task success.

---

# 4. Re-score the current 600-case raw outputs without regeneration

Do not rerun Phi-3.5 generation unless needed.

Use the existing frozen:

```text
raw_captures/
per_case_evidence_actual.jsonl
```

as immutable model evidence.

Create one new deterministic scorer:

```text
evaluation/uir_phase4e/rescore_internal_final.py
```

It must compute all final metrics from:
- raw final outputs,
- frozen scoring cases,
- final attack oracle,
- final metric contract.

Output:

```text
results/uir_phase4e/per_case_scored_final.jsonl
results/uir_phase4e/strong_baseline_summary_final.csv
```

The scorer is the only source for final internal metrics.

---

# 5. Final internal safety-utility table

The final paper table should distinguish three dimensions:

```text
Safety
Complete Utility
Partial Utility
```

Recommended columns:

```text
pipeline
unsupported_accept_rate
attack_success_rate
complete_claim_set_accuracy
supported_answer_coverage
safe_partial_answer_rate
no_verified_answer_rate
conditional_claim_precision
macro_claim_recall
FRR
```

This prevents a safe partial answer from being mislabeled as a fully completed task.

---

# 6. Recompute statistics using corrected endpoints

Primary utility endpoint:

```text
complete_claim_set_accuracy
```

Secondary utility endpoints:

```text
supported_answer_coverage
safe_partial_answer_rate
claim recall
```

For C1 vs C8:
- use exact McNemar for complete claim-set success;
- separately test supported-answer coverage;
- report both even if one is non-significant.

Do not claim overall utility superiority unless a pre-declared primary endpoint supports it.

If complete accuracy remains statistically indistinguishable, say so.

This is scientifically acceptable and strengthens credibility.

---

# 7. Complete the Qwen2.5-7B external replication

Recommended final scope:

```text
FinQA N=200
HaluEval-QA N=200
```

Pipelines:

```text
C1
C8
```

Use the exact same frozen runtime/scoring files as Phi.

Capture:

```text
qwen_finqa_C1_raw.jsonl
qwen_finqa_C8_raw.jsonl
qwen_halueval_C1_raw.jsonl
qwen_halueval_C8_raw.jsonl
```

Per row include:
- original case ID,
- prompt hash,
- model selector,
- Ollama model digest,
- generation config,
- raw response,
- raw-response SHA-256,
- parsed contract,
- score,
- latency.

Do not extrapolate from 10 cases.

---

# 8. Optional internal second-backbone replication

Strongly recommended but not mandatory after full external Qwen replication.

Use a frozen 200-case stratified internal subset:

```text
valid benign
condition-heavy
policy violation
adversarial
numeric/provenance
invalid entity
```

Evaluate:

```text
C1
C5
C8
```

Purpose:
separate architecture safety effects from Phi-specific behavior.

If skipped, state that cross-model evidence is external-benchmark-only.

---

# 9. Genuine constrained-decoding baseline

Integrate one real external constrained-generation package.

Preferred:

```text
lm-format-enforcer
```

Alternative:
another actively maintained library with token-level grammar/schema enforcement.

Required experiment:

```text
D1_EXTERNAL_CONSTRAINED_DECODING
```

Run on the same 600 internal cases using Phi-3.5.

Capture:
- package/version,
- grammar/schema,
- logits processor configuration,
- raw output,
- schema validity,
- safety,
- complete utility,
- partial utility,
- latency.

Compare against:
- C3 prompted/post-hoc JSON schema,
- C8 UIR.

Do not imply UIR superiority over constrained decoding without this experiment.

---

# 10. Rebuild external benchmark tables

## FinQA

Report:
- N,
- official execution accuracy,
- program validity/accuracy where applicable,
- contract validity,
- unsupported accepted output,
- latency.

If C8 remains low utility, report the negative result.

Do not optimize the architecture on the frozen test split.

## HaluEval-QA

Report:
- N,
- semantic classification accuracy,
- contract validity,
- unsupported accepted output,
- invalid output rate,
- latency.

Separate:
- semantic decision error,
- format/contract rejection,
- evidence-reference error.

This distinction is a major scientific finding.

---

# 11. Correct model-scaling interpretation

If full Qwen N=200 confirms improvement on HaluEval, permitted wording:

> Increasing backbone capability improved contract adherence and task accuracy under the same UIR enforcement boundary.

Do NOT infer:

```text
larger model always improves UIR
```

from one model pair and one benchmark.

For FinQA, if both models remain poor, preserve the negative result.

---

# 12. Verify external raw evidence in the final archive

The final ZIP must contain all raw external captures used in manuscript claims.

Required:

```text
Phi FinQA C1/C8 raw
Phi HaluEval C1/C8 raw
Qwen FinQA C1/C8 raw
Qwen HaluEval C1/C8 raw
```

If tool C4 or other pipelines are reported externally, include their raw files too.

---

# 13. Publication-table generator

Create:

```text
evaluation/uir_phase4e/generate_publication_tables.py
```

It must read only final aggregate CSVs and generate:

```text
docs/work_reports/uir_phase4e/generated_tables.md
docs/work_reports/uir_phase4e/generated_tables.tex
```

No numerical table should be manually copied into the final report.

---

# 14. Strong consistency checker

Create:

```text
evaluation/uir_phase4e/check_final_publication_consistency.py
```

It must compare:

```text
per-case JSONL
aggregate CSVs
statistical CSVs
generated Markdown tables
generated LaTeX tables
final work report
final manuscript draft
```

It must fail on:
- any metric value mismatch,
- any N mismatch,
- any model sample-size mismatch,
- any CI mismatch,
- any p-value mismatch,
- wrong metric label,
- use of “task completion” for partial answer coverage,
- use of “constrained decoding” for C3 if no token constraint exists,
- Qwen N=200 claim when raw rows != 200,
- untracked manuscript number.

Required result:

```text
0 blockers
0 warnings
```

---

# 15. Overclaim lint

Add:

```text
evaluation/uir_phase4e/lint_scientific_claims.py
```

Flag publication prose containing:

```text
hallucination eliminated
universal safety
unassailable safety
arbitrary-domain guarantee
guarantees zero hallucination
all emitted claims are correct
superior task completion
```

unless the exact phrase is part of a limitation/quotation or formally scoped.

Publication-safe default:

```text
0 observed unsupported-claim acceptance
```

with N and Wilson CI.

---

# 16. Canonical Phase-4E findings that may remain negative

Phase 4E must not tune away negative findings.

The final manuscript is allowed to report:

- FinQA utility remains poor under strict UIR arithmetic contracts.
- Phi-3.5 has poor HaluEval contract adherence.
- Complete internal task accuracy may be statistically similar to Naive RAG.
- UIR obtains its primary advantage through evidence-bounded execution, safe partial responses, mutation robustness, and explicit policy enforcement rather than universal semantic superiority.

These negative findings make the paper stronger if stated clearly.

---

# 17. Final artifact package

Create:

```text
results/uir_phase4e/
├── AUTHORITATIVE_EVIDENCE_MAP.yaml
├── METRIC_CONTRACT_FINAL.yaml
├── per_case_scored_final.jsonl
├── strong_baseline_summary_final.csv
├── stat_safety_final.csv
├── stat_complete_utility_final.csv
├── stat_partial_utility_final.csv
├── latency_summary_final.csv
├── external_constrained_decoding_summary.csv
├── qwen_finqa_C1_raw.jsonl
├── qwen_finqa_C8_raw.jsonl
├── qwen_halueval_C1_raw.jsonl
├── qwen_halueval_C8_raw.jsonl
├── external_generalization_final.csv
├── external_failure_taxonomy_final.csv
├── FINAL_PUBLICATION_CONSISTENCY.md
└── PHASE4E_FINAL_MANIFEST.json
```

Final report:

```text
docs/work_reports/uir_phase4e/
REPORT_PHASE4E_FINAL_PUBLICATION_FREEZE.md
```

Generated paper tables:

```text
docs/work_reports/uir_phase4e/generated_tables.md
docs/work_reports/uir_phase4e/generated_tables.tex
```

---

# 18. Final gate

Required:

```text
phase4d_preserved = true
canonical_raw_source_defined = true
metric_contract_corrected = true
partial_vs_complete_utility_separated = true
complete_utility_stats_recomputed = true
all_report_tables_generated_from_csv = true
all_report_numbers_match_raw = true
qwen_finqa_raw_n = 200
qwen_halueval_raw_n = 200
qwen_raw_provenance_complete = true
genuine_constrained_decoding_baseline_complete = true
c3_terminology_correct = true
external_negative_results_preserved = true
scientific_overclaim_lint_pass = true
final_consistency_blockers = 0
final_consistency_warnings = 0
```

Expected status:

```text
READY_FOR_MANUSCRIPT_DRAFT_FINAL
```

---

# 19. Stop rule

Once:

```text
READY_FOR_MANUSCRIPT_DRAFT_FINAL
```

is reached:

**STOP ALL DEVELOPMENT.**

Do not add:
- new UIR architecture,
- new policy levels,
- third language,
- new domains,
- GAT/GNN components,
- Policy-Augmented Agent extensions,
- code-generation experiments,
- biology/genomics experiments.

Proceed directly to:

```text
final SCI manuscript preview (.md)
→ PI review
→ section-by-section LaTeX
→ verified bibliography
→ journal formatting
→ submission
```

---

# 20. Intended final scientific narrative

The final paper should not argue that UIR makes the language model universally smarter.

The defensible narrative is:

1. UIR separates probabilistic language generation from deterministic policy and evidence authority.
2. Under explicit trust assumptions, unsupported claims cannot enter accepted output through the verified transition system.
3. In authentic internal evaluation, UIR provides a strong evidence-control boundary and supports safe partial answers.
4. Complete-task utility is not universally superior to RAG; the benefit is a safety–utility reallocation rather than a universal reasoning gain.
5. External FinQA and HaluEval results show that semantic task performance remains dependent on backbone capability and task-contract fit.
6. Typed contracts expose model failures as rejection/partial completion instead of silently accepting fabricated outputs.
7. This separation between **system-level verifiability** and **model-level reasoning ability** is the central contribution.
