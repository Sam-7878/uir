# UIR shared repository and project layout

The repository owns three projects: `uir_base`, `uir_security`, and `uir_law`.
The organization follows the shared-source/project-boundary principle used by
`dlg_gnn`; it does not move UIR into `dlg_gnn` or introduce a GNN dependency.

```text
uir/
  src/
    llm_trust/             shared historical Python implementation
    uir_common/            domain-neutral reference contracts, paths, local clients
  crates/                 self-contained Rust workspace
  protocol/               schemas, protocol fixtures and examples
  projects/
    uir_base/              financial groundedness/utility research
    uir_security/          cybersecurity/zero-trust research
    uir_law/               legal-domain research
      evaluation/          project-specific evaluation sources/configuration
      scripts/             project orchestration and experiment entry points
      results/             current evidence and project result entry points
      reports/             project reporting entry points
      paper/current/       private manuscript workspace; excluded from public Git
      reproduce.sh         project verification/table/test entry point
  archive/uir_base/results/ historical base evidence, not overwritten by revision
  docs/architecture/       common architectural contracts and provenance
  docs/work_reports/       project reports and work orders
  docs/papers/             unchanged legacy private manuscripts
  tests/                  project-scoped regression tests
  scripts/                repository-wide maintenance/runtime entry points
  local_storage/          local model weights and caches; excluded from Git
```

The tree shows the repeating project pattern; each project is a separate portal.
Shared sources may not import project evaluation, gold labels or manuscripts.
Project scripts may depend on shared sources, not the reverse. Rust protocol/core
sources are local workspace members; the checkout no longer requires an adjacent
`hete_sandbox` for those path dependencies. See `RUST_PROVENANCE.md` for their origin.

## Compatibility and historical evidence

Root `llm_trust`, grouped `evaluation/<project>` and `results/<project>`, and flat
legacy evaluation/result entry points remain symlink aliases. They are not separate
copies of data. Run from a symlink-capable Ubuntu checkout; do not treat Windows
symlink text files as working Python packages.

The migration manifest under the `107_Astra_review` work report maps old paths to
new paths with byte hashes. Historical non-Python evidence is preserved; mechanical
repository-root lookup changes in Python are separately identified. Revision
results live in a new result directory and must not overwrite old inference logs.
Moving files or preserving hashes does not independently validate their annotation
or experimental methodology.

## Public versus local/private files

Public release candidates include source, tests, schemas, environment/reproduction
instructions, provenance manifests and permitted raw case-level evidence. Manuscript
sources/assets, credentials, Python environments, build caches, model weights and
unapproved legal corpora are excluded. `.gitignore` alone does not remove files
already tracked; inspect the staged/released file list before a public push. No
remote publication is implied by this organization.

Model installation manifests and operational smoke outputs are evidence artifacts;
weights are not. AI reviewer labels belong under `uir_base/results/.../ai_reviews`,
never in human annotation files. The local AI-review protocol explicitly distinguishes
AI capture from human validation and publication readiness.

## Execution

For this host use `/mnt/d/_Work/goat_bank/.venv_cuda`; exact runtime and GPU/model
settings must be captured per experiment. A local-model launch script selects RTX
3090 by UUID and isolates its Ollama port from the existing system service. It is a
host-specific launcher, not a promise that the same GPU UUID exists on another host.

```bash
source /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate
cd /mnt/d/_Work/goat_bank/uir
python -m pytest -q
cargo test --workspace
bash projects/uir_base/reproduce.sh verify
bash projects/uir_base/reproduce.sh tables
```

`verify` checks recorded source integrity, not scientific validity or submission
approval. `tables` regenerates independent revision tables/replay diagnostics;
it does not silently claim a fresh model experiment. Security and law portals do
not imply that those projects have been experimentally revalidated by base work.
