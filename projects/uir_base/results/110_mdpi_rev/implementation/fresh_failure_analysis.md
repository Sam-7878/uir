# Frozen negative findings and post-hoc diagnostics

Matched output-layer inference: 272 actual Phi calls; 251 stop and 21 length.
The five-required-field schema / seven-bound-field scorer mismatch prevents a
clean model/IR contribution estimate. Keep raw candidates and all primary metrics.

New FinQA execution: 800 actual requests (200 cases × two models × two conditions).
The strict adapter-defined end-to-end counts are Phi C1 4/200, Phi C8 0/200,
Qwen3-1.7B C1 1/200, Qwen3-1.7B C8 0/200. They are **not isolated reasoning
accuracy**, hallucination rates, or a fair causal benefit estimate for typed IR.
The C8 condition is the custom bounded arithmetic adapter, not a silent rerun of
the historical full C8/B6 architecture.

Post-hoc diagnostics preserve the primary metrics: 64 responses contain an answer
marker somewhere but fail the end-anchored native adapter. Displayed percentage
versus benchmark executable-answer units can further confound interpretation.
Of 400 C8 requests, the program diagnostics record 385 unsupported-operator/step
failures, 13 missing/resource-limit failures and two syntactically executable
programs. JSON string validity does not force an arithmetic program: many outputs
describe operations in prose. Truncation is assigned only from recorded finish
reason, not inferred from a malformed JSON response.

The full-source expressibility audit covers 172/200 gold programs. It is
evaluation-only and does not prove that question-only lexical retrieval exposed
all operands. The 200 new indices are distinct, but 71 documents and 180 companies
overlap historical development. Unsupported factual claim rates remain
NOT_MEASURED. Do not convert rejection or missing extraction into zero error.

Before further confirmatory inference: on declared development data align all
required schema/scorer fields, freeze percent/unit interpretation, require the
actual DSL grammar and its valid examples, and compare input/representation layers
with identical accessible information. Any resulting confirmatory evaluation needs
a new protocol version and genuinely unused holdout; do not silently re-score this
holdout to select the most favorable interpretation.
