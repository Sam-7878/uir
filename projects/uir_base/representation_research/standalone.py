"""S01 collection gap and exact-fixture standalone verification, without inference."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from .common import PRIOR, ROOT, RELEASE_SHA, csvfile, relative, sha, textfile, utc, write
from .baseline import checked_zip

FIXTURES = ["projects/uir_base/results/uir_phase4d/frozen_inputs/" + n for n in
            ("smoke_runtime_100.jsonl", "finqa_runtime_200.jsonl")]


def execute(command, cwd, log, env=None):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, env=env)
    textfile(log, result.stdout + result.stderr)
    return {"command": command, "cwd": str(cwd), "exit_code": result.returncode,
            "log": str(log), "log_sha256": sha(log)}


def collected(log):
    return {line.strip() for line in Path(log).read_text().splitlines()
            if "::" in line and line.strip().startswith(("tests/", "projects/"))}


def run(out):
    archive = PRIOR / "uir_repr_private_review_release_v3.zip"
    checked_zip(archive, RELEASE_SHA)
    logs = out / "logs_and_tests"
    logs.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="uir-s-standalone-"))
    checkout = scratch / "checkout"
    with zipfile.ZipFile(archive) as source:
        source.extractall(checkout)  # checked_zip has rejected paths/symlinks/duplicates.
    envdir = scratch / "venv"
    venv = execute([sys.executable, "-m", "venv", "--copies", str(envdir)], scratch, logs / "venv.log")
    if venv["exit_code"]:
        raise RuntimeError("VENV_CREATION_FAILED")
    python = str(envdir / "bin/python")
    oldout = checkout / "projects/uir_base/results/uir_repr_validation_2026_10_12_v1"
    install = execute([python, "-m", "pip", "install", "--no-index", "--no-deps", "--require-hashes", "--find-links",
                       str(oldout / "wheelhouse"), "-r", str(oldout / "requirements.lock")], scratch, logs / "install.log")
    if install["exit_code"]:
        raise RuntimeError("OFFLINE_INSTALL_FAILED")
    env = {"PATH": "/usr/bin:/bin", "HOME": str(scratch), "PYTHONNOUSERSITE": "1", "OMP_NUM_THREADS": "1",
           "OPENBLAS_NUM_THREADS": "1", "PYTHONPATH": str(checkout / "src") + ":" + str(checkout)}
    before = execute([python, "-m", "pytest", "--collect-only", "-q", "tests/uir_base"], checkout, logs / "baseline_collection.log", env)
    checkout_collection = execute([sys.executable, "-m", "pytest", "--collect-only", "-q"], ROOT, logs / "checkout_collection.log")
    original = collected(logs / "baseline_collection.log")
    full = collected(logs / "checkout_collection.log")
    rows = []
    for case in sorted(full | original):
        rel = case.split("::", 1)[0]
        rows.append({"nodeid": case, "in_checkout": case in full, "in_baseline_uir_base": case in original,
                     "source_path": rel, "source_sha256": sha(ROOT / rel) if (ROOT / rel).is_file() else "MISSING",
                     "classification": "INCLUDED_UIR_BASE" if case in original else "OTHER_PROJECT_OR_PACKAGE_TEST_NOT_IN_PRIOR_UIR_BASE_COLLECTION",
                     "public_distribution": "PENDING_RIGHTS_REVIEW"})
    csvfile(out / "test_collection_diff.csv", rows)
    # Reproduce the missing-fixture failure first. Never hide the failed baseline.
    baseline_test = execute([python, "-m", "pytest", "-q", "tests/uir_base", "--junitxml=" + str(logs / "baseline_python.xml")], checkout, logs / "baseline_python.log", env)
    fixture_records = []
    for rel in FIXTURES:
        original_path = ROOT / rel
        if not original_path.is_file():
            raise FileNotFoundError("BLOCKED_PRIVATE_FIXTURE: " + rel)
        dest = checkout / rel
        if dest.exists():
            raise ValueError("FIXTURE_ALREADY_PRESENT_IN_BASELINE")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original_path, dest)
        fixture_records.append({"path": rel, "sha256": sha(dest), "bytes": dest.stat().st_size,
                                "source": "exact existing frozen runtime fixture; not regenerated", "rights": "PRIVATE_REVIEW_ONLY_PENDING_PUBLIC_RIGHTS"})
    patched_test = execute([python, "-m", "pytest", "-q", "tests/uir_base", "--junitxml=" + str(logs / "python_full_suite.xml")], checkout, logs / "python_full_suite.log", env)
    replay = execute([python, "-c", "from pathlib import Path;import json;from projects.uir_base.validation.release import reconstruct;print(json.dumps(reconstruct(Path.cwd())))"], checkout, logs / "cpu_raw_reconstruct.log", env)
    # Check the fail-closed fixture boundary on a fresh copy, without editing frozen inputs.
    test_missing = execute([python, "-c", "from pathlib import Path;from evaluation.uir_phase4d import audit_runtime_gold_access as a;a.FROZEN_DIR=Path('/nonexistent-uiR-fixtures');r=a.audit_runtime_files();assert r['status']=='FAIL';print(r)"], checkout, logs / "missing_fixture_negative.log", env)
    write(out / "offline_test_bundle_manifest.json", {"baseline_sha256": RELEASE_SHA, "added_fixtures": fixture_records,
          "scope": "complete delivered tests/uir_base suite; not whole-repository 296", "original_collection": len(original),
          "checkout_collection": len(full), "other_project_test_count": len(full - original), "rights": "PRIVATE_REVIEW_ONLY"})
    tool_environment = execute(["/bin/bash", "-c", "uname -sr; /home/sam/.cargo/bin/rustc --version; /home/sam/.cargo/bin/cargo --version; python3 --version"], scratch, logs / "host_toolchains.log")
    container = execute(["/bin/bash", "-c", "docker version"], scratch, logs / "container_availability.log")
    write(out / "clean_room_environment.json", {"created_at_utc": utc(), "scratch": str(scratch), "fresh_virtual_environment": True,
          "interpreter": python, "provisioned_by_host_python": sys.version, "original_repo_import_path_used": False,
          "GPU_used": False, "remote_db_used": False, "different_machine": False,
          "container_status": "UNAVAILABLE" if container["exit_code"] else "AVAILABLE_NOT_EXECUTED", "container_probe": container,
          "offline_install": install, "venv": venv, "collection": before, "checkout_collection": checkout_collection,
          "baseline_test": baseline_test, "patched_test": patched_test, "CPU_replay": replay, "missing_fixture_test": test_missing,
          "tool_environment": tool_environment})
    textfile(out / "offline_reproduction_status.md", "# Standalone scope\n\nA fresh copied CPython environment and extracted archive were used, with no original repository path or GPU. Exact missing fixtures are overlaid only in a new temporary checkout; baseline failure is retained. Full scope is the delivered UIR-base tests, NOT whole-repository 296. Other-project tests are itemized separately. Docker integration is unavailable; different-host/container replication is BLOCKED_ENVIRONMENT, owner: user/runtime provider. Fixture public rights remain pending. Rust execution is a separate command/log, not inferred from Python replay.\n")
    print(json.dumps({"S01": "PASS_UIR_BASE_SCOPED" if patched_test["exit_code"] == replay["exit_code"] == 0 else "FAIL",
                      "checkout_tests": len(full), "standalone_tests": len(original), "missing_test_files": fixture_records,
                      "different_host": "NOT_EXECUTED", "scratch": str(scratch)}))
