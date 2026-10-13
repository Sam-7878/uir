# Operational semantics

The implementation is the restricted CNL in grammar.ebnf, not unrestricted
Korean/English NLU. It preserves typed NOT/AND/OR/comparisons, parentheses,
IF/ONLY IF/UNLESS, one year and optional unit. Korean 조건: has IF semantics;
NOT is explicit 아님. Other Korean conditional paraphrases require clarification.
User conditions and default verified_provenance are separate fields.

Evaluation requires observable typed inputs; missing inputs do not default true.
Units/period/operand IDs of the existing bounded arithmetic DAG are checked by
`uir_common.contracts.derive`, with maximum depth 8/nodes 32, same-period binding,
unit checks, zero-division/overflow rejection and ROUND_HALF_EVEN. This reference
arithmetic is not the official FinQA evaluator.

Priority: stale snapshot or quarantine > compiler clarification > policy deny >
approval pending > write blocked by read-only > no verified answer > complete >
partial (unless disabled). See executable transition tests. Policy and evidence
snapshot versions are bound into the execution contract. A changed decision-
execution snapshot quarantines the in-memory sandbox action.

Resolution identifies records, relevance selects authorized requested facts,
authorization enforces policy/snapshot, provenance binds values to the provided
registry. Fact-ID equality alone is neither entailment nor real-world truth.
The six sandbox conformance traces are actual in-memory read/write opportunities,
not real institution actions or a new injection attack benchmark.
