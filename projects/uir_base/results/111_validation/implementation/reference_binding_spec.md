# vNext claim and identity contracts

All full generated claim objects require claim_type, entity_id, attribute, value,
unit, period and provenance as strings. Exact seven-field support is required;
numeric/derived claims reject omitted/null/empty/unknown unit or period. Empty
unit/period in nonnumeric metadata claims explicitly mean not applicable, never
a wildcard matching a numeric unknown.

Generic reference candidates name catalog IDs only plus the v1 identity field.
Only server-owned authoritative values can be rendered. Model prose/additional
keys, unknown references and duplicate IDs cannot increase authority.

Development renderer v1 asks the model to copy the digest. It exposes both random
digest copying failures and entity-name/fact-ID confusion. v1 is preserved.
Development v2 removes generated authority metadata: a trusted synchronous
request envelope supplies the digest, and each request's public authorized catalog
IDs form a schema enum. This is explicitly a stronger reference-binding condition,
not syntax-only decoding and not a unique benefit of the shared UIR. Both UIR and
equivalent specialized pipelines can use this same binding method.

Dependency closure is required for derived facts. Operands must match entity/period
authority and values/units are recomputed using the bounded arithmetic definition.
Missing denominators, cycles, mismatched operands and invalid arithmetic quarantine
or remove the dependent conclusion. The trusted registry remains an assumption;
this is not full W3C PROV serialization or independent real-world truth.
