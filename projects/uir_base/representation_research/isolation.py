"""Actual Linux user/mount/network namespace checks; not a host security theorem."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
from .common import ROOT, jsonl, load, read, sha, textfile, utc, write


def command(script):
    return ["unshare", "-Urnm", "--fork", "/bin/bash", "-c", "set -eu\nmount --make-rprivate /\n" + script]


def gold(out):
    evidence_out = out / "gold_boundary_v2"
    hidden = out / "evaluator_only"
    runtime = out / "runtime/query_aware_dev.jsonl"
    target = hidden / "query_aware_gold.jsonl"
    bootstrap = (f"mount -t tmpfs -o size=1m uir-s-gold-hidden {shlex.quote(str(hidden))}\n"
                 f"cd {shlex.quote(str(ROOT))}\n"
                 f"PYTHONPATH=src:. {shlex.quote(sys.executable)} -m projects.uir_base.representation_research.runtime_worker "
                 f"--runtime {shlex.quote(str(runtime))} --probe-gold {shlex.quote(str(target))}")
    # Same runtime run twice, once before and once after evaluator-only temp labels
    # are changed. The actual frozen gold is never edited.
    first = subprocess.run(command(bootstrap), capture_output=True, text=True)
    textfile(evidence_out / "gold_isolation_test.log", first.stdout + first.stderr)
    if first.returncode or not first.stdout.startswith('{"probe": "GOLD_READ_BLOCKED"}'):
        write(evidence_out / "gold_isolation_status.json", {"status": "BLOCKED_RUNTIME_ISOLATION", "exit_code": first.returncode})
        raise RuntimeError("NO_KERNEL_GOLD_BOUNDARY")
    import tempfile
    scratch = Path(tempfile.mkdtemp(prefix="uir-s-grader-mutation-"))
    altered = [{**row, "expected_ids": ["WRONG_EVALUATOR_LABEL"]} for row in read(target)]
    changed = scratch / "changed_gold.jsonl"
    jsonl(changed, altered)
    # Bind the changed evaluator bytes over the canonical gold path in this
    # private namespace BEFORE hiding that directory from the runtime process.
    changed_bootstrap = f"mount --bind {shlex.quote(str(changed))} {shlex.quote(str(target))}\n" + bootstrap
    second = subprocess.run(command(changed_bootstrap), capture_output=True, text=True)
    textfile(evidence_out / "gold_mutation_invariance.log", second.stdout + second.stderr)
    if second.returncode or second.stdout != first.stdout:
        raise ValueError("RUNTIME_DEPENDS_ON_EVALUATOR_LABELS")
    write(evidence_out / "gold_isolation_status.json", {"status": "PASS_SCOPED_KERNEL_NAMESPACE", "created_at_utc": utc(),
          "runtime_sha256": sha(runtime), "gold_hash_only_for_grader": sha(target), "run1_exit": first.returncode,
          "run2_exit": second.returncode, "outputs_identical": True, "gold_directory_hidden_by_kernel_mount": True,
          "network_namespace_separate": True, "scope": "new evaluator-only directory at canonical path; not protection against compromised host/root or arbitrary aliases",
          "mutated_evaluator_file_sha256": sha(changed), "mutated_labels": len(altered),
          "canonical_path_overlay_before_isolation": True, "supersedes": "v1 pilot changed an unrelated evaluator-only file; not label-mutation evidence",
          "frozen_gold_modified": False})


def standalone_namespace(out, scratch):
    checkout = scratch / "checkout"
    python = scratch / "venv/bin/python"
    logs = out / "logs_and_tests"
    prefix = ("mount -t tmpfs -o size=1m uir-s-original-hidden /mnt/d/_Work/goat_bank\n"
              "test ! -e /mnt/d/_Work/goat_bank/uir/Cargo.toml\n"
              f"cd {shlex.quote(str(checkout))}\n")
    test = subprocess.run(command(prefix + f"PYTHONPATH=src:. {shlex.quote(str(python))} -m pytest -q tests/uir_base "
                                 f"--junitxml={shlex.quote(str(scratch / 'namespace_python.xml'))}"), capture_output=True, text=True)
    textfile(logs / "namespace_python.log", test.stdout + test.stderr)
    if (scratch / "namespace_python.xml").exists():
        import shutil
        shutil.copyfile(scratch / "namespace_python.xml", logs / "namespace_python.xml")
    program = "from pathlib import Path;import json;from projects.uir_base.validation.release import reconstruct;print(json.dumps(reconstruct(Path.cwd())))"
    replay = subprocess.run(command(prefix + f"PYTHONPATH=src:. {shlex.quote(str(python))} -c {shlex.quote(program)}"), capture_output=True, text=True)
    textfile(logs / "namespace_reconstruct.log", replay.stdout + replay.stderr)
    write(out / "namespace_standalone_report.json", {"created_at_utc": utc(), "test_exit_code": test.returncode,
          "replay_exit_code": replay.returncode, "original_workspace_hidden": True, "network_namespace_separate": True,
          "same_physical_host": True, "GPU_inference_calls": 0, "kernel_namespace_container": True,
          "not_full_rootfs_image": True, "fixture_overlay": "exact bytes only in temporary extracted checkout"})
