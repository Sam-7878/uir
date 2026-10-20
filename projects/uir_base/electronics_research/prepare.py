"""Prepare a bounded privacy checkpoint, never label it a completed T stage."""
import platform
import subprocess
import sys

from .policy import ROOT, SI, seal, sha, utc, validate_results_dir, write_once, publication_gate
from .privacy import inventory


def run(directory, *, network_metadata=False):
    directory = validate_results_dir(directory)
    if directory.exists():
        raise FileExistsError("RUN_ID_ALREADY_EXISTS")
    subprocess.run(["git", "check-ignore", "--quiet", str(directory / "README.md")], cwd=ROOT, check=True)
    # Gather before creating the run: failures must not leave a misleading receipt.
    receipt = inventory(network_metadata)
    directory.mkdir(parents=True, exist_ok=False)
    for subdir in ("scientific_public_candidates", "evaluation", "backend_conformance", "experiments",
                   "manuscript_private", "private_evaluator_only", "private_runtime_logs", "publication_gates", "work_reports"):
        (directory / subdir).mkdir()
    write_once(directory / "git_remote_receipt.json", receipt)
    inputs = ROOT / "docs/work_reports/uir_base/113_T00-T14"
    lineage = {p.name: {"sha256": sha(p), "source": str(p.relative_to(ROOT)), "access": "READ_ONLY"}
               for p in sorted(inputs.iterdir()) if p.is_file()}
    if not lineage:
        raise ValueError("EMPTY_WORK_ORDER_INPUT_SCAN")
    write_once(directory / "lineage_manifest.json", lineage)
    code_paths = list((ROOT / "projects/uir_base/electronics_research").glob("*.py")) + [
        ROOT / "projects/uir_base/representation_research/interpreter_python.py",
        ROOT / "tests/uir_base/test_t_local_privacy.py", ROOT / ".gitignore"]
    write_once(directory / "code_snapshot_manifest.json", {str(p.relative_to(ROOT)): sha(p) for p in sorted(code_paths)})
    historical = [
        ROOT / "projects/uir_base/results/uir_repr_semantics_2026_10_13_v1/run_20261013T050400Z/S_science_manifest.json",
        ROOT / "projects/uir_base/results/uir_electronics_T_2026_10_13_v1/run_20261020T122259Z/evidence_manifest.json"]
    write_once(directory / "historical_lineage.json", [{"path": str(p.relative_to(ROOT)),
                "sha256": sha(p) if p.is_file() else None, "status": "PRESENT_READ_ONLY" if p.is_file() else "MISSING",
                "claim": "BYTE_LINK_ONLY_NOT_REVALIDATION_OF_PRIOR_SCIENCE"} for p in historical
                if p.parent != directory])
    write_once(directory / "environment_receipt.json", {"python": platform.python_version(), "platform": platform.platform(),
               "timestamp_utc": utc(), "inference_executed": False, "packages_changed": False, "journal": SI})
    write_once(directory / "public_release_manifest.json", {"status": "NOT_PUBLIC", "files": [], "owner_approved": False})
    binary = ROOT / "target/debug/uir_contract_eval"
    cargo = "/home/sam/.cargo/bin/cargo"
    rust_build = subprocess.run([cargo, "build", "--offline", "-p", "poa-uir", "--bin", "uir_contract_eval"],
                                cwd=ROOT, text=True, capture_output=True, timeout=120)
    write_once(directory / "private_runtime_logs/rust_build.txt", rust_build.stdout + rust_build.stderr)
    write_once(directory / "backend_conformance/build_receipt.json", {"returncode": rust_build.returncode,
               "offline": True, "binary_freshness": "BUILD_CHECKED" if rust_build.returncode == 0 else "NOT_CERTIFIED"})
    if rust_build.returncode == 0 and binary.is_file():
        from .conformance import evaluate
        result = evaluate()
        write_once(directory / "backend_conformance/boundary_probes.json", result)
        write_once(directory / "backend_conformance/summary.json", {k: v for k, v in result.items() if k != "records"})
    rust_test = subprocess.run([cargo, "test", "--offline", "-p", "poa-uir", "--bin", "uir_contract_eval"],
                               cwd=ROOT, text=True, capture_output=True, timeout=120)
    write_once(directory / "private_runtime_logs/rust_test.txt", rust_test.stdout + rust_test.stderr)
    write_once(directory / "evaluation/rust_test_receipt.json", {"returncode": rust_test.returncode,
               "scope": "UIR_CONTRACT_EVAL_BINARY_UNIT_TESTS_ONLY", "host_scope": "SAME_HOST_ONLY"})
    tests = subprocess.run([sys.executable, "-m", "pytest", "tests/uir_base/test_t_local_privacy.py",
                            "tests/uir_base/test_s_representation_research.py", "-q",
                            "--junitxml=" + str(directory / "evaluation/protected_paths_test.xml")],
                           cwd=ROOT, text=True, capture_output=True, timeout=120)
    write_once(directory / "private_runtime_logs/pytest.txt", tests.stdout + tests.stderr)
    write_once(directory / "evaluation/test_receipt.json", {"returncode": tests.returncode,
               "command_scope": "T_LOCAL_GUARDS_AND_S_REGRESSION", "independent_review": False})
    write_once(directory / "privacy_architecture_decision.md", "# Owner decision\n\nPrivate reports and raw evidence are LOCAL ONLY. No private GitHub repository will be created.\n\n"
               "This supersedes the earlier proposed private-remote split. No upload, history rewrite, deletion, visibility change or push was performed. "
               "Git ignore prevents accidental new additions, not historical access or `git add -f`. Existing public-history exposure remains unresolved; "
               "history rewriting requires separate informed approval and cannot revoke cached copies. Local-only is not an encrypted backup.\n")
    write_once(directory / "results_path_policy.md", "# Local evidence policy\n\nAll new T-stage evidence belongs to a fresh canonical run directory. "
               "No symlinks, implicit root/docs outputs, frozen-input rewrites or resealing. All files default PRIVATE. "
               "Public candidates remain NOT_PUBLIC pending rights and owner byte-level approval. "
               "Run `python -m projects.uir_base.electronics_research scan-staged` before commits; hook/CI installation has NOT been performed.\n")
    tasks = {"T00": "PARTIAL_HISTORY_EXPOSURE_UNRESOLVED", "T01": "PARTIAL_LOCAL_GUARDS_IMPLEMENTED",
             "T02": "BLOCKED_NO_INDEPENDENT_SOURCE", "T03": "NOT_PREREGISTERED"}
    tasks.update({f"T{i:02}": "NOT_EXECUTED" for i in range(4, 15)})
    if rust_build.returncode == 0 and binary.is_file():
        tasks["T05"] = "PARTIAL_BOUNDARY_PROBES_EXECUTED_NOT_FULL_T05"
    write_once(directory / "task_status.csv", "task_id,execution_status\n" + "".join(f"{k},{v}\n" for k, v in tasks.items()))
    write_once(directory / "publication_gates/status.json", publication_gate({"REMOTE_PRIVACY": receipt["remote_privacy_gate"]}))
    report = ("# T-stage privacy checkpoint — incomplete\n\nImplemented local-only storage guards, write-once evidence, staged path scanner and read-only Git inventory. "
              "This is a technical self-check, NOT an independent review or completion of T00–T14.\n\n"
              "No new external source/gold was acquired, no preregistration certified, no model calls or manuscript changes made. "
              "See backend_conformance/summary.json for bounded synthetic boundary probes, if a Rust binary was available; they are not independent human validation. "
              "T02 requires licensed independent parent families and question/gold role separation before confirmatory experiments. "
              "AI-only Route B remains the selected design; W08 human evaluation is NOT SATISFIED. "
              "Arbitrary-prose AUCR, FinQA task accuracy and independent human development effort remain NOT_MEASURED here. "
              "Author, rights, remote privacy and submission approvals remain blocked/not certified.\n\n"
              "Next: authenticated artifacts/history exposure review, install explicitly approved CI controls, then independent-source protocol and bounded S1 mutation tests. "
              "No public/submission archive has been produced.\n")
    write_once(directory / "work_reports/T_STAGE_COMPLETION_REPORT.md", report)
    write_once(directory / "README.md", "# Private T-stage checkpoint\n\nLOCAL ONLY / NOT_PUBLIC / SUBMISSION_READY=BLOCKED.\n\nSee task_status.csv for actual execution scope. "
               "The detached evidence manifest excludes its own bytes. Do not append results or reseal this run; create a fresh run.\n")
    seal(directory)
    print(directory)
