# Runtime/evaluator boundary

RawRequest is the original input plus authenticated runtime context.
TrustedSlotInput is requested_entity/attribute/period supplied by the historical
fixture. The old assisted compiler and its 99 OK /21 missing-slot review packets
are NOT a free-NL parser experiment. RuntimeContractRequirements arise only from
runtime facts, policy snapshots and supported raw-only CNL parsing.
EvaluationGold (required sets, outcomes, strata, attacks) is scoring-only.

`next_runtime_worker.py` starts a fresh `python -I` interpreter with a
runtime-only stdin JSON payload. Recursive field rejection refuses nested gold
fields. A CPython audit hook denies gold/scoring/human-label file opens. Tests
cover explicit forbidden file access, nested payload poisoning and counterfactual
gold replacement: deterministic runtime output stays equal while scorer changes.
No inherited parent Python objects or scorer closures enter the worker.

This is not an OS sandbox: malicious native code, audit-hook bypass, adversarial
file descriptors, host compromise, shared memory, registry compromise and
arbitrary child tools are outside its guarantees. Environment filtering is
tested for the isolated worker. A native OpenBSD/OS confinement claim is not
made by these Ubuntu tests.

In the fresh matched runner gold is loaded only after all 600 runtime candidates
are captured. Runtime fact selection uses the supplied fact catalog, actual
entity registry, actual policy and compiler; it never uses expected_claims.
Inputs are trusted-slot assisted and constructed, not prospective user requests.

Data flow: raw/context -> frontend -> policy/entity gate -> version-bound
catalog -> optional generator candidate -> guard/projection -> user output;
runtime capture -> SEPARATE scorer + EvaluationGold -> metric tables.
