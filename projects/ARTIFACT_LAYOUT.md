# Project Artifact Layout

The `uir` repository organizes research assets into a **Two-Tier System**, consistent with the organizational model of `dlg_gnn`:

1. **Tier 1 (`projects/<project>/`)**: Active, reviewer-facing portals containing active revision evidence, canonical reports, verified results, and reproduction facades.
2. **Tier 2 (`archive/<project>/`)**: Historical archive containing legacy phases, developmental evaluation data, superseded rounds, and audit logs.
3. **Core Library (`src/`, `crates/`, `protocol/`)**: Reusable domain-neutral execution contracts, capability guards, schemas, and Rust kernel.

---

## Layout and Ownership Mapping

| Previous Location | Role & Contents | Reorganized Location / Disposition |
|---|---|---|
| `projects/uir_base/results/uir_phase3`–`4f`, `uir_slm`, `uir` | Historical UIR base phases 1–4f and SLM runs | `archive/uir_base/results/` (Historical Tier 2 archive) |
| `projects/uir_security/results/llm_security_v1`–`v3_1`, preclosure/incomplete runs | Historical security benchmark rounds and interrupted runs | `archive/uir_security/results/` (Historical Tier 2 archive) |
| `projects/uir_base/results/mdpi_revision_2026_10_11/` | Base MDPI revision canonical evidence and manifests | `projects/uir_base/results/mdpi_revision_2026_10_11/` (Active Tier 1) |
| `projects/uir_base/results/mdpi_next_2026_10_11_v2/` | Next-generation base audit and model comparison evidence | `projects/uir_base/results/mdpi_next_2026_10_11_v2/` (Active Tier 1) |
| `projects/uir_base/results/uir_repr_*` | Representation research and semantics validation results | `projects/uir_base/results/uir_repr_*` (Active Tier 1) |
| `projects/uir_security/results/HETE_UIR_ZTA_V3_2_FINAL_PACKAGE` | Canonical HETE Zero-Trust Architecture release bundle | `projects/uir_security/results/HETE_UIR_ZTA_V3_2_FINAL_PACKAGE` (Active Tier 1) |
| `projects/uir_security/results/llm_security_v3_2*` | Active v3.2 evaluation and closure evidence | `projects/uir_security/results/llm_security_v3_2*` (Active Tier 1) |
| `projects/uir_law/results/law200` | Active Korean/English legal knowledge retrieval benchmark | `projects/uir_law/results/law200/` (Active Tier 1) |
| `docs/resources/reference_literature/*MANUSCRIPT*.md` | Unsubmitted manuscript drafts | Local only; excluded from Git tracking |
| `projects/**/validation/manuscript.py`, `build_manuscripts.py`, etc. | Manuscript build & compilation scripts | Local only; excluded from Git tracking |
| `projects/<project>/paper/` | Project manuscript workspaces | Public landing: `projects/<project>/paper/README.md`; TeX/Bib/PDF drafts: local only |
| `docs/work_reports/` | Work orders, private reviews, internal reports | Local only; excluded from Git tracking |

---

## Two-Tier Project Structure

Each of the three research projects (`uir_base`, `uir_security`, `uir_law`) follows a uniform project layout:

```text
projects/<project>/
  README.md                Project overview and scope
  paper/
    README.md              Public paper landing page
    current/               [Local only] Unsubmitted manuscript workspace (.tex, .bib, .pdf)
  docs/                    Project-wide architecture specifications
  evaluation/              Evaluation code, runners, and benchmark suites
  scripts/                 Task orchestration entry points
  resources/               Cross-milestone inputs and fixtures
  results/<task_id>/       Active task results, evidence, and reports
  reproduce.sh             Project-level verification entry point

archive/<project>/
  results/<phase_id>/      Historical evaluation runs and benchmark logs
```

---

## Reproduction and Path Translation

Path references to historical data continue to resolve seamlessly through `uir_common.paths.recorded_path()`. Frozen manifests preserve their exact historical recorded paths without requiring byte changes.

Deterministic reproduction commands:

```bash
# Verify immutable inputs and evaluator hashes
python scripts/reproduce_project.py uir_base verify
python scripts/reproduce_project.py uir_security verify
python scripts/reproduce_project.py uir_law verify

# Regenerate independent audit tables
python scripts/reproduce_project.py uir_base tables

# Execute project regression test suites
python scripts/reproduce_project.py uir_base tests
python scripts/reproduce_project.py uir_security tests
python scripts/reproduce_project.py uir_law tests
```
