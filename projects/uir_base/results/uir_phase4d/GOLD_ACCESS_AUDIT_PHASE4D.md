# Phase UIR-4D Gold Access & Label Leakage Audit

Generated: 2026-10-11T12:01:46.649612+00:00

## Audit Result

`status = PASS`
- `gold_derived_runtime_decision_fields = 0`
- `forbidden_generation_gold_access = 0`
- `total_runtime_rows_checked = 1100`

## Prohibited Runtime Fields Verified Absent

- `attack_goal`: ZERO instances found across all runtime files
- `category`: ZERO instances found across all runtime files
- `entity_valid`: ZERO instances found across all runtime files
- `exe_ans`: ZERO instances found across all runtime files
- `expected_claims`: ZERO instances found across all runtime files
- `expected_outcome`: ZERO instances found across all runtime files
- `expected_policy_decision`: ZERO instances found across all runtime files
- `gold`: ZERO instances found across all runtime files
- `gold_judgement`: ZERO instances found across all runtime files
- `gold_program`: ZERO instances found across all runtime files
- `hallucinated_answer`: ZERO instances found across all runtime files
- `is_adversarial`: ZERO instances found across all runtime files
- `is_invalid_entity`: ZERO instances found across all runtime files
- `is_policy_violation`: ZERO instances found across all runtime files
- `policy_valid`: ZERO instances found across all runtime files
- `qa.program`: ZERO instances found across all runtime files
- `required_claims`: ZERO instances found across all runtime files
- `right_answer`: ZERO instances found across all runtime files
- `runtime_entity_exists`: ZERO instances found across all runtime files
- `runtime_policy_permit`: ZERO instances found across all runtime files
- `runtime_uir_compiles`: ZERO instances found across all runtime files
- `split`: ZERO instances found across all runtime files
- `stratum`: ZERO instances found across all runtime files
- `uir_ready`: ZERO instances found across all runtime files

## Segregation Verification

- `strong_runtime_600.jsonl`: ONLY observable user queries, canonical text, context claims, and IDs.
- `strong_scoring_600.jsonl`: Contains ground-truth stratum, expected claims, expected outcomes, and behavioral attack goals.
- `finqa_runtime_200.jsonl`: Contains question, pre_text, post_text, and table. No gold programs or answers.
- `finqa_scoring_200.jsonl`: Contains gold program and exe_ans for evaluation only.
- `halueval_qa_runtime_200.jsonl`: Contains knowledge, question, candidate answer. No hallucination indicator.
- `halueval_qa_scoring_200.jsonl`: Contains gold judgement (Yes/No) and reference answers.

## Findings
- Zero leakage findings detected. All runtime datasets are strictly sanitized.
