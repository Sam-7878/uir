# Repository path policy

- Do not create symbolic links or link-based compatibility directories in this repository.
- The only source location for the shared Python package is `src/llm_trust/`.
  Keep the import name `llm_trust`; do not create a root `llm_trust/` copy or shim.
- When relocating folders, update package configuration, path consumers, tests,
  and current architecture documentation instead of preserving old paths with links.
- Install shared Python code using `pyproject.toml`. After moving the repository,
  reinstall the editable package from its new location.
- Use the Ubuntu Python environment specified by the parent `dev_env.md`;
  currently this is `/mnt/d/_Work/goat_bank/.venv_cuda`.
- Preserve source bytes when performing a layout-only move. Do not rewrite
  frozen results, historical manifests, or paper sources just to update old paths.
- Missing frozen inputs must be reported as missing. Do not weaken tests,
  fabricate replacement evidence, or allow empty source scans to pass silently.
- Root directories contain only cross-project infrastructure and documentation.
  `uir_base` is the base research project; `uir_law` and `uir_security` are derived
  projects. Shared core must not import project evaluation or gold.
- Project-wide sources, specifications, reusable resources and manuscript workspaces
  belong to `projects/<project>/`. Put task-specific data, reports, figures, logs,
  resources under `projects/<project>/results/<task_id>/`.
- Owner exception: private work orders, internal reviews and work reports remain
  at `docs/work_reports/<project>/<task_id>/` in their original location, LOCAL ONLY.
  Other root `docs/` folders are not blanket-private; evaluate file rights normally.
  Do not move work_reports into project results. Do not create root manuscript copies.
- New task outputs default to local-only. Preserve frozen file contents during
  relocation and record old/new paths and hashes externally; never edit old
  manifests merely to make a historical path current. Use explicit recorded-path
  translation in readers, not filesystem aliases or silent missing-input fallback.
