# Canonicalization v2

The reference contract uses RFC 8785 through the installed rfc8785 library,
recursive NFC normalization, SHA-256 and collision rejection for normalized keys.
Condition decimal literals are finite exact normalized decimal STRINGS, not
unbounded binary float literals. The language, raw source text, case ID and
timing are not in the semantic digest. Schema version, input route, unit,
contract policy/evidence snapshots, system constraints and typed user AST are.
Metadata excluded from a digest remains separately recorded in capture manifests.

Equal digest means equal canonical serialization, not proof of semantic
preservation. The bilingual conformance suite supplies explicit synthetic AST
expectations and negation/parentheses counterexamples. It is not human semantic gold.
