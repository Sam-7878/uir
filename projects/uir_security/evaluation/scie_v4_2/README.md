# HETE V4.2 reference engine and evaluation

Run from the UIR repository root with the Ubuntu root `.venv_cuda` Python3.14.4.
The application boundary is `typed_engine.py`. It imports no benchmark oracle or
gold labels; authority comes from the application issuer, never generated text.
`external.py` invokes real AgentDojo environments and matched minimal/typed paths.
`effect_oracles.py` is offline analysis only. `mechanism.py` exercises actual SQLite
effects and the original pipeline output boundary. Protocols freeze source hashes
before experiments; do not edit a seen protocol or relabel development as held out.

Evidence and local manuscript ZIPs are under
`projects/uir_security/results/hete_electronics_v4_2_2026_10_21/`. Start with its
`reports/FINAL_EXECUTION_REPORT_KO.md`, `WORK_ORDER_W01_W20_STATUS.csv`,
`SUBMISSION_DECISION.json` and `PREFLIGHT_REPORT.json`. Every release remains HOLD
until actual author/institutional decisions. READY/FINAL names are not permission.

Existing failures, incomplete backend responses, post-hoc C3 transport correction,
late analysis registration, low bilingual utility and prose-contract costs remain.
Minimal and typed guards have identical observed external security and utility.
No superiority, general confidentiality, human validation or complete historical
inference replay is claimed. Portable stdlib projection recount is a different
reproduction level from new GPU inference.

Use `python -m projects.uir_security.evaluation.scie_v4_2.<module>`. Writers target
the fixed task directory: use a NEW directory/protocol for genuinely new inference.
Do not execute historical V4 writers to verify frozen outputs. See task
`source/REPRODUCTION_COMMANDS.md` for dependencies, roles, hardware, context,
caching, missing responses and rebuild details.
