# Work Order — Phase UIR-4F
## Final Metric Closure, Full Constrained-Decoding Baseline, and External Acceptance Semantics

### Target manuscript
**A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents**

### Purpose

Phase UIR-4E successfully repaired the major Phase-4D inconsistencies, completed the Qwen2.5-7B external runs, and separated complete answers from safe partial answers.

However, independent inspection of the uploaded Phase-4E archive identified four remaining publication-critical issues:

1. the genuine constrained-decoding baseline D1 was executed on only **2 cases**;
2. attack-success rates are reported with two incompatible denominators;
3. external “unsupported claim” metrics mix **raw model generation** with **accepted system output**;
4. HaluEval semantic accuracy is reported even when the strict C8 output contract is invalid for all Qwen cases.

Phase 4F is a **final metric/evidence closure phase only**.

No new UIR architecture, policy feature, model family, language, or domain may be added.

---

# 0. Preserve all previous evidence

Treat the following as immutable:

```text
results/uir_phase3d/
results/uir_phase4/
results/uir_phase4b/
results/uir_phase4c/
results/uir_phase4d/
results/uir_phase4e/
```

Create:

```text
results/uir_phase4f/
evaluation/uir_phase4f/
docs/work_reports/uir_phase4f/
```

Do not overwrite Phase-4E artifacts.

---

# 1. BLOCKER A — D1 constrained-decoding baseline has N=2 only

The Phase-4E archive contains:

```text
external_constrained_decoding_summary.csv
constrained_decoding_per_case.jsonl
```

but the actual experiment contains:

```text
total_cases = 2
commit_eligible_cases = 0
```

Both cases are adversarial/non-COMMIT examples.

Therefore these Phase-4E claims are not publication-valid:

```text
D1 unsupported accept = 100%
D1 complete accuracy = 0%
D1 vs C8 utility comparison
```

because D1 was never evaluated on valid task-completion cases.

## Required correction

Run:

```text
D1_EXTERNAL_CONSTRAINED_DECODING
```

on the **same frozen 600 internal cases** used for C0–C8.

Use the already integrated:

```text
lm-format-enforcer v0.11.3
```

with actual token-level logits masking.

No new prompts, no benchmark tuning.

Capture all 600 raw outputs.

Required files:

```text
results/uir_phase4f/d1_constrained_raw_600.jsonl
results/uir_phase4f/d1_constrained_summary_600.csv
```

Required metrics:

```text
schema_validity
raw_unsupported_generation_rate
accepted_unsupported_claim_rate
complete_claim_set_accuracy
supported_answer_coverage
safe_partial_answer_rate
no_verified_answer_rate
conditional_claim_precision
macro_claim_recall
latency
```

Only after this run may the manuscript compare D1 against C3 and C8.

---

# 2. BLOCKER B — Attack success has incompatible denominators

Phase-4E generated tables report values such as:

```text
C0 = 5.50%
C1 = 7.67%
C2 = 7.00%
```

because successful attacks are divided by all 600 cases.

Other Phase-4E reports report:

```text
C0 = 66%
C1 = 92%
C2 = 84%
```

because attack success is divided by the 50 adversarial cases.

Both arithmetic forms can be derived from the same raw outcomes, but they represent different metrics.

## Final metric definitions

Define:

### Adversarial Attack Success Rate — primary security metric

```text
adversarial_attack_success_rate =
successful behavioral attacks
/
adversarial attack cases
```

Denominator:

```text
N_attack = 50
```

### Workload Attack-Incidence Rate — optional secondary metric

```text
workload_attack_incidence_rate =
successful behavioral attacks
/
all workload cases
```

Denominator:

```text
N_total = 600
```

Do not use the generic label:

```text
attack_success_rate
```

without specifying the denominator.

## Required final table

Primary manuscript security table must use:

```text
Adversarial ASR (N=50)
```

and may include workload incidence only in supplementary material.

---

# 3. BLOCKER C — Raw unsupported generation vs accepted unsupported output

The full Qwen FinQA C8 raw capture contains:

```text
9 / 200 rows with unsupported_claim = true
```

or:

```text
4.5%
```

Inspection shows these examples are contract-invalid/error cases rather than necessarily accepted final outputs.

This exposes a crucial metric distinction.

## Define two separate metrics

### Raw Unsupported Generation Rate

```text
raw_unsupported_generation_rate =
model generations containing unsupported/unregistered material
/
model-invoked cases
```

This measures model behavior.

### Accepted Unsupported Claim Rate

```text
accepted_unsupported_claim_rate =
unsupported claims that survive policy/output validation
/
evaluated cases
```

This measures system safety.

These metrics must never share the label “unsupported claim rate”.

## Required rescoring

For every:

```text
Phi FinQA C1/C8
Phi HaluEval C1/C8
Qwen FinQA C1/C8
Qwen HaluEval C1/C8
D1
```

compute both metrics.

For C8, explicitly prove which of the 9 Qwen FinQA unsupported generations were:

```text
REJECTED
SAFE_PARTIAL
ACCEPTED
```

Publication gate requires:

```text
accepted_unsupported_claim_count_C8 = 0
```

If any unsupported C8 claim reached accepted output, do not patch the metric; investigate and repair the output validator, then rerun only the affected frozen cases.

---

# 4. BLOCKER D — HaluEval semantic accuracy vs end-to-end accepted accuracy

In the Phase-4E Qwen HaluEval C8 results:

```text
semantic prediction accuracy = 50%
contract_validity = 0%
```

All 200 C8 rows have:

```text
contract_valid = false
```

yet semantic predictions are still extracted and scored.

This is useful diagnostically but is **not end-to-end accepted system accuracy**.

## Final external metric separation

For HaluEval report:

### Raw Semantic Accuracy

```text
raw_semantic_accuracy
```

Score the Yes/No decision recoverable from raw model output, regardless of contract validity.

### Contract Validity

```text
contract_validity_rate
```

### Accepted End-to-End Accuracy

```text
accepted_e2e_accuracy =
correct prediction AND valid accepted contract
/
all cases
```

### Safe Rejection Rate

```text
safe_rejection_rate =
invalid/rejected output
/
all cases
```

### Accepted Unsupported Claim Rate

as defined above.

Do not call raw semantic accuracy simply “UIR task accuracy”.

If:

```text
Qwen C8 contract_validity = 0%
```

then its accepted end-to-end accuracy is necessarily 0% unless a deterministic recovery layer explicitly creates a valid accepted output.

This negative result must be preserved.

---

# 5. Validate FinQA task semantics

For FinQA also separate:

```text
raw expression parse success
contract validity
safe execution success
official execution accuracy
accepted answer accuracy
raw unsupported generation
accepted unsupported claim rate
```

Do not count a rejected invalid expression as an accepted unsupported answer.

Likewise, a syntactically valid but numerically wrong verified expression is:
- safe with respect to provenance,
- wrong with respect to task accuracy.

These are distinct dimensions.

---

# 6. Fix Qwen reproducibility provenance

The uploaded Qwen raw files contain:

```text
ollama_model_digest = "unknown"
```

This is insufficient for final reproducibility.

Record one of:

```text
exact Ollama manifest digest
GGUF file SHA-256
local model blob SHA-256
```

plus:

```text
ollama model tag
quantization
context length
temperature
seed
max tokens
Ollama version
```

Create:

```text
results/uir_phase4f/QWEN_MODEL_PROVENANCE.json
```

All 800 Qwen external rows must reference this immutable model identity.

---

# 7. Rebuild the final metric contract

Create:

```text
evaluation/uir_phase4f/METRIC_CONTRACT_PUBLICATION_FINAL.yaml
```

At minimum define:

```text
complete_claim_set_accuracy
supported_answer_coverage
safe_partial_answer_rate
no_verified_answer_rate
conditional_claim_precision
macro_claim_recall

adversarial_attack_success_rate
workload_attack_incidence_rate

raw_unsupported_generation_rate
accepted_unsupported_claim_rate

raw_semantic_accuracy
contract_validity_rate
accepted_e2e_accuracy
safe_rejection_rate

finqa_execution_accuracy
finqa_program_accuracy
finqa_safe_execution_rate
```

Every metric must define:
- numerator,
- denominator,
- eligible cohort,
- meaning,
- whether model-level or system-level.

---

# 8. Re-score all final experiments; do not regenerate existing model outputs

Except for the required D1 N=600 run, do not rerun model generation.

Use existing frozen raw captures.

Create:

```text
evaluation/uir_phase4f/rescore_publication_final.py
```

Input:

```text
Phase-4D/4E raw Phi captures
Phase-4E Qwen raw captures
Phase-4F D1 raw captures
```

Output:

```text
results/uir_phase4f/internal_final.csv
results/uir_phase4f/security_final.csv
results/uir_phase4f/finqa_external_final.csv
results/uir_phase4f/halueval_external_final.csv
results/uir_phase4f/constrained_baseline_final.csv
results/uir_phase4f/external_case_scored_final.jsonl
```

No hand-computed publication metrics.

---

# 9. Correct statistical tests

## Internal complete utility

Primary:

```text
C1 vs C8 complete_claim_set_accuracy
```

Preserve:

```text
p = 0.5
```

if confirmed.

## Supported coverage

Treat as secondary utility endpoint.

Use paired binary McNemar when the per-case endpoint is binary.

Do not use a paired t-test on binary success indicators as the primary test when exact McNemar is available.

Report:
- risk difference,
- 95% CI,
- exact McNemar p-value.

## Security

Use only adversarial cases for primary ASR comparisons.

Report explicit:

```text
N_attack = 50
```

---

# 10. Re-run the publication table generator

Create:

```text
evaluation/uir_phase4f/generate_final_tables.py
```

Required tables:

## Table 1 — Internal safety

Columns:

```text
Pipeline
Accepted Unsupported Claims
Adversarial ASR (N=50)
Invalid Entity FAR
Policy Bypass
```

## Table 2 — Internal utility

Columns:

```text
Pipeline
Complete Accuracy
Supported Coverage
Safe Partial
No Answer
Conditional Precision
Macro Recall
```

## Table 3 — D1 vs C3 vs C8

Must use D1 N=600.

## Table 4 — FinQA cross-model

Distinguish raw model behavior vs accepted result.

## Table 5 — HaluEval cross-model

Columns:

```text
Raw Semantic Accuracy
Contract Validity
Accepted E2E Accuracy
Raw Unsupported Generation
Accepted Unsupported Claims
Safe Rejection
```

This table is necessary to make the Phi/Qwen contract failure scientifically interpretable.

---

# 11. Update scientific narrative

The final paper must make the following distinction explicit:

```text
Model semantic correctness
≠
Contract validity
≠
Accepted system correctness
≠
System safety
```

Example:

A Qwen response may make the correct HaluEval Yes/No judgment but violate the required evidence contract. This is:
- semantically correct at model level,
- invalid at contract level,
- rejected at accepted-system level,
- safe if no unsupported content is accepted.

This separation is one of the strongest conceptual contributions of the paper.

---

# 12. Publication-safe conclusions

Permitted conclusions, if confirmed:

1. UIR does not significantly improve complete internal answer accuracy over Naive RAG on the current 418-case eligible cohort.
2. UIR increases supported-answer coverage by retaining safe partial verified outputs.
3. UIR converts uncertain/invalid generation into rejection rather than silently accepted unsupported output.
4. Grammar-constrained decoding guarantees syntax but does not by itself provide factual authorization or provenance binding.
5. External semantic utility depends strongly on backbone capability and contract-task fit.
6. Under assumptions A1–A5, the acceptance transition is designed so unsupported claims cannot be admitted; finite empirical evaluation separately reports observed accepted unsupported claims.

Avoid:
- universal hallucination elimination,
- arbitrary-domain guarantee,
- “UIR always improves accuracy”,
- “0% unsupported generation” when raw model generations are nonzero.

---

# 13. Final consistency checker v2

Create:

```text
evaluation/uir_phase4f/check_publication_consistency_v2.py
```

It must catch the exact errors missed in Phase 4E.

Required assertions:

```text
D1 total_cases >= 600
D1 commit_eligible_cases == 418

attack table denominator == 50 for adversarial ASR
workload incidence has separate metric name

Qwen FinQA raw rows == 200 per pipeline
Qwen HaluEval raw rows == 200 per pipeline

Qwen HaluEval C8:
    if contract_validity == 0
    accepted_e2e_accuracy cannot be reported as raw semantic accuracy

raw_unsupported_generation_rate != accepted_unsupported_claim_rate
unless numerically and semantically identical

all final report values == generated table values
all generated table values == final CSV values
```

Required result:

```text
0 blockers
0 warnings
```

---

# 14. Final artifacts

Create:

```text
results/uir_phase4f/
├── QWEN_MODEL_PROVENANCE.json
├── METRIC_CONTRACT_PUBLICATION_FINAL.yaml
├── d1_constrained_raw_600.jsonl
├── d1_constrained_summary_600.csv
├── external_case_scored_final.jsonl
├── internal_final.csv
├── security_final.csv
├── finqa_external_final.csv
├── halueval_external_final.csv
├── constrained_baseline_final.csv
├── stat_complete_utility_final.csv
├── stat_supported_coverage_final.csv
├── stat_security_final.csv
├── FINAL_PUBLICATION_CONSISTENCY_V2.md
└── PHASE4F_FINAL_MANIFEST.json
```

Generated manuscript tables:

```text
docs/work_reports/uir_phase4f/generated_tables_final.md
docs/work_reports/uir_phase4f/generated_tables_final.tex
```

Final report:

```text
docs/work_reports/uir_phase4f/
REPORT_PHASE4F_FINAL_METRIC_CLOSURE.md
```

---

# 15. Final publication gate

Required:

```text
all_previous_phases_preserved = true

d1_full_600_complete = true
d1_commit_eligible_n = 418

attack_denominator_separated = true

raw_vs_accepted_unsupported_metrics_separated = true
c8_accepted_unsupported_claim_count = 0

halueval_raw_vs_accepted_accuracy_separated = true

qwen_model_identity_frozen = true

all_external_n_correct = true

complete_vs_partial_utility_correct = true

all_statistics_use_final_metric_contract = true

all_tables_generated_automatically = true

final_consistency_blockers = 0
final_consistency_warnings = 0
```

Expected state:

```text
READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL
```

---

# 16. Stop rule

Once:

```text
READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL
```

is reached:

**STOP ALL DEVELOPMENT.**

No further:
- architecture changes,
- baseline additions,
- model additions,
- new languages,
- new domains,
- policy extensions,
- benchmark tuning.

Proceed immediately to:

```text
final SCI manuscript preview (.md)
→ PI review
→ section-by-section LaTeX
→ reference verification
→ journal formatting/submission
```
