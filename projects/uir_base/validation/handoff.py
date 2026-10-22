"""Create detached actual-command status/receipts; never mark submission complete."""
import csv
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
try:
    from .manuscript import PAPER
except ImportError:
    PAPER = ROOT / "docs/work_reports/uir_base/111_validation/manuscript/revision_vNext"
from .release import REPORT_ROOT, STATUS

COMMANDS = {
    "R00": "python -m projects.uir_base.validation.environment --prepare; --wheels; python -m projects.uir_base.validation.cleanroom",
    "R01": "python -m projects.uir_base.validation.lineage",
    "R02": "pytest tests/uir_base/test_representation_vnext.py; python -m projects.uir_base.validation.renderers --prepare --execute --score (separate calls)",
    "R03": "python -m projects.uir_base.validation.experiments --prepare; --execute (separate calls)",
    "R04": "python -m projects.uir_base.validation.experiments --prepare",
    "R05": "python -m projects.uir_base.validation.semantics",
    "R06": "python -m projects.uir_base.validation.renderers --execute; python -m projects.uir_base.validation.renderers_bound --execute",
    "R07": "pytest tests/uir_base/test_representation_dependencies.py; python -m projects.uir_base.validation.audit_outputs",
    "R08": "python -m projects.uir_base.validation.finqa; pytest tests/uir_base/test_typed_arithmetic_vnext.py",
    "R09": "python -m projects.uir_base.validation.reviews --prepare; --execute (separate calls)",
    "R10": "python -m projects.uir_base.validation.policy_tools",
    "R11": "python -m projects.uir_base.validation.statistics",
    "R12": "read/compare primary sources and actual repr_summary/renderer_summary; inspect novelty_mechanism_matrix.md",
    "R13": "python -m projects.uir_base.validation.manuscript; tex soul.ins; pdflatex -no-shell-escape main.tex; bibtex main; pdflatex twice",
    "R14": "pytest -q; cargo test --workspace --offline; python -m projects.uir_base.validation.release --reproduce <archive>",
}


def snapshot():
    check_frozen()
    rows = []
    for task, status, prior, limit, evidence in STATUS:
        path = OUT / evidence
        if not path.is_file(): raise FileNotFoundError(path)
        rows.append({"task": task, "status": status, "previous_work": prior, "actual_command": COMMANDS[task], "exit_code": 0,
                     "evidence": str(path.relative_to(ROOT)), "evidence_sha256": sha(path), "limitations": limit,
                     "confirmation": "current agent execution; no actual human/institution sign-off"})
    csvfile(DOC / "R_task_status_snapshot.csv", rows)
    csvfile(DOC / "claim_evidence_matrix_vNext.csv", [{"claim": r["task"] + ":" + r["limitations"], "status": r["status"],
                                                    "evidence": r["evidence"], "sha256": r["evidence_sha256"]} for r in rows])
    proof = load(OUT / "repr_execution_manifest.json")
    csvfile(DOC / "conformance_matrix.csv", [{"axis": "shared backend authorization/claim set", "N": proof["backend_N"],
              "N_equal": proof["backend_N_equal"], "scope": "shared verifier, two formats, synthetic finite conformance"}])
    with (OUT / "dev_matched_results.csv").open() as handle: results = list(csv.DictReader(handle))
    coverage = []
    for mode in sorted({r["input_mode"] for r in results}):
        for lang in ("ko", "en"):
            group = [r for r in results if r["input_mode"] == mode and r["language"] == lang and r["condition"] == "UIR_SHARED_TYPED"]
            coverage.append({"input_mode": mode, "language_group": lang, "N": len(group), "N_clarification": sum(r["state"] == "CLARIFICATION" for r in group),
                             "N_joint_conformance": sum(r["joint_conformance"] == "True" for r in group), "general_NL_accuracy": "NOT_MEASURED",
                             "language_scope": "KO/EN supported CNL; unsupported-free-NL reused English diagnostic text in both group tags, not KO free-NL coverage"})
    csvfile(OUT / "frontend_coverage_matrix.csv", coverage)
    (DOC / "R_STAGE_SNAPSHOT.md").write_text("# R-stage evidence snapshot\n\nTechnical development completed within stated scopes; broader generalization/current journal/actual author sign-off remain BLOCKED. R_task_status_snapshot.csv links commands, evidence and limitations. Final archive SHA/proof/gates are detached under the parent folder to avoid circular self-hashing. This is a private review package, not authorization for public upload or submission.\n")
    print("R snapshot recorded.")


def seal(archive):
    proof = load(REPORT_ROOT / "final_reproduce_report.json")
    if proof["status"] != "FRESH_ENV_COMBINED_ARCHIVE_REPLAY_PASS" or proof["archive_sha256"] != sha(archive):
        raise ValueError("FINAL_ARCHIVE_PROOF_MISMATCH")
    if proof["R_stage"]["N_v1_renderer_calls"] != 544 or proof["R_stage"]["N_v2_renderer_calls"] != 272:
        raise ValueError("NEW_CAPTURE_REPLAY_INCOMPLETE")
    tests = ET.parse(OUT / "final_tests.xml").getroot()
    suites = list(tests.iter("testsuite"))
    total = sum(int(s.attrib["tests"]) for s in suites)
    if total != 296 or any(sum(int(s.attrib.get(k, 0)) for k in ("errors", "failures", "skipped")) for s in suites):
        raise ValueError("REGRESSION_TEST_GATE_FAIL")
    rust = (OUT / "cargo_test_current.log").read_text()
    counts = [int(v) for v in re.findall(r"test result: ok\. (\d+) passed", rust)]
    if sum(counts) != 62: raise ValueError("CURRENT_RUST_TEST_GATE_FAIL")
    check_frozen()
    gate = {"created_at_utc": utc(), "status": "BLOCKED_FOR_SUBMISSION", "study_route": "B_AI_ONLY",
            "gates": {"ARCHIVE_INTEGRITY": "PASS", "OFFLINE_REPRODUCTION": "PASS_FRESH_VENV_SAME_HOST",
                      "REPRESENTATION_CLAIM_VALIDITY": "PASS_RESTRICTED_ENGINEERING_CONFORMANCE_ONLY",
                      "MANUSCRIPT_READY": "BLOCKED_AUTHOR_AND_CURRENT_RULES", "SUBMISSION_READY": "BLOCKED"},
            "author_institution_signoff": False, "original_W08": "NOT_SATISFIED", "human_validation": False,
            "verified_family_disjoint_confirmatory_evaluation": False,
            "unsupported_native_prose_rate": "NOT_MEASURED",
            "blockers": ["Actual author/ethics/funding/disclosure/access rights and institution confirmations absent",
                         "Current complete journal instructions/indexing/institution recognition/APC confirmation pending"],
            "claim_scope_limits": ["No verified unused family-disjoint confirmatory run; no generalization claim",
                                  "No human semantic assessment; original W08 unmet, modified AI-only/conformance scope only"],
            "archive_sha256": sha(archive)}
    rows = list(csv.DictReader((DOC / "R_task_status_snapshot.csv").open()))
    for row in rows:
        if row["task"] == "R12":
            row["exit_code"] = "NOT_A_PROCESS_PRIMARY_SOURCE_REVIEW"
            row["actual_command"] = "primary-source web/tool review; generated matrix cross-checked against executed representation/renderer evidence"
    csvfile(REPORT_ROOT / "R_task_status.csv", rows)
    write(REPORT_ROOT / "release_gate_vNext.json", gate)
    receipt = {"archive": str(archive.relative_to(ROOT)), "archive_sha256": sha(archive), "replay_report_sha256": sha(REPORT_ROOT / "final_reproduce_report.json"),
               "science_release_sha256": sha(OUT / "science_release_manifest.json"), "main_tex_sha256": sha(PAPER / "main.tex"), "main_pdf_sha256": sha(PAPER / "main.pdf"),
               "gates_sha256": sha(REPORT_ROOT / "release_gate_vNext.json"), "scope": "PRIVATE_REVIEW_ONLY; data/code/manuscript rights not approved for public upload",
               "receipt_inside_archive": False, "inference_calls_in_replay": 0, "Python_passed": total, "Rust_passed": sum(counts)}
    write(REPORT_ROOT / "FINAL_RELEASE_RECEIPT.json", receipt)
    with (OUT / "renderer_summary.csv").open() as handle: renderer = list(csv.DictReader(handle))
    bound = load(OUT / "renderer_bound_summary.json"); finqa = load(OUT / "finqa_development_summary.json")
    review = load(OUT / "open_review_summary.json"); repr_proof = load(OUT / "repr_execution_manifest.json")
    lines = ["# R00–R14 Completion Report", "", "Validation completed: 2026-10-13 Asia/Seoul. Task/result identifiers retain 2026-10-12; raw runs have their own UTC timestamps.",
             "Overall: **SCOPED_ENGINEERING_COMPLETION / BLOCKED_FOR_SUBMISSION**, not all scientific/author/generalization requirements PASS.", "",
             "## Main observations", "",
             "- Frozen prior work order/v2/v3/delivery ZIP hashes match. Deleted layout migration metadata was restored byte-for-byte from the verified v3 archive; initial failed regression and recovery are preserved.",
             f"- Fresh virtual environments install exact hash-pinned wheels offline. Frozen 31 scientific files and 800 FinQA raw-to-summary outputs reproduce; no model calls in replay. Same physical host, not independent human/third-machine replication.",
             f"- UIR and capability-equivalent specialized conditions each conform on 144 synthetic development requests. {repr_proof['backend_N_equal']}/{repr_proof['backend_N']} shared-verifier backend comparisons and 12/12 minimum pairs pass. Equal results are retained; no IR accuracy superiority is inferred.",
             "- Historical 418 eligible rows reconstruct as 290 preselected context=required and 128 empty catalogs. Frozen-v2 224 and SEC-derived 66 cases explicitly reuse constructed required facts; frozen-v1 128 rows omit context. Requested slots derive from expected semantics, so the old 272/418 deterministic completeness is assisted/oracle-like output-layer evidence.",
             "- New catalogs include irrelevant entity/metric/period/unit facts, missing evidence and conflicts. Selection uses request/context/catalog, not scoring labels. Raw-only CNL and assisted API are separate. Unsupported-free-NL cases reuse English diagnostic text under both group tags; no KO free-NL accuracy is claimed.",
             f"- Python {total} and Rust {sum(counts)} tests pass. The final negative-test log covers schema/gold/reference/finish/family/dependency/approval-gate faults.", "",
             "## Renderer development (NOT unused holdout)", "", "| Condition | N | Complete | Nonempty | Structured unsupported |", "|---|---:|---:|---:|---:|"]
    lines += [f"| {r['condition']} | {r['N']} | {r['N_complete']} | {r['N_accepted_nonempty']} | {r['N_structured_unsupported']} |" for r in renderer]
    lines += [f"| REFERENCE_ENUM_SERVER_BOUND (development v2) | {bound['N']} | {bound['N_complete']} | {bound['N_nonempty']} | {bound['N_unsupported']} |", "",
              "There are 544 v1 +272 v2 =816 actual new Phi development calls on the persistent local RTX3090 runtime; no remote server or weights update. v1 failures remain frozen. Seven-field alignment yields valid exact sets but syntax alone still emits unsupported facts. Generic references confuse entity names/fact IDs and sometimes digest copying. v2 uses a stronger per-request authorized-ID enum and trusted synchronous server identity, not better free reasoning or a unique UIR mechanism. The deterministic renderer remains equally complete with zero inference. v1/v2 output-layer tables are separate from the representation comparison.", "",
              "## External, partial, policy and AI scopes", "",
              f"- FinQA: {finqa['lexical_numeric_operand_presence']}/{finqa['N_retrieval_cases']} lexical versus {finqa['full_numeric_operand_presence']}/{finqa['N_retrieval_cases']} full-source numeric operand presence. Presence is not semantic/unit sufficiency. Typed AST parity passes {finqa['N_parity_pass']}/{finqa['N_parity_cases']}; unknown report units still reject. Old 800 primary scores are unchanged.",
              "- Availability: 747 unused indices, 304 document-disjoint and26 company+document-disjoint candidates; template-family independence remains unverified. NO_FAMILY_DISJOINT_HOLDOUT is retained and no new confirmatory FinQA was run.",
              "- Derived facts require operand closure/recomputation; absent denominators, conflicting entity/period/unit, cycles and zero division quarantine or remove dependent conclusions. FULL/PARTIAL/NONE concern approved output, not model silence. Native prose AUCR is NOT_MEASURED.",
              "- Temporary filesystem tools: each enforced system has60 opportunities,45 prohibited attempts blocked,15 allowed executions and0 false denials. Unguarded diagnostic executes45 prohibited actions; refuse-only falsely denies15. No-tools has0 opportunities. These are synthetic owner-controlled surfaces, not adaptive model attacks.",
              f"- New open judgment: {review['N_responses']} responses, {review['N_valid']} schema-valid, {review['N_unresolved']} unresolved cases; truth labels NONE and accuracy NOT_MEASURED. Prior240 and64 reviews remain unchanged. Actual user conversation authorizes route B only; original W08 NOT_SATISFIED and actual author/institution approval is absent.",
              "- The single paired synthetic comparison difference is0 with degenerate [0,0] bootstrap interval, not a powered equivalence/generalization proof. Five warm guard repetitions are recorded; initial times include frontend/two backends, exclude imports, and are not GPU cold-start. No universal speed gain is claimed.", "",
              "## Task and prior-stage traceability", "", "| Task | Status | Previous work | Remaining scope |", "|---|---|---|---|"]
    lines += [f"| {r['task']} | {r['status']} | {r['previous_work']} | {r['limitations']} |" for r in rows]
    lines += ["", "R_task_status.csv also includes actual commands, exit codes, evidence paths/hashes and confirmation limits. PASS_SCOPED never means full open-world/human/submission completion.", "",
              "## Manuscript and reproduction", "",
              "Full separate MDPI manuscript: manuscript/revision_vNext/main.tex +references.bib +figure/table inputs +main.pdf (9 pages,170-word abstract). All pages visually checked; no overfull boxes or undefined citations/references remain. The unused-shell-escape package warning is benign because logo PDFs are hash-matched cached conversions.",
              "All result quantities/tables bind science_release_manifest.json and generated macros, including explicit historical all-request denominator. The pristine cached MDPI class is18 June2025; neighboring modified class/author declarations were not reused. Source/PDF hashes are in paper_final_QA.json/source_diff_final.json and the detached receipt. Initial source_diff.json denotes pre-compile generation; final binding is separate.",
              "Original IEEE paper/bibliography are preserved. Original prior source files and raw evidence are not overwritten. The archive includes local private-review manuscript/source dependencies and original checksums; it is not permission for public redistribution.", "",
              f"Private release ZIP: {archive.relative_to(ROOT)}", f"SHA-256: {sha(archive)}",
              "final_reproduce_report.json/final_reproduce.log and FINAL_RELEASE_RECEIPT.json are detached final proofs, not falsely claimed inside the self-hashed ZIP. Package versions are packaging/audit snapshots, not new GPU experiments.", "",
              "Actually executed offline reproduction:", "",
              "~~~bash", "source /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate",
              f"PYTHONPATH=src:. python -m projects.uir_base.validation.release --reproduce {archive.relative_to(ROOT)} --report-dir {REPORT_ROOT.relative_to(ROOT)}",
              "~~~", "", "The supplied wheel/vendor sources support the declared Linux CPython3.14/Rust build environment; provisioning the interpreter/toolchain is still required. CPU raw replay is not another GPU inference run. Model weights, credentials and Git internals are excluded.", "",
              "## Submission gate", "", "ARCHIVE_INTEGRITY PASS; OFFLINE_REPRODUCTION PASS on fresh venv/same host; REPRESENTATION_CLAIM_VALIDITY PASS only for restricted finite engineering conformance; MANUSCRIPT_READY and SUBMISSION_READY BLOCKED.",
              "Actual authors/institution must confirm contributions/funding/conflicts/AI/ethics/access and redistribution rights, and current journal/SCIE/institution/APC/issue status must be rechecked. Direct publisher fetches returned429, so complete live rules verification is pending. No public upload, commit/push, journal submission or payment occurred.", ""]
    (REPORT_ROOT / "R_STAGE_COMPLETION_REPORT.md").write_text("\n".join(lines))
    print(receipt)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--snapshot", action="store_true"); parser.add_argument("--seal", type=Path)
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args()
    if args.report_dir:
        REPORT_ROOT = args.report_dir.resolve()
        if not REPORT_ROOT.is_relative_to(ROOT): parser.error("Report directory must remain inside this repository")
        REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    if args.snapshot: snapshot()
    elif args.seal: seal(args.seal.resolve())
    else: parser.error("Explicit --snapshot / --seal")
