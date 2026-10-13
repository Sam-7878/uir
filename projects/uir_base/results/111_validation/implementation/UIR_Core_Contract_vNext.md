# Core and implemented scope

The serialized artifact has metadata, canonical semantic fields/predicate,
policy constraints, execution contract, output contract and semantic digest.
Entity/attribute/period/unit, predicate, action and policy/evidence versions define
identity. Raw language, case ID and audit timing do not. NFC/RFC8785 SHA-256 is
inherited from the shared contract implementation. Supported AND/OR flattening and
sorting are canonical CNL normalization, not arbitrary theorem proving.

Korean/English CNL and authenticated assisted slots can construct the same typed
request. Two backend input formats (fact-ID and seven-field claims) share one
validator/renderer. Backend conformance is therefore common-verifier composition,
not independent implementations of a prover or a language-model accuracy test.

A capability-equivalent specialized structured dict removes public shared artifact
serialization, but retains the lexical parser/policy/support checker. Existing
systems also have intermediate structures; the baseline is not artificially
unstructured or weaker. Equal finite-case behavior is expected and preserved.

Implemented: typed request, snapshot identity, finite conditions, exact reference
support, dependency-safe rejection, deterministic approved output, finite sandbox
read/write. Not established: arbitrary NL meaning, new domains/languages,
registry truth, independent human semantics, adaptive model security, human
development-effort savings, completeness, or general performance superiority.
