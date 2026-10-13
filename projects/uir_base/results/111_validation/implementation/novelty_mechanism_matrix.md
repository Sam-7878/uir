# Mechanisms and measured contribution

| Axis | Specified/implemented | Unit verified | Matched empirical scope | Not established |
|---|---|---|---|---|
| Multilingual normalization | Restricted KO/EN CNL + canonical AST | 12 minimum pairs | 144 synthetic requests across input modes | free-NL/human accuracy |
| Typed policy/evidence contract | Public serialized artifact, snapshot/digest identity | field/identity/snapshot negatives | equivalent-specialized has same finite behavior | accuracy superiority from IR alone |
| Derived evidence | bounded recomputation and dependency closure | denominator/unit/period/entity/cycle errors | finite constructed traces | open-world truth/full PROV compliance |
| Backend-independent acceptance | ID and seven-field candidates share guard | same authorization/accepted sets | 192 matching backend comparisons | independent prover or arbitrary backend support |
| Safe partial | dependent conclusion removed if operand absent | FULL/PARTIAL/NONE/partial-off | synthetic graph traces | unassessed native prose safety |
| Composition/reuse | same verifier used by two CNL frontends/API and two candidate formats | serialized roundtrip | public artifact reuse demonstrated | human implementation effort or maintainability savings |

Primary related work: [MLIR interfaces](https://mlir.llvm.org/docs/Interfaces/)
formalize reuse of analyses across different operation semantics;
[LMQL constraints](https://lmql.ai/docs/latest/language/constraints.html) guide
generation through explicit constraints. These precedents rule out “first IR”
or “first constrained generation” claims.

[CaMeL v2](https://arxiv.org/html/2503.18813v2) separates control from untrusted data,
and [AgentSpec](https://cposkitt.github.io/files/publications/agentspec_llm_enforcement_icse26.pdf)
specifies runtime constraints. They are related mechanisms, not formally
reproduced baselines in this experiment. [PROV-DM](https://www.w3.org/TR/prov-dm/)
provides interoperable provenance structures; our catalog IDs/dependency checks
are not a complete PROV implementation or proof of asserted facts' truth.

The bounded candidate contribution is the inspectable composition of semantic,
snapshot, policy, candidate and accepted-output contracts. New matched results
support finite conformance and reuse, not superior reasoning or unique safety
that an equivalent specialized validator cannot provide.
