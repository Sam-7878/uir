"""Execute a real local checkpoint and stop before unmet confirmatory gates.

No hooks, remote writes, inference, scientific approval or submission are implicit.
"""
import argparse
from copy import deepcopy
import csv
from io import StringIO
import json
import platform
from pathlib import Path
import subprocess
import sys

from ..policy import ROOT, sha, utc, verify_manifest, write_once
from ..privacy import inventory
from ..conformance import evaluate
from ...representation_research.interpreter_python import interpret
from .artifacts import RunStore
from .interchange import InterchangeFailure, to_native, to_uir
from .protocol import matrix, precision_plan, preregistration_text
from .protection import scan_index
from .sources import acquire

DOCS = ROOT / "docs/work_reports/uir_base/116_electronics_confirmatory"
INPUT = ROOT / "docs/work_reports/uir_base/116_T15-T26"


def csv_text(rows, fields):
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def command(store, name, args, timeout=120):
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    store.write("logs/" + name + ".log", result.stdout + result.stderr)
    store.write("logs/" + name + "_receipt.json", {"command": args, "returncode": result.returncode,
                "timestamp_utc": utc(), "host_scope": "SAME_HOST_ONLY"})
    return result.returncode


def semantic_regression(store):
    cargo = "/home/sam/.cargo/bin/cargo"
    rc = command(store, "rust_build", [cargo, "build", "--offline", "-p", "poa-uir", "--bin", "uir_contract_eval"])
    if rc:
        return {"status": "BLOCKED_RUST_BUILD_FAILED"}
    result = evaluate()
    store.write("semantics/t22_boundary_regression.json", result)
    original = ROOT / "projects/uir_base/results/uir_repr_semantics_2026_10_13_v1/run_20261013T050400Z/semantic_differential_cases.jsonl"
    if not original.is_file():
        return {"status": "BLOCKED_MISSING_S41_FROZEN_INPUT"}
    cases = [json.loads(line) for line in original.read_text().splitlines() if line.strip()]
    if len(cases) != 41:
        raise ValueError("S41_ROW_COUNT_MISMATCH")
    binary = ROOT / "target/debug/uir_contract_eval"
    process = subprocess.run([str(binary)], input="".join(json.dumps(c["packet"]) + "\n" for c in cases),
                             text=True, capture_output=True, check=True, timeout=60)
    rust = [json.loads(line) for line in process.stdout.splitlines()]
    rows = []
    for case, answer in zip(cases, rust, strict=True):
        python = interpret(case["packet"])
        rows.append({"case_id": case["case_id"], "python": python, "rust": answer, "expected_state": case["expected_state"],
                     "agree": python == answer, "oracle_match": python["state"] == answer["state"] == case["expected_state"],
                     "split": "HISTORICAL_SYNTHETIC_REGRESSION_NOT_CONFIRMATORY"})
    store.jsonl("semantics/s41_regression.jsonl", rows)
    base = deepcopy(cases[0]["packet"])
    base["artifact"]["metadata"] = {"transport": "metadata-must-not-be-lost"}
    trace = []
    for name, mutate in (("roundtrip", lambda p: None),
                         ("unknown_section", lambda p: p["artifact"].update(unknown="reject")),
                         ("stale_authority", lambda p: p["authority"].update(version="revoked")),
                         ("digest_tamper", lambda p: p["artifact"].update(semantic_digest="0" * 64)),
                         ("stale_evidence", lambda p: p.update(current_evidence_version="stale"))):
        packet = deepcopy(base)
        mutate(packet)
        try:
            native = to_native(packet)
            restored = to_uir(native)
            trace.append({"case_id": name, "result": "ROUNDTRIP", "serialized_packet_equal": restored == packet,
                          "semantic_decision_equal": interpret(packet) == interpret(native) == interpret(restored)})
        except InterchangeFailure as exc:
            trace.append({"case_id": name, "result": "TYPED_FAILURE", "reason": str(exc)})
    store.jsonl("semantics/consumer_interchange_116.jsonl", trace)
    passed = (result["oracle_matches"] == 22 and all(r["agree"] and r["oracle_match"] for r in rows)
              and trace[0].get("serialized_packet_equal") is True and trace[0].get("semantic_decision_equal") is True
              and all(r["result"] == "TYPED_FAILURE" for r in trace[1:]))
    receipt = {"status": "PASS_SCOPED_REGRESSION" if passed else "FAILURES_PRESERVED_NOT_TUNED",
               "t_boundary_N": 22, "t_boundary_agree": result["agreement"], "s_N": len(rows),
               "s_agree": sum(r["agree"] for r in rows), "s_oracle_matches": sum(r["oracle_match"] for r in rows),
               "original_s_cases_sha256": sha(original), "interchange_tests": len(trace),
               "implementation_identity": "TWO_CODEBASES_SAME_AGENT", "new_independent_backend": False,
               "new_blind_mutation_holdout": "NOT_EXECUTED", "generalization_measured": False}
    store.write("semantics/independent_interpreter_receipt.json", receipt)
    return receipt


def prepare(directory, *, network=False, fetch_sources=False):
    for filename in ("T_STAGE_116_EXECUTION_REPORT.md", "T_STAGE_116_INDEPENDENT_REVIEW.md"):
        if (DOCS / filename).exists():
            raise FileExistsError("Existing work report; use a new explicit report version, never overwrite")
    store = RunStore(directory)
    ignored = subprocess.run(["git", "check-ignore", "--quiet", str(store.directory / "README.md")], cwd=ROOT)
    if ignored.returncode:
        raise ValueError("STAGE116_PRIVATE_IGNORE_MISSING")
    store.create()
    store.write("README.md", "# Stage 116 LOCAL ONLY\n\nReal privacy/engineering checkpoint and source candidates; NOT a confirmatory experiment.\n")
    store.write("environment_receipt.json", {"created_at_utc": utc(), "python": platform.python_version(),
                "platform": platform.platform(), "executable": sys.executable, "inference_calls": 0, "packages_changed": False,
                "layout_reorganization": False, "root_helper_extra_dirs": ["data", "reports", "figures", "resources", "logs", "manifests"]})
    store.write("input_lineage.json", {str(p.relative_to(ROOT)): sha(p) for p in sorted(INPUT.iterdir()) if p.is_file()})
    store.write("code_snapshot.json", {str(p.relative_to(ROOT)): sha(p) for p in sorted(Path(__file__).parent.glob("*.py"))})
    baseline = {}
    for name in ("run_20261020T122259Z", "run_20261020T122424Z", "run_20261020T122531Z"):
        p = ROOT / "projects/uir_base/results/uir_electronics_T_2026_10_13_v1" / name
        baseline[name] = {"verified_files": verify_manifest(p), "manifest_sha256": sha(p / "evidence_manifest.json"),
                          "claim_scope": "BYTES_ONLY_NO_RETROACTIVE_SCIENCE_COMPLETION"}
    store.write("historical_checkpoint_verification.json", baseline)
    receipt = inventory(network)
    receipt["owner_decision_2026_10_23"] = "ACKNOWLEDGE_UNRESOLVED_HISTORY_STRENGTHEN_NEW_LOCAL_ONLY"
    store.write("publication_gates/remote_visibility_receipt_116.json", receipt)
    rows = [{"path": name, "classification": "PRIVATE_PATH_CANDIDATE_REQUIRES_RIGHTS_REVIEW", "raw_bytes_disclosed": False}
            for name in receipt["current_protected_path_candidates"]]
    store.write("publication_gates/historical_exposure_classification_116.csv", csv_text(rows, ["path", "classification", "raw_bytes_disclosed"]))
    store.write("publication_gates/owner_privacy_decision_116.md", "# Owner decision, 2026-10-23\n\nAcknowledge historical public exposure as UNRESOLVED; strengthen new LOCAL ONLY evidence. No private remote, purge, force-push or visibility change.\n")
    store.write("publication_gates/remote_privacy_gate_116.json", {"status": "HISTORICAL_EXPOSURE_UNRESOLVED", "public_distribution": "BLOCKED", "local_research": "ALLOWED"})
    store.write("publication_gates/real_index_scan.json", scan_index(ROOT))
    store.write("publication_gates/private_backup_decision.md", "# Backup decision pending\n\nLOCAL ONLY is not encrypted backup. No backup location, retention, encryption or recovery target was authorized; none is certified.\n")
    test_rc = command(store, "protection_tests", [sys.executable, "-m", "pytest", "tests/uir_base/test_stage116.py", "-q",
                       "--junitxml=" + str(store.path("publication_gates/protected_paths_negative_tests.xml"))])
    store.write("publication_gates/content_and_history_scan_receipt.json", {"synthetic_index_tests_returncode": test_rc,
                "hooks": "NOT_INSTALLED_NO_SPECIFIC_INSTALL_APPROVAL", "ci": "NOT_INSTALLED",
                "history_inventory": "READ_ONLY_PATH_INVENTORY", "historical_content_secret_scan": "NOT_EXECUTED",
                "detector_limit": "BOUNDED_UTF8_JSON_JSONL_PRIVATE_MARKERS_ZIP_NOT_COMPLETE_DLP", "main_index_mutated": False})
    # Precision planning is recorded BEFORE candidate source retrieval or model calls.
    store.write("preregistration/T_power_precision_plan.json", precision_plan())
    store.write("preregistration/T_PREREGISTRATION_DRAFT.md", preregistration_text())
    store.write("preregistration/factorial_matrix_116.csv", csv_text(matrix(), list(matrix()[0])))
    store.write("preregistration/T_protocol_freeze_receipt.json", {"status": "NOT_PREREGISTERED", "draft_sha256": sha(store.path("preregistration/T_PREREGISTRATION_DRAFT.md")),
                "reason": "No blind independent gold/template disjointness/OS isolation/method review/precision signoff", "heldout_model_calls": 0})
    source = acquire(store) if fetch_sources else {"status": "NOT_EXECUTED", "physical_source_families": [], "records": []}
    store.write("source_registry/T17_gate.json", {"status": "BLOCKED_NO_BLIND_GOLD_OR_RAW_QUERY_FAMILY_SIGNOFF",
                "physical_source_families": source["physical_source_families"], "rights_approved_for_release": False,
                "old_source_family_overlap_zero": "NOT_CERTIFIED", "template_overlap_zero": "NOT_CERTIFIED", "gold_os_isolation": "NOT_EXECUTED"})
    store.write("source_registry/rights_matrix_116.csv", csv_text(source["records"], ["source_id", "parent_source_family", "role", "status", "license_status", "rights_class"]))
    store.write("source_registry/dataset_card_116.md", "# Source candidates, NOT a dataset\n\nPhysical bytes, retrieval receipts and candidate licenses are retained. Source choice is by the implementing agent. No raw KO/EN held-out queries, independently built gold or model outputs were generated. Documents alone do not establish document/template disjointness, source truth, independent gold or runtime OS isolation. No pilot/confirmatory sample was fabricated to reach 24/200. AI-only route is retained; human gold remains NOT_SATISFIED.\n")
    sem = semantic_regression(store)
    rust_rc = command(store, "rust_unit_tests", ["/home/sam/.cargo/bin/cargo", "test", "--offline", "-p", "poa-uir", "--bin", "uir_contract_eval"])
    fmt_rc = command(store, "rustfmt_check", ["/home/sam/.cargo/bin/cargo", "fmt", "--all", "--", "--check"])
    store.write("publication_gates/nonfunctional_quality.json", {"rust_unit_tests_returncode": rust_rc, "rustfmt_returncode": fmt_rc,
                "clippy": "NOT_EXECUTED", "full_workspace_rust_tests": "NOT_EXECUTED", "scope": "RECORD_FAILURES_DO_NOT_REFORMAT_FROZEN_SOURCE"})
    tasks = {"T15": "DONE_SCOPED_INVENTORY_HISTORY_UNRESOLVED", "T16": "PARTIAL_LOCAL_TESTS_HOOK_CI_NOT_INSTALLED",
             "T17": "PARTIAL_SOURCE_CANDIDATES_BLIND_GOLD_AND_DISJOINTNESS_BLOCKED", "T18": "DRAFT_NOT_PREREGISTERED",
             "T19": "PARTIAL_REGRESSION_ONLY_NO_NEW_BLIND_HOLDOUT", **{f"T{i}": "NOT_EXECUTED_DEPENDENCY_BLOCKED" for i in range(20, 26)},
             "T26": "PARTIAL_HONEST_GATES_NO_INDEPENDENT_REVIEW_OR_APPROVED_PACKAGES"}
    store.write("task_status.csv", csv_text([{"task_id": k, "execution_status": v} for k, v in tasks.items()], ["task_id", "execution_status"]))
    gates = {"ENGINEERING_CONFORMANCE_READY": "PASS_SCOPED_REGRESSION_ONLY" if sem.get("status") == "PASS_SCOPED_REGRESSION" and test_rc == rust_rc == 0 else "BLOCKED",
             "CONFIRMATORY_EVIDENCE_READY": "BLOCKED", "MANUSCRIPT_READY": "BLOCKED", "PUBLIC_RELEASE_READY": "BLOCKED", "SUBMISSION_READY": "BLOCKED",
             "native_prose_AUCR": "NOT_MEASURED", "FinQA_official_task_accuracy": "NOT_EXECUTED", "human_effort": "NOT_MEASURED", "independent_science_review": "NOT_EXECUTED"}
    store.write("publication_gates/final_stage_gate_116.json", gates)
    for kind in ("private_review", "public_release", "submission_package"):
        store.write("release/" + kind + "_manifest_116.json", {"kind": kind, "status": "NOT_PACKAGED", "files": [], "owner_approved": False,
                    "reason": "No fabricated empty archive PASS; science/rights/author prerequisites missing", "storage": "LOCAL_ONLY"})
    report = ("# Stage 116 execution checkpoint — PARTIAL / STOP RULE APPLIED\n\n"
              f"Results: `{store.directory.relative_to(ROOT)}`. Source commit: `{receipt['local_head']}`; exact dirty source hashes are separately recorded.\n\n"
              f"T15 current remote metadata: {receipt.get('remote_check')}; main matches local: {receipt.get('remote_main_matches_local_head', 'NOT_VERIFIED')}. "
              "Owner acknowledges unresolved history and strengthens LOCAL ONLY. Releases/forks are scoped to API visibility; authenticated private Actions artifacts and LFS payloads remain NOT_AUDITED. No remote mutation.\n\n"
              f"T16 synthetic real-index tests returncode={test_rc}; empty real index is not counted as an exercise. Hooks/CI NOT_INSTALLED; historical full-content scan NOT_EXECUTED. "
              "Limited content detection does not certify absence of arbitrary secrets.\n\n"
              f"T17 physically acquired candidate families: {source['physical_source_families']}. License candidates and raw bytes are retained, not release-approved. "
              "No signed document/template disjointness, independent request/gold roles or runtime OS gold isolation. T17 fails; T18–T23 CONFIRMATORY experiments prohibited. "
              "No 24/200 synthetic substitutes, no held-out inference, no use of old 24/272/418 as new confirmation.\n\n"
              "T18 eight-cell protocol and cluster-precision calculations are drafts, NOT PREREGISTERED. Two source families are not 200 independent trials.\n\n"
              f"T19 bounded historical/S1 regression receipt: `{sem}`. Native interchange is an adapter, NOT an independent backend. "
              "Implementers remain TWO_CODEBASES_SAME_AGENT; new blind mutation holdout NOT_EXECUTED. No failed holdout tuning.\n\n"
              "T20–T24 representation effects/query-aware inference/new whole-output/FinQA/cost/statistical confirmation NOT_EXECUTED. "
              "UIR versus specialized representation advantage remains unestablished. Native prose AUCR and human productivity NOT_MEASURED. "
              "S negative results (raw selector0/24, template24/24, model renderer7/24,192/192 identical pairs) remain historical, not new observations.\n\n"
              "T25 no new manuscript/PDF or fabricated authorship/ethics declarations. Journal direct fetch may be429; indexed announcement is not live portal approval. "
              "T26 three distinct package manifests explicitly NOT_PACKAGED; no human-author-approved submission archive exists. "
              "No independent review was fabricated. Source/raw snapshot retention is not science completion.\n\n"
              "## Required owner/scientific decision\n\nProvide an isolated source/question/gold curation and review route with rights and family/template proof, "
              "or explicitly authorize narrowing to a finite typed-contract conformance and bounded acceptance-control engineering study. "
              "The existing AI-only decision does not itself certify independent gold or make W08 human validation satisfied.\n")
    write_once(DOCS / "T_STAGE_116_EXECUTION_REPORT.md", report)
    write_once(DOCS / "T_STAGE_116_INDEPENDENT_REVIEW.md", "# Independent review — NOT EXECUTED\n\nThis file records a pending reviewer gate. The implementation agent's tests are self-checks, not an independent scientist/team or human audit. No reviewer identity or agreement is invented.\n")
    store.write("work_report_lineage.json", {str(p.relative_to(ROOT)): sha(p) for p in sorted(DOCS.glob("T_STAGE_116_*.md"))})
    seal_hash = store.seal()
    print(json.dumps({"results_dir": str(store.directory), "manifest_sha256": seal_hash, "verified_files": store.verify(),
                      "gates": gates, "source_families": source["physical_source_families"]}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "verify", "scan-index"))
    parser.add_argument("--results-dir", type=Path)
    parser.add_argument("--network", action="store_true")
    parser.add_argument("--fetch-sources", action="store_true")
    args = parser.parse_args()
    if args.command == "scan-index":
        result = scan_index(ROOT)
        print(json.dumps(result))
        raise SystemExit(1 if result["findings"] else 0)
    if args.results_dir is None:
        parser.error("--results-dir required, no implicit root/docs output")
    if args.command == "prepare":
        prepare(args.results_dir, network=args.network, fetch_sources=args.fetch_sources)
    else:
        print(json.dumps({"verified_files": RunStore(args.results_dir).verify()}))


if __name__ == "__main__":
    main()
