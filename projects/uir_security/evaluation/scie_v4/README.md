# HETE SCIE reinforcement V4

Research entry points for the 2026-10-21 acceptance work order. Run modules from
the UIR repository root with the parent `.venv_cuda` Python. Task evidence is kept
separately under `projects/uir_security/results/scie_acceptance_2026_10_21_v4/`.
The frozen V3.2 inputs are never rewritten by these tools.

- `audit_v32`, `recover_snapshot`, `export_evidence`: historical byte/count audit,
  explicit hash-matching recovery overlay, tokenized score projection.
- `model_substitution`, `full_pipeline_replacement`, `adaptive_boundary`,
  `outer_boundary`: finite mechanism experiments, retained encoded-leak findings
  and separately versioned narrow V4.1 contracts.
- `agentdojo_adapter`, `benchmark_analysis`: actual official-environment pilot
  with a local JSON agent and matched minimal/typed read-only policies.
- `ai_review`: two blinded local AI raters; `human_validation` is always false.
- `phi_dev_probe`, `no_llm_control`, `stats_analysis`: explicitly scoped
  development and post-hoc controls; no replacement of adverse original results.
- `integration_demo`, `property_suite`: actual local SQLite effects and finite
  adversarial properties. No production key rotation or general compiler proof.
- `references`, `citation_metadata`, `manuscript`, `build_manuscripts`,
  `claim_audit`: verified source records, new manuscript drafts and numeric checks.
- `package_delivery`, `validate_bundles`, `release_verify`, `finish_reports`:
  local archives, extracted-source builds, scoped verification and gate reports.

Protocol JSONs register datasets, model/policy/source identities before inference.
Existing inference IDs resume without erasing failures. Do not change a frozen
protocol to force a rerun; create a new version. The persistent integration demo
refuses to overwrite its state. The original full manifest audit intentionally
fails when old bytecode/source bytes no longer match; scoped recovery must remain
an explicit separate receipt. Publication requires author and release decisions.
