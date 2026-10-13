# Reviewer rubric v2 — executed, not human validation

The original 120 cases / 240 raw responses are preserved. The new protocol adds
separate labels for request ambiguity, reviewer epistemic uncertainty, candidate
presence, evaluability, user-condition presence/preservation, finite-rule policy,
entity recognition and evidence availability. Missing candidates require
NOT_EVALUABLE slot/condition labels rather than a forced correct/incorrect label.
System provenance constraints are not treated as user predicates.

Sixteen constructed calibration cases and sixteen lexical-shift holdout cases
were each reviewed once by Qwen3-4B Instruct 2507 and Ministral 3 14B. Expected
fixture labels are scoring-only; they are not human gold. Calibration and holdout
raw responses, confusion matrices, accuracy, agreement and uncertainty are in
`projects/uir_base/results/mdpi_next_2026_10_11_v2/ai_review_v2/`.

All 64 responses satisfy the response schema, but every one of the 16 calibration
and 16 holdout cases remains unresolved in at least one field. In particular,
absent-candidate and policy judgments remain unreliable. No tie is adjudicated
by the same two models, no high-kappa stopping rule was used, and no original
case was tuned until agreement. Some calibration/holdout templates and context
variants share lexical structure: this is not independent-family semantic gold.

The calibration attempt is complete as an experiment but **does not establish a
calibrated semantic assessor**. Under user-approved route B, these labels are
supplementary only. Original W08 remains NOT_SATISFIED; human labels and author/
institution approvals have not been generated.
