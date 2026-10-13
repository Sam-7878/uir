# Matched comparison: execution and limits

The machine-authoritative pre-execution protocol is
`projects/uir_base/results/mdpi_next_2026_10_11_v2/fresh_matched_protocol.json`.
Its runner, analysis and family-map hashes are frozen independently of the later
handoff scripts. Historical C5 replay is a separate counterfactual experiment:
600 stage records, 498 original model invocations, 226 pre-execution exclusions
from the 272-case common gate, and no new model calls. All original candidates
are additionally projected without selecting by C8 success.

The new output-layer development experiment has 600 requests, 418 eligible utility
cases and 272 actual local Phi calls. Four conditions share runtime facts and
policy: trusted deterministic template, syntax-constrained SLM, exact-key
projection and partial-off projection. Temperature 0, seed 20261012, context 8192,
visible generation limit 512, retry 0, local GGUF Q4_0 on RTX3090 are captured.
Six exploratory endpoint comparisons retain case pairs within recorded families.

**Design limitation:** the inherited syntax schema requires five fields whereas
the exact scorer binds seven. Period is omitted in 249 candidate cases and unit
in 118 (nonexclusive); 21 calls end at the generation limit. These are observable
configuration failures, not an unbiased causal estimate of SLM or UIR benefit.
The deterministic control's better completeness is retained. Projection rejection
is not evidence that an answer was useful.

The input/representation-layer comparison (raw-only / trusted-slot / no typed IR
with equivalent policy and validation) remains NOT_EXECUTED. Restricted parser
conformance must not substitute for that comparison. A future syntax/fact-binding
comparison must use a new declared development protocol and data selection, not
rewrite these frozen results. Historical replay, raw-only conformance and fresh
model inference remain separate evidence kinds.
