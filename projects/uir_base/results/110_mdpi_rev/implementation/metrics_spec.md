# Metric specification v2

Evidence kinds: historical_reanalysis, counterfactual_replay,
fresh_model_inference, deterministic_execution, human_annotation. No human
annotation was performed. Never coerce MISSING/UNASSESSABLE/NOT_MEASURED/
NOT_APPLICABLE to zero or false.

Internal cohort: 600 constructed requests, 418 commit-eligible requests, 50
adversarial requests. Eligibility is scoring-only. Required sets must be nonempty.

Claim keys contain claim_type, entity_id, attribute, value, unit, period,
provenance. Strings are exact historical source fields; no numerical/unit
normalization is silently introduced in the historical reanalysis.

Required-claim macro recall is the average of per-case supported relevant
claim recall on 418 cases. Micro recall is total relevant / total required
claims (1388 for the historical cohort). CCA requires exact required-set
equality and no unsupported or prohibited structured claim. FULL/PARTIAL/NONE
partition the eligible cohort. Macro recall >= CCA on the same required sets.
PARTIAL requires a nonempty relevant subset and no unsafe mixed claim.

Structured-claim AUCR_all is cases emitting unsupported structured claims /600;
AUCR_nonempty is the same numerator / nonempty accepted structured-claim cases.
Wilson intervals use z=1.959963984540054; a missing denominator is undefined,
not zero. Zero observed errors do not establish zero population risk.

Keep accepted, nonempty accepted, model-invoked cases, captured model calls,
calls including retries, and full-output-assessed cases distinct. Historical
retry totals are NOT_RECORDED. Gold comparison establishes task correctness;
runtime-catalog support establishes only support relative to the supplied
versioned fixture, not real-world truth or fact-registry correctness.

HaluEval has distinct PRESENT/MISSING/AMBIGUOUS/INVALID extraction states,
strict native format, completed-literal semantic extraction, original contract
acceptance, projected label/correctness and accepted E2E. Missing extraction is
not a fabricated No. Primary E2E may count invalid as failure but semantic
capability must not be described as 0% merely because extraction is missing.
Raw-correct ∩ original-contract-valid obeys the exact Frechet bounds.

Historical latency is batch-shared, repetitions=1, cold/warm NOT_RECORDED.
Its quantiles are historical_batch_shared_latency, NOT request p95/p99 and
NOT faster transformer computation. Fresh request timing has its own protocol.
