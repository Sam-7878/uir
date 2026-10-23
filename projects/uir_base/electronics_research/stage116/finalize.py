"""Evidence-linked checkpoint handoff, not a scientist or author approval."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from ..policy import ROOT, sha, write_once
from .artifacts import RunStore
from .runner import DOCS, csv_text


def finalize(directory, checkpoints):
    stores = [RunStore(p) for p in checkpoints]
    receipts = []
    for store in stores:
        receipts.append({"path": str(store.directory.relative_to(ROOT)), "verified_files": store.verify(),
                         "manifest_sha256": sha(store.path("evidence_manifest.json"))})
    initial, audit, financial = stores
    xml = ET.parse(audit.path("publication_gates/full_python_tests.xml")).getroot()
    suites = [xml] if xml.tag == "testsuite" else list(xml.findall("testsuite"))
    counts = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ("tests", "errors", "failures", "skipped")}
    sem = json.loads(audit.path("semantics/independent_interpreter_receipt.json").read_text())
    source = json.loads(financial.path("source_registry/source_registry_116.json").read_text())
    remote = json.loads(initial.path("publication_gates/remote_visibility_receipt_116.json").read_text())
    gates = {"ENGINEERING_CONFORMANCE_READY": "PASS_SCOPED_REGRESSION_ONLY" if counts["errors"] == counts["failures"] == 0 and sem["status"] == "PASS_SCOPED_REGRESSION" else "BLOCKED",
             "CONFIRMATORY_EVIDENCE_READY": "BLOCKED", "MANUSCRIPT_READY": "BLOCKED", "PUBLIC_RELEASE_READY": "BLOCKED", "SUBMISSION_READY": "BLOCKED",
             "human_ground_truth": "NOT_SATISFIED_AI_ONLY_ROUTE_B", "remote_privacy": "HISTORICAL_EXPOSURE_UNRESOLVED",
             "gold_OS_isolation": "NOT_EXECUTED", "preregistration": "DRAFT_NOT_FROZEN", "model_calls": 0,
             "independent_science_review": "NOT_EXECUTED", "full_python": counts,
             "physical_source_families": source["physical_source_families"], "physical_sources_are_not_confirmatory_gold": True}
    target = RunStore(directory)
    target.create()
    target.write("checkpoint_lineage.json", receipts)
    target.write("publication_gates/final_stage_gate_116.json", gates)
    original = ROOT / "projects/uir_base/results/uir_electronics_T_2026_10_13_v1/run_20261020T122531Z/task_status.csv"
    target.write("publication_gates/T00_T14_historical_status_unchanged.csv", original.read_bytes())
    tasks = [{"task_id": "T15", "status": "DONE_SCOPED_INVENTORY_UNRESOLVED_HISTORY_ACKNOWLEDGED"},
             {"task_id": "T16", "status": "PARTIAL_INDEX_CONTENT_NEGATIVES_PASS_HOOK_CI_NOT_INSTALLED"},
             {"task_id": "T17", "status": "PARTIAL_TWO_RAW_SOURCES_RIGHTS_BLIND_GOLD_DISJOINTNESS_ISOLATION_PENDING"},
             {"task_id": "T18", "status": "DRAFT_NOT_PREREGISTERED"},
             {"task_id": "T19", "status": "PARTIAL_REGRESSION_INTERCHANGE_NOT_NEW_BLIND_HOLDOUT"}]
    tasks += [{"task_id": f"T{i}", "status": "NOT_EXECUTED_CONFIRMATORY_DEPENDENCY_BLOCKED"} for i in range(20, 26)]
    tasks += [{"task_id": "T26", "status": "PARTIAL_BYTE_GATES_ONLY_REVIEW_AND_PACKAGES_BLOCKED"}]
    target.write("task_status.csv", csv_text(tasks, ["task_id", "status"]))
    report = ("# Stage116 final checkpoint handoff — PARTIAL, not T15–T26 completion\n\n"
              f"Authoritative local gate: `{target.directory.relative_to(ROOT)}/publication_gates/final_stage_gate_116.json`.\n\n"
              f"Current repository `{remote['repository']}`, local HEAD `{remote['local_head']}`, remote refs `{remote.get('remote_refs')}`, visibility `{remote.get('github_metadata', {}).get('visibility')}`. "
              "Read-only observations are timestamped in the initial receipt; no future-state claim. Owner chose unresolved-history acknowledgement plus new LOCAL ONLY. No push, history rewrite, visibility change, upload, submission, payment, hook installation, environment upgrade or layout reorganization.\n\n"
              "## Actually executed\n\n"
              "- Synthetic temporary Git repositories with nonempty indices: positive source and negative forced-private-path, disguised JSON/JSONL gold, nested ZIP, archive path, key-marker and symlink cases. Scanner reads indexed bytes even if the worktree is sanitized. Unknown binaries/oversize inputs fail closed; arbitrary-secret absence is NOT certified.\n"
              f"- Current-source full Python: {counts}. Tests use same host, not independent institution.\n"
              f"- S41 historical regression: {sem['s_agree']}/41 agree, {sem['s_oracle_matches']}/41 declared expected-state matches. T boundary regression: {sem['t_boundary_agree']}/22 agree. Five typed interchange traces, not an independent backend or blind holdout. TWO_CODEBASES_SAME_AGENT limitation retained.\n"
              f"- Two physical raw-source candidates: {source['physical_source_families']}. Cargo manifest/revision/license bytes; Treasury five raw fiscal rows. Treasury catalog API404 and both World Bank timeouts are retained. Candidate government-data rights still need explicit source-specific evidence; no blank license was promoted to approval.\n"
              "- Eight-cell matched design and family-based precision draft recorded before retrieval/inference. NOT PREREGISTERED, no 24/200 fabricated query cases and no model calls. Two parent families do not imply 200 independent trials.\n"
              "- Official MDPI target page physically fetched HTTP200. Title,15February2027,GeunseokYang and2400CHF text checks pass; browser-service429 is separately retained as a limitation of that channel, not proof of a closed SI. Logged-in submission/discount/author approval NOT verified.\n"
              "- Old checkpoints verified15/17/21 files; new execution checkpoints verified individually. Original adverse observations and immutable manifests remain unchanged.\n\n"
              "## Not completed / stop rule\n\n"
              "Independent source/question/gold roles, document/template disjointness, gold OS isolation and precision/method signoff are not established. "
              "Therefore T17 does not pass; T18–T23 confirmatory inference is prohibited. Requested-subset grounding, native-prose AUCR, actual protected-tool attacks, official FinQA task accuracy, independent consumer/developer effort and confirmatory statistics remain NOT_EXECUTED/NOT_MEASURED. "
              "No semantic superiority or UIR accuracy advantage is claimed. Historical S 0/24 raw selection,24/24 template,7/24 model renderer and192/192 equal pairs are not relabelled new confirmation.\n\n"
              "Rust unit tests pass within the evaluated binary scope; rustfmt --check fails and its log is retained. Clippy/full Rust workspace NOT_EXECUTED. "
              "Hooks/CI, authenticated private Actions artifacts, LFS payloads, full historical secret-content scan and backup approval remain incomplete.\n\n"
              "No new manuscript/PDF or author declarations were fabricated while dependent science gates were blocked. The independent-review file explicitly records NOT_EXECUTED. "
              "Three package manifests distinguish private/public/submission but all are NOT_PACKAGED; empty fake archives were not counted as passes. "
              "T00–T14 original status is preserved. ENGINEERING_CONFORMANCE_READY is scoped only; CONFIRMATORY_EVIDENCE_READY,MANUSCRIPT_READY,PUBLIC_RELEASE_READY,SUBMISSION_READY remain BLOCKED.\n\n"
              "## Decision needed before further research\n\n"
              "Please select whether to establish an isolated independent request/gold/review route plus rights/disjointness/OS evidence and continue confirmation, "
              "or explicitly narrow the article to finite typed-contract conformance and bounded acceptance-control engineering. No scope downgrade is assumed from the AI-only RouteB decision.\n")
    path = DOCS / "FINAL_T_STAGE_COMPLETION_REPORT.md"
    write_once(path, report)
    target.write("work_report_lineage.json", {str(path.relative_to(ROOT)): sha(path)})
    target.write("README.md", "# LOCAL ONLY final handoff\n\nT15–T26 PARTIAL. See the actual independent gates and child checkpoint hashes. No scientific or submission approval is implied.\n")
    target.seal()
    print(json.dumps({"verified_files": target.verify(), "results_dir": str(target.directory), "report": str(path), "gates": gates}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--checkpoints", type=Path, nargs=3, required=True)
    args = parser.parse_args()
    finalize(args.results_dir, args.checkpoints)
