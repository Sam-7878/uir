# POA UIR Research Contract

## Scope

`poa-uir` defines a language-independent, policy-evaluable execution contract for controlled multilingual research inputs. It does not add domain semantics to `poa-core`, and it does not treat the renderer or an SLM as a policy authority.

## Contract layers

1. `metadata`: traceability fields, source language/hash, compiler version, and domain label.
2. `semantics`: intent, domain-neutral target, action, parameters, conditions, and temporal scope.
3. `policy_constraints`: L0–L3 constraints represented with a typed condition AST and enforcement action.
4. `execution_contract`: required capabilities/resources, allowed operations, provenance, failure behavior, and execution mode.
5. `output_contract`: permitted claim types, provenance/numeric requirements, external-inference rule, and unsupported-claim behavior.

The normative JSON shape is `protocol/schemas/uir.schema.json`.

## Processing order

```text
normalize/security gate -> language frontend -> UniversalIr
-> structural/semantic validation -> EffectivePolicy evaluation
-> AACO outcome mapping -> verified execution -> renderer
-> structured output validation -> audit evidence
```

Reject and Quarantine outcomes do not enter the executor or renderer. A renderer cannot change a lexer-owned entity identifier. Output validation compares structured claims with a `VerifiedFactSet`; prose keyword overlap is not evidence.

## Digests

- `uir_digest`: digest of the entire canonical UIR.
- `semantic_digest`: digest of the semantic contract view. It excludes `request_id`, `source_language`, `source_hash`, and `created_at`.
- `policy_digest`: supplied by `poa-protocol::policy_digest(EffectivePolicy)`.

Canonical bytes reuse `poa-protocol::canonicalize_value` and SHA-256.

## Outcome mapping

| Condition | AACO outcome |
|---|---|
| Schema/type/authorization/entity failure | Reject |
| Risk threshold or explicit quarantine | Quarantine |
| Internal mutation failure | Abort |
| All preconditions satisfied | Commit |

## Research limitations

The KO/EN frontends implement deterministic controlled language, not general NLP. The fixture executor and mock renderer provide reproducible CI evidence. A future local SLM or GAT/XBRL backend must implement the existing renderer/executor interfaces and remains subject to the same output contract.
