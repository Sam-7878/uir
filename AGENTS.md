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
