# HETE security reinforcement V4: implementation and claim boundary

This is a new research specification. UIR-v2 is the historical security representation;
UIR-Core Typed IR v0.1 is the shared evolving architecture; V3.2 and V4 identify
evaluation protocols. No representation migration is implied by an evaluation label.
HETE expands to **Heterogeneous Entity Trust Extension** in the existing architecture.

The implementation under `evaluation/scie_v4/` is a small mechanism study and local
AgentDojo adapter, not a production replacement for the V3.2 evaluated pipeline.
Task-specific protocols, evidence, reports and figures are in
`results/scie_acceptance_2026_10_21_v4/`.

## Trusted transitions

1. An authenticated application creates an immutable session with principal,
   capabilities, permitted evidence IDs, confidential fixture labels, revision and
   resource budget. Models and retrieved text cannot construct this authority.
2. The model proposes a JSON value. A whole-document decoder rejects duplicates,
   non-finite values, unexpected fields and invalid revision types.
3. Admission checks principal, tool registry, capability and argument scope.
4. Dispatch checks the current revision and permission again. A replayed nonce is
   rejected. SQLite uniqueness is an additional masking control.
5. A transaction commits report/action state atomically. Any SQL failure rolls back
   both effects and leaves revision unchanged. This is a local SQLite property,
   not a distributed transaction or external API rollback guarantee.
6. Egress requires a separate output contract. V4 exact-token DLP failed an encoded
   summary attack. V4.1 is a separately versioned narrow-contract repair: it rejects
   unverified fields and emits a canonical verified numeric fixture record.

## I1–I4

| Invariant | Preconditions | Concrete enforcement | Failure oracle |
|---|---|---|---|
| I1 capability monotonicity | application session authenticated and immutable | caller-supplied frozen capability set; principal check; independent dispatch check | unauthorized executor invocation or committed effect |
| I2 taint non-attenuation | all external/model text enters as data | model proposal cannot update Session; no automatic declassification | proposal changes a trusted grant or releases a confidential field |
| I3 evidence admission | trusted signer and binding assumptions hold | admitted evidence IDs and numeric claim contract | unsupported citation/quantity accepted |
| I4 output non-authority | dispatcher/egress are the only effect boundaries | tool admission, revision check, atomic commit and output validator | forbidden write or protected egress |

Taint propagation in the shared historical UIR implementation is covered by its
existing regression suite. The new `Session` mechanism is immutable authority
separation; it is not a complete generic information-flow type system. An explicit
declassification operation is absent: no model proposal may request one. Trusted
evidence endorsement must originate outside the model. Production endorsement,
key rotation and credential revocation are assumptions, not implemented guarantees.

## Evidence and authenticity

Hash validity establishes correspondence to bytes, not truth, authorship, freshness,
or absence of injected instructions. The historical public HMAC fixture key tests
binding logic and cannot establish authenticity against an adversary who knows that
key. A deployment needs protected signer keys, signed principal grants, expiry,
rotation/revocation, anti-rollback state, compromised-source analysis and a separately
trusted evidence curator. Numeric fixture verification does not validate arbitrary
natural-language facts.

## Audit scope

The task retains per-case proposals, admission, execution, mutations, egress and
policy decisions. SHA-256 manifests anchor byte integrity. Unkeyed hashes alone do
not establish tamper evidence against a writer able to replace the log and manifest.
The implementation does not claim WORM storage, an externally witnessed append-only
log, signed audit events, or universal attack resistance.
