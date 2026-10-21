# UIR security research

Derived cybersecurity/zero-trust project, reusing the shared core and explicit base
interfaces without copying them. Project-wide design belongs in `docs/`, reusable
inputs in `resources/`, and evaluation/orchestration sources in `evaluation/` and
`scripts/`. Manuscript workspaces are local/private under `paper/`.

Keep every task's data, reports, figures, resources and logs together in
`results/<task_id>/`. Private work orders/reviews/work reports stay at root
`docs/work_reports/uir_security/<task_id>/`, LOCAL ONLY.
See [repository layout](../../docs/architecture/PROJECT_LAYOUT.md).

The SCIE reinforcement starts at `evaluation/scie_v4/`; its versioned task output
is `results/scie_acceptance_2026_10_21_v4/`. Current assumptions and contracts are in
`docs/SECURITY_MODEL_V4.md`, `docs/TCB_ASSUMPTIONS.md`, and
`docs/RESOURCE_SEMANTICS.md`. Historical V3.2 originals remain separate.

V4.2 implementation: `evaluation/scie_v4_2/`; task evidence and review manuscripts:
`results/hete_electronics_v4_2_2026_10_21/`. Start with that task's
`reports/FINAL_EXECUTION_REPORT_KO.md` and `SUBMISSION_DECISION.json`. Current scope:
`docs/SECURITY_MODEL_V4_2.md`. Local draft/READY names do not authorize release.
