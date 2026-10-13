"""Traceable scoped handoff; approvals and nonexecuted research remain explicit."""
import csv
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
from .common import DOC, PRIOR, ROOT, csvfile, jsonl, load, read, relative, sha, textfile, utc, write

STATUS = [
    ("S00", "PASS_SCOPED", "immutableZIPs, authority sidecars, 272 enumeration audit", "source_hash and mirror integrity are not source-world truth"),
    ("S01", "PASS_FULL_SUITE_SAME_HOST_NAMESPACE", "prior296+new32=328fulltests;165other-project tests/source and exact fixtures restored;Rust64offline", "same-host namespace and host interpreter/toolchain provisioning; no third-machine or independent human replication"),
    ("S02", "PASS_SYNTHETIC_DEVELOPMENT", "source-first48-fact corpus/24 real KO-EN requests/proper subsets/distractors/kernel gold boundary", "same implementer, easy CNL; no physical external retrieval"),
    ("S03", "PASS_EXPLORATORY_PREREG", "frozen16-cell factorial, same capabilities, one primary contrast, 72 identical-hash unique model calls", "development not confirmatory; four constructed clusters"),
    ("S04", "PASS_FINITE_INDEPENDENT_CODE", "separately coded Python/Rust41/41, current source/binary receipts and two extension cases", "same coding agent; S1 finite fragment, not all priorUIR semantics or independently staffed proof"),
    ("S05", "PASS_RESTRICTED_RAW_CNL", "12 true KO/EN pairs,24/32 raw inputs compile;8 unsupported clarify;negation/honorific tests", "no free-NL/human semantic accuracy"),
    ("S06", "PASS_CLOSED_DISPLAY_SCOPE", "all approved display lines checked;mixed prose/citation/numeric negatives;nonempty partial unit test;missing operands", "arbitrary native prose AUCR NOT_MEASURED; no open-world truth"),
    ("S07", "BLOCKED_NO_CONFIRMATORY_DATA", "known historical/development families excluded; no confirmatory inference", "new rights-cleared independent source/template/parent-report families not verified"),
    ("S08", "PARTIAL_SCOPE_CORRECTION", "FinQA supplied-page terminology and260/400,399/400 preserved; prior800 unchanged", "fresh operand/unit/task accuracy NOT_EXECUTED; no new family-disjoint data"),
    ("S09", "PASS_FINITE_READ_SANDBOX", "seven fixed surfaces/five policy scenarios;35 opportunities/condition;3allowed32blocked;forged ID set checked", "read-onlyS1, no adaptive model attacks/production host/concurrency theorem"),
    ("S10", "PARTIAL_AUTOMATED_PORTABILITY", "financialJSON and new energy_kwh domain preserve Python/Rust;LOC and100 warm observations", "implementation preceded cost protocol; no independent developer/reviewer labor study"),
    ("S11", "PASS_AI_ONLY_BOUNDARY", "oldAI raw/13valid8unresolved preserved; routeB/no human; annotation protocol prepared", "originalW08 NOT_SATISFIED; ethics/actual author approval pending"),
    ("S12", "PARTIAL_PRIVATE_MANUSCRIPT", "new10-page MDPI source/PDF and178-word abstract;five-tuple/rules/evidence/negative findings", "actualauthor/rights/currentjournal placeholders; MANUSCRIPT_READY BLOCKED"),
    ("S13", "PARTIAL_SUBMISSION_BLOCKED", "integrity/replay/claim/manuscript/submission gates separate, negative tests and detached receipt", "no public release/submit/payment; broad research remains unproved"),
]


def pre_release(out):
    baseline_run = out.parent / "run_20261013T045818Z"
    for name in ("S_BASELINE_MANIFEST.json", "release_report_sidecars.json", "historical_endpoint_audit.csv", "AUTHORITATIVE_RELEASE_MAP.md", "R_TO_S_CHANGELOG.md"):
        shutil.copyfile(baseline_run / name, out / name)
    write(out / "S00_import_receipt.json", {"source_run": relative(baseline_run), "copied_exact_bytes": True,
          "files": {n: sha(out / n) for n in ("S_BASELINE_MANIFEST.json", "release_report_sidecars.json", "historical_endpoint_audit.csv")}})
    paper = DOC / "manuscript/revision_S"
    log = (paper / "main.log").read_text(errors="replace")
    if "Overfull" in log or "undefined" in log or "Fatal error" in log:
        raise ValueError("PAPER_COMPILE_QA_NOT_PASS")
    write(paper / "paper_final_QA_S.json", {"created_at_utc": utc(), "page_count": 10, "pages_visually_inspected": list(range(1, 11)),
          "source_sha256": sha(paper / "main.tex"), "PDF_sha256": sha(paper / "main.pdf"), "overfull": False, "undefined_references": False,
          "abstract_words": 178, "initial_generation_manifest_is_not_final_source_binding": True,
          "render_files": {p.name: sha(p) for p in (paper / "rendered_pages").glob("final-*.jpg")}, "author_signoff": False,
          "benign_warning": "shell escape disabled; hash-matched cached logo PDF assets used"})
    textfile(paper / "render_qa.md", "# Final PDF QA\n\nAll10 pages rendered and visually inspected. Final layout repairs remove all overfull boxes; no undefined references/citations. Long science digest is line-breakable. Initial failed compile lacked copied soul packages; exact existing style assets were restored, and failed logs remain. Initial generation manifest binds pre-layout source; paper_final_QA_S.json and final detached receipt bind final source/PDF. No author/submission approval follows.\n")
    csvfile(out / "S_task_status_PRE_RELEASE.csv", [{"task": task, "status": status, "executed_evidence": evidence, "remaining_scope": scope,
             "evidence_kind": "SCOPED_ENGINEERING_TRACE", "responsible": "Codex implementation, not independent human QA", "created_at_utc": utc()} for task, status, evidence, scope in STATUS])
    claims = [
        ("independentS1interpretation", "SYNTHETIC_CONFORMANCE", "interpreter_agreement_v2.jsonl", "main.tex:125", "finite41; same coding agent"),
        ("queryaware_selection", "DEVELOPMENT", "query_aware_summary.csv", "main.tex:130", "0/24 raw exact; guard recovery is not model accuracy"),
        ("representation_matched", "DEVELOPMENT", "paired_analysis.json", "main.tex:136", "192/192 equal, no accuracy superiority"),
        ("actualGPUcalls", "FRESH_MODEL_INFERENCE", "fresh_execution_manifest.json", "main.tex:103", "72unique payloads,384not independent calls"),
        ("portability", "SYNTHETIC_CONFORMANCE", "backend_portability_cases.jsonl", "main.tex:148", "two API/domain cases, not labor productivity"),
        ("FinQA_scope", "HISTORICAL_REPLAY", "finqa_scope_metrics.json", "main.tex:141", "page literal presence, not annual-report QA"),
    ]
    csvfile(out / "claim_evidence_matrix_S.csv", [{"claim": claim, "evidence_kind": kind, "artifact": relative(out / source), "artifact_sha256": sha(out / source),
        "metric_generator": relative(ROOT / "projects/uir_base/representation_research/analysis.py"),
        "metric_generator_sha256": sha(ROOT / "projects/uir_base/representation_research/analysis.py"), "model_protocol_sha256": sha(out / "preregistration.json"),
        "paper_final_source_sha256": sha(paper / "main.tex"), "manuscript_locator": location, "scope": scope} for claim, kind, source, location, scope in claims])
    # Per-line support spans refer to actual approved strings, not raw native prose.
    spans = []
    for row in read(out / "factorial_saved_outputs.jsonl"):
        approved = row["approved"]["user_visible_output"]
        start = 0
        for line in approved.splitlines():
            spans.append({"case_id": row["case_id"], "condition_id": row["condition_id"], "start": start, "end": start + len(line),
                          "approved_fact_line": line, "support_oracle": "exact trusted bound closed line", "evidence_kind": "DEVELOPMENT"})
            start += len(line) + 1
    csvfile(out / "whole_output_claim_spans.csv", spans)
    textfile(DOC / "README_S_STAGE.md", "# S-stage private review\n\nTarget: Electronics / Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems (WFBEQFE47X). This is a scoped engineering/development release, not submission approval.\n\nActual executed stages: baseline ZIP/authority checks, exact fixture131-suite repair, same-host user/mount/network namespace,41 independently coded interpreter cases,24synthetic raw requests and16factorial cells,72actual RTX3090 Phi calls, two API/domain portability cases,35fixed sandbox opportunities per condition, new10-page PDF. All adverse results remain.\n\nThe final detached release_verification directory contains authoritative package replay/gates/receipt. PRE_RELEASE records inside the archive predate final ZIP replay and are not relabeled final. Historical root final_reproduce_report.json points to another R package. No self-hash is claimed inside a ZIP.\n\nActual reproduce command (once final receipt reports it succeeded):\n\n```bash\nsource /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate\nPYTHONPATH=src:. python -m projects.uir_base.representation_research.release --reproduce docs/work_reports/uir_base/112_representation_research/S_STAGE_REVIEW_PACKAGE.zip --report-dir /tmp/uir-s-review-replay\n```\n\nInterpreter/toolchain provisioning remains necessary: Linux CPython3.14 and recorded Rust version. Use `--help` for stage commands. Fresh inference is distinct from CPU raw replay; it needs frozen model artifact and the RTX3090-bound local server. It is NOT replayed during release verification.\n\nNot executed/blocked: third-machine/human replication, independently staffed developers, confirmed source-family-disjoint external inference, FinQA new task accuracy, human annotation and actual author/institution/rights/current-journal submission approvals. Native unrestricted prose AUCR and human productivity NOT_MEASURED.\n\nPrivate only: no model weights/secrets/Git internals, no public redistribution authorization, no upload/payment/submission.\n")


def final(out, archive, report_dir):
    replay = load(report_dir / "S_FINAL_REPRODUCE_REPORT.json")
    if replay["archive_sha256"] != sha(archive) or replay["status"] != "PASS_SCOPED":
        raise ValueError("FINAL_REPLAY_NOT_PASS")
    paper = DOC / "manuscript/revision_S"
    gates = {"created_at_utc": utc(), "ARCHIVE_INTEGRITY": "PASS", "OFFLINE_REPRODUCTION": "PASS_SCOPED_SAME_HOST_NAMESPACE",
             "REPRESENTATION_CLAIM_VALIDITY": "PASS_SCOPED_FINITE_ENGINEERING_ONLY", "MANUSCRIPT_READY": "BLOCKED_AUTHOR_RIGHTS_CURRENT_RULES",
             "SUBMISSION_READY": "BLOCKED", "confirmatory": "BLOCKED_NO_CONFIRMATORY_DATA", "human_W08": "NOT_SATISFIED",
             "full_research_superiority": "NOT_ESTABLISHED", "actual_author_approval": False, "institution_approval": False,
             "public_rights_approval": False, "live_submission_rules_certified": False, "responsible": "Codex technical evidence; author/institution authority not delegated"}
    write(report_dir / "S_stage_release_gate.json", gates)
    csvfile(report_dir / "S_task_status.csv", [{"task": task, "status": status, "executed_evidence": evidence,
             "remaining_scope": scope, "final_archive_sha256": sha(archive)} for task, status, evidence, scope in STATUS])
    report = "# S00–S13 scoped completion report\n\n2026-10-13 Asia/Seoul. Engineering implementation/evidence delivered; not all original scientific/author requirements met.\n\n"
    report += "## Actual results\n\n- Original ZIP hashes match,5417baseline files verified; authoritative v3 detached report selected. Original ZIPs/results/paper bytes preserved.\n- Recovered exact two runtime fixtures: baseline129pass/2fail retained; repaired131pass. New S-delivered163tests pass separately; full checkout328pass is NOT standalone328. Other165tests are itemized. Rust64tests execute independently offline in the extracted new package.\n- Actual user/mount/network namespace hides original repository path; exact offline lock install and raw replay use no GPU/remoteDB/network inference. Physical host and toolchain provisioning remain shared; no third-machine/human replication.\n- Independently coded Python/Rust41/41agree; same coding agent, shared canonical serialization only. New JSON financial/energy API cases also preserve results.\n- Source-first synthetic48-fact pool,24actual raw KO/EN requests,16factorial cells/384records,72actual RTX3090Phi calls. Gold hidden at canonical directory; changed evaluator labels do not change runtime outputs.\n- Non-oracle rawSLM exact selection0/24; raw irrelevant selections24/24. Strong deterministic relevance guard+template recovers24/24. Model renderer complete7/24. No outcomes hidden or tuned into confirmation.\n- UIR/specialized192/192paired outcomes equal. Public serialization warmP50~2.162ms vs native~0.953ms in the actual differing workloads; no speed/productivity superiority. Developer/reviewer labor NOT_MEASURED.\n- Approved whole display is checked only for CLOSED_FACT_LINES_S1. Arbitrary native prose AUCR NOT_MEASURED. Valid nonempty partial and missing-operand negatives are tested.\n- New finite read-only sandbox35opportunities per condition:3allowedexecute,32prohibitedblocked,0false denial. Fixed synthetic payloads, not adaptive model attacks.\n- FinQA page-context literal presence260/400,399/400 remains historical diagnostics, not source-report correctness; old800scores unchanged. New confirmatory/FinQA task inference NOT_EXECUTED.\n- NewMDPI10-page/178-word private draft compiled, all pages rendered/visually inspected; no overfull/undefined refs. Target changed to WFBEQFE47X, without inventing multi-agent features or a30-page padding requirement.\n\n"
    report += "## Remaining and failed checks\n\nS01third-machine/independent human replication, S07independent unseen source families, S08new end-to-end FinQA/unit accuracy, S10independently staffed developer effort, S11actual human/ethics and S12–S13actual author/rights/current journal approval remain limited/blocked. The final package closes the previously missing165 other-project tests and reproduces all328. Initial package v1 Rust fixture failure and package-v2 narrower163suite success remain distinct audit records; FINAL is authoritative. No human labels are fabricated. OriginalW08 NOT_SATISFIED. Full `cargo fmt --check` detects pre-existing formatting; full `clippy -D warnings` fails two existing Boolean assertions in crates/poa-uir/src/tests.rs:379/383. They are preserved, not hidden; the new interpreter binary's clippy passes. Functional tests pass.\n\n"
    report += "## Gate and package authority\n\nARCHIVE_INTEGRITY PASS; OFFLINE_REPRODUCTION PASS_SCOPED on same-hostnamespace; REPRESENTATION_CLAIM_VALIDITY PASS_SCOPED finiteengineering only; MANUSCRIPT_READY and SUBMISSION_READY BLOCKED. Actual author/institution/rights/livejournal confirmation is required. No commit/push/newbranch/symlink/publicupload/submission/payment. PRE_RELEASE package records are explicitly earlier than final verification. The final detached receipt/gates/replay report in this directory are authoritative, not falsely claimed inside their self-hashed ZIP.\n\n"
    report += f"Archive: `{relative(archive)}`\n\nSHA-256: `{sha(archive)}`\n\nReproduction report: `S_FINAL_REPRODUCE_REPORT.json` (all command/log/exit-code fields).\n"
    textfile(report_dir / "S_STAGE_COMPLETION_REPORT.md", report)
    write(report_dir / "S_FINAL_RELEASE_RECEIPT.json", {"created_at_utc": utc(), "archive": relative(archive), "archive_sha256": sha(archive),
          "replay_sha256": sha(report_dir / "S_FINAL_REPRODUCE_REPORT.json"), "gates_sha256": sha(report_dir / "S_stage_release_gate.json"),
          "science_manifest_sha256": sha(out / "S_science_manifest.json"), "main_tex_sha256": sha(paper / "main.tex"), "main_PDF_sha256": sha(paper / "main.pdf"),
          "receipt_inside_archive": False, "archive_rights": "PRIVATE_REVIEW_ONLY", "submission_ready": False})
    print(json.dumps(gates))
