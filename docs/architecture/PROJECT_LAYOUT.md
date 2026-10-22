# UIR shared repository and project layout

## Current ownership policy — 2026-10-21

`uir_base` is the base research project; `uir_security` and `uir_law` are derived
projects. Shared core remains in root `src/`, `crates/`, `protocol/`, `spec/`;
root `docs/` and `scripts/` contain cross-project material only.

```text
projects/<uir_base|uir_security|uir_law>/
  docs/                    project-wide architecture/specifications
  resources/               reusable inputs/assets across milestones
  evaluation/, scripts/    reusable project implementation and runners
  paper/                   local/private manuscript workspace
  results/<task_id>/
    data/                  task-specific data/results
    reports/               task reports
    figures/               plots and pictures
    resources/             task-specific inputs/work orders/assets
    logs/                  execution logs
    manifests/             provenance, hashes and rights
uir/docs/work_reports/<project>/<task_id>/  LOCAL ONLY internal work reports
```

The same pattern applies to all three projects. Root `tests/<project>` may retain
test source; its generated data, technical reports and figures belong to the task.
Owner exception: private work orders, research reviews and internal work reports
remain at root `docs/work_reports/<project>/<task_id>/` in their original location.

Create a fresh task with `python scripts/create_project_task.py uir_base 115_example`
(or `uir_security`, `uir_law`). It refuses overwrite, invalid IDs and symlink paths.
Existing frozen layouts, including T-stage `run_<UTC>`, keep their internal structure.

`docs/work_reports` bundles were restored in place following the owner's clarification;
their bytes are preserved, with a separate reversal receipt. Project papers feature a public
landing page at `paper/README.md`, while drafts are under `paper/current/` or task-local
`manuscript_private`. Historical developmental results reside in `archive/<project>/results/`.
Project-specific docs moved to project `docs/`.
The private task `114_project_layout_2026_10_21` holds old/new paths and SHA-256s.
Frozen content, embedded paths and archive members are unchanged. Historical readers
can explicitly use `uir_common.paths.recorded_path` and must still check original
hashes. No filesystem aliases, fallback copies, source duplication or symlinks exist.
Old evaluator-hash releases may require their pinned source snapshot; moving evidence
does not scientifically recertify it or make changed code match an old source hash.

Only `docs/work_reports/` is blanket-private within root `docs/`; other docs folders
remain public candidates subject to file rights and existing per-file exclusions.
Private work reports remain LOCAL ONLY. New tasks created by the task helper receive
a task-local ignore file; reports, private folders and manuscripts are excluded.
Previously public numerical results remain reviewable as moves, not hidden by a
blanket result-tree ignore. Existing tracked files are not untracked by ignore rules; rights,
staged paths and owner approval must be reviewed before public release. No remote
mutation/history rewrite is implied. This also does not remove previously public history.

## Historical 2026-10-11 description (superseded where paths differ)

The repository owns three projects: `uir_base`, `uir_security`, and `uir_law`.
The organization follows the shared-source/project-boundary principle used by
`dlg_gnn`; it does not move UIR into `dlg_gnn` or introduce a GNN dependency.

```text
uir/
  src/
    llm_trust/             shared historical Python implementation
    uir_common/            domain-neutral reference contracts, paths, local clients
    evaluation/            checkout-only legacy Python import namespace
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
      paper/
        README.md          public paper landing page
        current/           private manuscript workspace; excluded from public Git
      reproduce.sh         project verification/table/test entry point
  archive/
    uir_base/results/      historical base evidence (phases 1-4f, slm)
    uir_security/results/  historical security evaluation rounds
  docs/architecture/       common architectural contracts and provenance
  docs/work_reports/       project reports and work orders (local only)
  tests/                   project-scoped regression tests
  scripts/                 repository-wide maintenance/runtime entry points
  local_storage/           local model weights and caches; excluded from Git
```

The tree shows the repeating project pattern; each project is a separate portal.
The domain-neutral llm_trust/uir_common packages may not import project evaluation,
gold labels or manuscripts. The separate evaluation namespace is a checkout adapter,
not a domain-neutral core component.
Project scripts may depend on shared sources, not the reverse. Rust protocol/core
sources are local workspace members; the checkout no longer requires an adjacent
`hete_sandbox` for those path dependencies. See `RUST_PROVENANCE.md` for their origin.

## Compatibility and historical evidence

Sources and evidence have one canonical physical location. Root package copies,
symbolic-link aliases and legacy filesystem compatibility directories are prohibited.
Use `projects/<project>/evaluation` and `projects/<project>/results`; historical base
results are under `archive/uir_base/results`. After moving a repository, reinstall
its editable package and update path consumers rather than recreating old paths.

New code should import `projects.<project>.evaluation.<module>`. The small
`src/evaluation/__init__.py` adapter resolves historical flat and project-qualified
Python import names directly to the real project source directories. It contains
no duplicated evaluation implementations and creates no filesystem links. This keeps
the SHA-pinned historical evaluator/reviewer code unchanged while resolving its
imports in the new checkout. The old link-based migration script is retired and
cannot run a migration.

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
python -m pip install --no-deps --no-build-isolation -e .
python -m pytest -q
cargo test --workspace
bash projects/uir_base/reproduce.sh verify
bash projects/uir_security/reproduce.sh verify
bash projects/uir_law/reproduce.sh verify
```

`verify` checks recorded source integrity, not scientific validity or submission
approval. `tables` regenerates independent revision tables/replay diagnostics;
it does not silently claim a fresh model experiment. Security and law portals do
not imply that those projects have been experimentally revalidated by base work.
