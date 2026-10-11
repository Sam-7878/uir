# Rust core provenance

`crates/poa-core` and `crates/poa-protocol` were copied byte-for-byte from
the corresponding `hete_sandbox/crates` directories on 2026-10-11 to remove
out-of-checkout path dependencies. Their sources and package versions were
not changed. The UIR workspace now owns these reusable components; shared
Rust components must not import project evaluators or manuscript generators.
No change was made to the original hete_sandbox repository.

Workspace licensing remains MIT OR Apache-2.0, as declared by the source workspace.
This is source provenance, not a claim of an independently issued release.
