"""Seal actual evidence with a detached receipt, never fabricate completed gates."""
import argparse
import json
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from projects.uir_base.scripts import revision_audit as a
from projects.uir_base.scripts.next_release import DEFAULT, checked_path, csv_rows

DOCS = a.ROOT / "projects/uir_base/results/110_mdpi_rev"
IMPL = DOCS / "implementation"
TASKS = [
    ("N00", "PASS_SCOPED", "W00,W04,W12", "Preserved historical inputs/evaluator; archive-only replay, not model rerun.", "release_manifest.json"),
    ("N01", "PASS", "W01,W02,W03", "Literal labels, hardcoded aggregate and exact-field D1 transition traced to raw captures.", "metric_change_diagnostics.json"),
    ("N02", "PASS_SCOPED", "W02,W10", "Structured support and unassessed prose separated; native whole-output safety NOT_MEASURED.", "whole_output_assessment.csv"),
    ("N03", "PASS_SCOPED", "W04,W07,W08", "Raw-only/trusted-slot paths separated; CPython payload/file tests, not host/native/inherited-FD isolation.", "logs/gold_access_test.log"),
    ("N04", "PASS_RESTRICTED_CNL", "W07,W08", "Recursive condition AST/canonical identity/conformance; no general free-NL accuracy.", "frontend_case_results.jsonl"),
    ("N05", "PARTIAL", "W06", "C5 lineage and 272 fresh calls; five/seven-field confound; input/IR causal comparison not executed.", "fresh_matched_offline_replay/verification.json"),
    ("N06", "PASS_SCOPED", "W11", "238 recorded eligible source families; paired bootstrap; descriptive single-repetition latency.", "paired_source_family_statistics.csv"),
    ("N07", "PARTIAL_UNRELIABLE_CALIBRATION", "W08", "64 valid-schema reviews, 16+16 unresolved; fixture accuracy is not human semantic calibration.", "ai_review_v2/holdout_summary.json"),
    ("N08", "PASS_ROUTE_B_ONLY", "W08,W14", "User-approved AI-only amendment; original W08 NOT_SATISFIED, actual human/author approvals absent.", "study_design_amendment.json"),
    ("N09", "PARTIAL_ADAPTER_CONFOUNDED", "W01,W09", "800 real requests replayed; strict extraction, DSL syntax and unit effects confound attribution.", "finqa_holdout_v2/posthoc_diagnostic_summary.json"),
    ("N10", "PASS_SYNTHETIC_CONFORMANCE_ONLY", "W10", "In-memory action opportunities tested; seeded mutation reconstruction, not deployed prompt-injection robustness.", "policy_conformance/action_summary.csv"),
    ("N11", "PASS_BOUNDED_POSITIONING", "W05,W13", "Primary literature and negative controls retained; causal IR benefit remains unestablished.", "historical_reanalysis/claim_evidence_map.csv"),
    ("N12", "PARTIAL_PROVISIONAL_DRAFT", "W03,W13,W14", "Generated tables/compiled separate research draft; not full MDPI revision or author-approved declarations.", "finqa_holdout_v2/summary.csv"),
    ("N13", "PARTIAL_SUBMISSION_BLOCKED", "W00-W15", "Technical replay/negative tests do not replace remaining scientific gates or human/author confirmations.", "fresh_independent_replay/verification.json"),
]


def load(relative):
    return json.loads((DEFAULT / relative).read_text())


def validate():
    release = load("release_manifest.json")
    for item in release["input_sources"]:
        checked_path(a.ROOT, item["path"], item["sha256"])
    name = "projects/uir_base/scripts/revision_audit.py"
    checked_path(a.ROOT, name, release["source_hashes"][name])
    for relative, digest in release["scientific_output_sha256"].items():
        checked_path(DEFAULT, relative, digest)
    fresh = load("fresh_matched/fresh_run_manifest.json")
    checked_path(DEFAULT, "fresh_matched/raw_requests_responses.jsonl", fresh["raw_capture_sha256"])
    checked_path(a.ROOT, "projects/uir_base/scripts/next_gpu_matched.py", fresh["runner_sha256"])
    finqa = load("finqa_holdout_v2/execution_manifest.json")
    checked_path(DEFAULT, "finqa_holdout_v2/raw_requests_responses.jsonl", finqa["raw_sha256"])
    protocol = load("finqa_holdout_v2/protocol.json")
    checked_path(a.ROOT, "projects/uir_base/scripts/next_holdout.py", protocol["source_sha256"])
    checked_path(a.ROOT, "projects/uir_base/scripts/next_benchmark_adapter.py", protocol["arithmetic_adapter_sha256"])
    review = load("ai_review_v2/protocol.json")
    checked_path(a.ROOT, "projects/uir_base/scripts/next_review.py", review["runner_sha256"])
    for split in ("calibration", "holdout"):
        checked_path(DEFAULT, f"ai_review_v2/{split}_raw_reviews.jsonl", load(f"ai_review_v2/{split}_summary.json")["raw_sha256"])
    if fresh["N_model_calls"] != 272 or finqa["N_attempted"] != 800:
        raise ValueError("Unexpected executed cohort")
    if load("fresh_independent_replay/verification.json")["status"] != "MATCHED_AI_AND_FINQA_CAPTURE_REPLAY_PASS":
        raise ValueError("Missing independent capture replay")


def prepare():
    validate()
    target = DEFAULT / "final_release_index.json"
    if target.exists():
        raise FileExistsError("Do not replace a sealed snapshot")
    files = [p for p in DEFAULT.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "dependency_manifest.csv"]
    files += list((a.ROOT / "projects/uir_base/scripts").glob("next_*.py"))
    files += list((a.ROOT / "tests/uir_base").glob("test_next_*.py"))
    a.write_json(target, {"status": "EVIDENCE_SNAPSHOT_NOT_SUBMISSION_READY", "original_W08": "NOT_SATISFIED",
                          "human_validation": False, "inference_rerun_in_clean_room": False,
                          "files": {str(p.relative_to(a.ROOT)): a.digest(p) for p in sorted(set(files))}})
    rows = [{"task": n, "status": s, "original_work": w, "scope_and_remaining_work": d,
             "evidence": str((DEFAULT / e).relative_to(a.ROOT)),
             "confirmation": "automated execution/model analysis; no independent human or author sign-off"}
            for n, s, w, d, e in TASKS]
    a.write_csv(IMPL / "task_status_snapshot.csv", rows)
    claims = [
        ("Restricted bilingual CNL equivalence/conditions", "SUPPORTED_CONFORMANCE_ONLY", "frontend_case_results.jsonl", "Not general free-NL semantic accuracy."),
        ("Registry-relative structured support", "SUPPORTED_SCOPED", "whole_output_assessment.csv", "Not whole-prose factuality or correct underlying registries."),
        ("SLM necessary for useful trusted-slot output", "NOT_SUPPORTED", "historical_reanalysis/internal_utility_recomputed.csv", "Control has 48 more complete cases at equal coverage."),
        ("Typed IR improves accuracy over equivalent no-IR validation", "NOT_ESTABLISHED", "fresh_matched_offline_replay/verification.json", "Representation comparison absent; output schema/scorer confound."),
        ("Two AI reviewers replace independent human gold", "NOT_CLAIMED", "ai_review_v2/holdout_summary.json", "Supplementary only; original W08 unmet."),
        ("Superior generator reasoning on new FinQA", "NOT_ESTABLISHED", "finqa_holdout_v2/posthoc_diagnostic_summary.json", "Extraction/units/DSL confounded."),
        ("Finite sandbox enforcement", "SUPPORTED_FINITE_CONFORMANCE", "policy_conformance/action_summary.csv", "Not deployed agent or host/registry-compromise security."),
        ("Offline raw-to-metric reconstruction", "SUPPORTED_SCOPED", "fresh_independent_replay/verification.json", "Not model rerun or independent human validation."),
    ]
    a.write_csv(IMPL / "claim_evidence_matrix.csv", [{"claim": c, "status": s, "evidence": str((DEFAULT / e).relative_to(a.ROOT)), "limitation": l} for c, s, e, l in claims])
    (IMPL / "EVIDENCE_HANDOFF_SNAPSHOT.md").write_text(
        "# Evidence snapshot\n\nOverall PARTIAL_COMPLETION / BLOCKED_FOR_SUBMISSION.\n\n"
        "task_status_snapshot.csv and claim_evidence_matrix.csv describe the scope. "
        "final_release_index.json binds actual results/source. The ZIP freezes this snapshot. "
        "Later ZIP SHA and final clean-room proof/gates are detached in ../FINAL_RELEASE_RECEIPT.json and ../release_gate.json; "
        "they are not claimed to be bytes inside a self-hashing archive.\n\n"
        "Original raw/evaluator/papers preserved. No commit, push, public upload, payment, "
        "submission, human annotation or author approval performed.\n")


def seal(archive, clean_report):
    validate()
    proof = json.loads(clean_report.read_text())
    if proof["status"] != "ARCHIVE_ONLY_OFFLINE_REPRODUCTION_PASS" or proof["archive_sha256"] != a.digest(archive):
        raise ValueError("Archive/proof mismatch")
    if not proof["no_development_checkout_imports"] or proof["scientific_files_equal"] != 31:
        raise ValueError("Historical archive replay incomplete")
    if (proof.get("fresh_capture_replay") or {}).get("status") != "MATCHED_AI_AND_FINQA_CAPTURE_REPLAY_PASS":
        raise ValueError("Fresh archive capture replay incomplete")
    tests = ET.parse(DEFAULT / "logs/final_tests.xml").getroot()
    suites = [tests] if tests.tag == "testsuite" else list(tests.iter("testsuite"))
    total = sum(int(s.attrib.get("tests", 0)) for s in suites)
    if total < 240 or any(sum(int(s.attrib.get(k, 0)) for k in ("failures", "errors", "skipped")) for s in suites):
        raise ValueError("Required configured tests incomplete")
    index_path = DEFAULT / "final_release_index.json"
    for relative, digest in json.loads(index_path.read_text())["files"].items():
        checked_path(a.ROOT, relative, digest)
    gate = {"status": "BLOCKED_FOR_SUBMISSION", "original_W08": "NOT_SATISFIED", "study_route": "B_AI_ONLY", "human_validation": False,
            "gates": {"EXPORT_INTEGRITY_PASS": "PASS", "REPRODUCIBLE_EVALUATION_PASS": "PASS_OFFLINE_CAPTURE_REPLAY_ONLY",
                      "SEMANTIC_SCOPE_VALIDATED": "PARTIAL_RESTRICTED_CONFORMANCE_ONLY", "MANUSCRIPT_READY": "BLOCKED", "SUBMISSION_READY": "BLOCKED"},
            "blocking_reasons": ["N05 representation-layer comparison incomplete and output schema/scorer mismatch",
                                 "N07 assessors remain unresolved, not human semantic gold",
                                 "N09 strict adapter/DSL/unit effects confound reasoning attribution",
                                 "N12 full MDPI source/template/narrative numeric/PDF review incomplete",
                                 "Actual author/institution declarations and final journal/indexing/APC checks pending"],
            "archive_sha256": a.digest(archive), "independent_human_reproduction": False}
    stable_proof = DOCS / "clean_room_report.json"
    stable_log = DOCS / "clean_room_reproduction.log"
    if stable_proof.exists() or stable_log.exists():
        raise FileExistsError("Do not overwrite detached clean-room proof")
    shutil.copyfile(clean_report, stable_proof)
    stable_log.write_text((clean_report.parent / "clean_room_reproduction.log").read_text() + "\n--- Fresh raw-capture replay ---\n" + (clean_report.parent / "clean_room_fresh_replay.log").read_text())
    receipt = {"status": "VERIFIED_TECHNICAL_EVIDENCE_PARTIAL_SCIENTIFIC_COMPLETION",
               "archive": str(archive.relative_to(a.ROOT)), "archive_sha256": a.digest(archive),
               "clean_room_report": str(stable_proof.relative_to(a.ROOT)), "clean_room_report_sha256": a.digest(stable_proof),
               "clean_room_log_sha256": a.digest(stable_log),
               "release_index_sha256": a.digest(index_path), "configured_tests": total,
               "receipt_inside_archive": False, "model_inference_calls_in_reproduction": 0, "gates": gate}
    for name in ("FINAL_RELEASE_RECEIPT.json", "release_gate.json", "NEXT_STAGE_COMPLETION_REPORT.md", "task_status.csv"):
        if (DOCS / name).exists():
            raise FileExistsError(f"Do not overwrite final handoff: {name}")
    a.write_json(DOCS / "FINAL_RELEASE_RECEIPT.json", receipt)
    a.write_json(DOCS / "release_gate.json", gate)
    rows = csv_rows(IMPL / "task_status_snapshot.csv")
    a.write_csv(DOCS / "task_status.csv", rows)
    lines = ["# Next-stage completion report — 2026-10-12 KST", "",
             "Overall: **PARTIAL_COMPLETION / BLOCKED_FOR_SUBMISSION**, not all N00–N13 PASS.",
             "Priority: Electronics / Generative AI, Large Language Models and Their Applications.",
             "User-approved route B: original W08 NOT_SATISFIED; no actual human labels or author/institution approvals.", "",
             "## Executed evidence", "",
             f"- Configured Python suite: {total} passed; Rust offline workspace log: 62 passed.",
             "- Historical archive-only replay: 31 byte-identical scientific files; old 120 cases / 240 reviews replayed, 119 unresolved.",
             "- Output-layer development: 600 requests / 272 Phi GPU calls. 251 stop, 21 length; five-required-field schema versus seven-bound-field scoring confounds ability/IR attribution.",
             "- Supplementary AI review: 16 calibration + 16 holdout cases × two model families = 64 schema-valid responses; all 16+16 unresolved on at least one field.",
             "- FinQA: 800 real requests on local RTX3090, no remote inference; independent archive-only case/summary replay identical.",
             "- In-memory policy: six prohibited/four allowed opportunities per capable condition; enforcement zero prohibited execution/false denial; refuse-only four false denials.",
             "- 500 legacy mutations / 1,500 gate decisions reconstructed; not recovered original mutation captures.", "",
             "## FinQA strict adapter-defined endpoints", "",
             "| Model | Condition | Correct | Finished | Adapter MISSING state |", "|---|---|---:|---:|---:|"]
    lines += [f"| {r['model']} | {r['condition']} | {r['N_correct']}/{r['N']} | {r['N_finished']}/{r['N']} | {r['N_missing']}/{r['N']} |" for r in csv_rows(DEFAULT / "finqa_holdout_v2/summary.csv")]
    lines += ["", "Not isolated reasoning accuracy or hallucination rates. Post-hoc diagnostics: 64 answer-marker-present responses rejected by strict end-anchored extraction; program-string JSON often describes arithmetic in prose rather than valid DSL. Percentage/benchmark-unit interpretation remains a confound. Primary scores and frozen raw captures are unchanged.", "",
              "## Corrected historical findings", "",
              "C8 224/418 complete + 48 partial = 272 coverage; deterministic trusted-slot control 272/418 complete. Control-only complete cases 48; C8-only 0. D1 legacy 206 complete / 125 unsupported becomes 74 / 326 under exact seven-field support, without raw changes. Old Phi HaluEval 72% was hardcoded; old Qwen 50% used a parse-failure default label. Native whole-output factuality is NOT_MEASURED.",
              "Eligible recorded source families: 238, not 418 independent row hashes; unknown dependence and single-repetition latency limits are explicit.", "",
              "## N00–N13 / W00–W15", "", "| Task | Status | Original work | Scope / remaining work |", "|---|---|---|---|"]
    lines += [f"| {r['task']} | {r['status']} | {r['original_work']} | {r['scope_and_remaining_work']} |" for r in rows]
    lines += ["", "## Required work-order questions", "",
              "1. HaluEval labels are replayed directly from historical raw text with missing/ambiguous states; D1 invokes the unchanged legacy pure scorer and independently compares seven exact fields. See metric_change_diagnostics.json, case_metric_transition.csv and halueval_extraction_audit.jsonl.",
              "2. All 498 original C5 invocations have raw references/hashes; the 226 exclusions are common UIR pre-execution policy/entity decisions, not absent raw candidates. replay_exclusion_audit.csv gives each case and reason. All-candidate projection additionally avoids selection by C8 success; zero fresh replay calls does not make original generation free.",
              "3. No necessity or incremental useful-answer benefit for SLM rendering is established; deterministic trusted-slot output wins completeness. The new five/seven-field mismatch prevents unbiased ability attribution. Input/IR comparison is still pending.",
              "4. Raw-only CNL preserves typed NOT/AND/OR, Boolean/decimal comparisons, supported units and explicit conditions separately from system provenance. Unknown tokens/fields, incomplete operands and unsupported requests clarify rather than dropping predicates; conformance is not free-NL accuracy.",
              "5. Effect sizes retain the same paired cases, but confidence intervals now resample 238 recorded families rather than 418 independent row hashes. Selected historical C8-minus-baseline complete-answer differences follow; all 18 comparisons/limits remain in paired_source_family_statistics.csv.", "",
              "| Baseline | Paired difference | Family bootstrap 95% interval | Recorded families |",
              "|---|---:|---|---:|"]
    selected = {"C1_NAIVE_RAG", "C5_GUARDRAIL_STYLE", "D1_EXTERNAL_CONSTRAINED_DECODING"}
    for stat in csv_rows(DEFAULT / "paired_source_family_statistics.csv"):
        if stat["metric"] == "complete" and stat["baseline"] in selected:
            lines.append(f"| {stat['baseline']} | {float(stat['risk_difference']):.6f} | [{float(stat['paired_cluster_ci_low']):.6f}, {float(stat['paired_cluster_ci_high']):.6f}] | {stat['N_source_clusters']} |")
    lines += ["", "6. Reviewer accuracy uses separate executable synthetic fixture labels only; model agreement is independently replayed, not treated as truth. No independent human semantic evidence exists; route B is approved and original W08 remains unmet.",
              "7. Holdout inference and finite sandbox action traces were actually executed, not merely prepared. They are not an external deployed-agent attack benchmark or recovered original raw mutation run.",
              "8. Extracted archive source reproduces 31 historical scientific files and new raw-to-metric scores with no development imports. This was performed by the current agent using separate replay code on the host interpreter, not by an independently appointed person/new machine and not a fresh GPU inference rerun.",
              "", "## Reproducibility and files", "",
              f"Archive: {archive.relative_to(a.ROOT)}", f"SHA-256: {a.digest(archive)}",
              "Detached FINAL_RELEASE_RECEIPT.json binds the ZIP, result index and clean-room proof; release_gate.json separates integrity/replay/semantic/manuscript/submission gates. The archive contains scope docs, code, raw data, tests and captured result hashes; it excludes private paper bytes, model weights, secrets, Git internals and symlinks.",
              "New source-linked research draft: projects/uir_base/results/110_mdpi_rev/manuscript_private/revision_next/draft_v4/. It is a provisional separate article, not full MDPI revision. Four result tables are generated; complete narrative numeric synchronization and actual PDF/source review remain pending. Original _47_UIR source is preserved.",
              "Scope: implementation/matched_baseline_protocol.md, rubric_change_log.md, fresh_failure_analysis.md, claim_evidence_matrix.csv, journal_target_verification.md and backmatter_verification.md.", "",
              "Archive-only replay with already installed CPU evaluation dependencies (no inference/network):", "",
              "~~~bash", "source /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate",
              "PYTHONPATH=src:. python -m projects.uir_base.scripts.next_verify \\",
              f"  --archive {archive.relative_to(a.ROOT)} --extract-to /tmp/NEW-NONEXISTENT-UIR-CHECKOUT",
              "python -m pytest -q", "cargo test --workspace --offline", "~~~", "",
              "Python -I uses extracted source, not editable development imports; the installed interpreter/dependencies are shared with the host. This is archive-only code/data reproduction, not independent human or new-machine replication. GPU artifact/templates/decoding/timestamp evidence is retained, not a second inference run. Frozen protocol status labels remain their pre-execution snapshots; separate execution manifests establish completed inference.", "",
              "## Remaining work", "",
              "Next development must align schema/DSL/unit interpretation on declared development data and compare equivalent-input representation layers. Do not optimize or silently rerun the evaluated holdout. Any future confirmatory run requires a new protocol and unused holdout.",
              "Actual author/institution confirmations, current Electronics instructions/template, publication rights/deposit, independent Clarivate/institution recognition and submission-day deadline/APC checks are pending. HTTP 429 limited publisher verification; search records are not a full live author-instructions check.",
              "No commit/push, submission, public upload or payment performed; AI-only design does not guarantee publication.", ""]
    (DOCS / "NEXT_STAGE_COMPLETION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--clean-report", type=Path)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.archive and args.clean_report:
        seal(args.archive.resolve(), args.clean_report.resolve())
    else:
        parser.error("Use --prepare or --archive / --clean-report")
