# FinQA development decomposition

The original 800 raw outputs/scores remain immutable. A non-end-anchored marker
diagnostic classifies completed literals versus ambiguity; it does not change
the primary score or automatically divide a displayed percent by 100.

New typed programs consist of bounded steps/operator/operand-reference ASTs,
never description prose. Numeric source refs carry declared units. Unknown units
fail rather than silently match; percent operands normalize to dimensionless
fractions, and display/executable-answer units remain distinct evaluation fields.
Cross-unit addition, missing source refs, forward refs, zero division, Boolean
numeric reuse, unsafe exponentiation and oversized programs fail explicitly.

Eleven fixtures expand official/custom parity to exponentiation, percentages and
explicit table aggregates. This is parity on a declared typed operand domain,
not full FinQA compatibility. Native report-wide unit inference and semantic
operand selection have not been implemented/evaluated as general competence.

For 400 previously used cases, lexical top-context and full authoritative document
number presence are separately checked using scoring-only program literals.
Presence is necessary but not sufficient for correct semantics/unit binding.
Remaining index/document/company availability is audited; template-family
independence is unverified and no new FinQA confirmatory inference is claimed.
