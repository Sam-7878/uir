# HETE security reference interpreter V4.2

This Python application security IR is distinct from UIR-Core wire/Rust equivalence.
Source: `../evaluation/scie_v4_2/typed_engine.py`; historical V4 contracts remain.
Application-owned TrustedSession, Capability, PolicyRevision and Budget cannot be
issued by tool text. Signed/scoped EvidenceRef binds endorsed bytes, not general
truth. Untrusted JSON becomes ProposedAction; successful checks yield a proof-bound
ApprovedAction. Dispatch rechecks principal, ownership, approval, revision, evidence
revocation, nonce and budget before effects. AuditEvent links proposal, approval and
execution. Host/issuer/key service, executor and sole output boundary remain trusted.

MinimalGuard checks the same application predicate. V4.2 external results have equal
security and utility, so typing is an explicit architecture/audit structure rather
than demonstrated incremental security. Numeric CanonicalOutput excludes arbitrary
prose with a measured functionality cost. External task text has no general semantic
confidentiality guarantee. SQLite and post-call quota checks do not establish
distributed atomicity or hard streaming cancellation.

Versioned evidence/current manuscripts are in
`../results/hete_electronics_v4_2_2026_10_21/`: schemas, model/source digests, tasks,
protocol amendments, original failures, missing responses, case-level claim maps
and scoped assumptions. Publication/data/code release require actual signed
author/institutional decisions.
