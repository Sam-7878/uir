"""S13 private combined release and fresh offline reproduction.

No commit, upload, submission, approval, or GPU inference is performed here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
from .common import DOC, PRIOR, ROOT, RELEASE_SHA, csvfile, load, read, relative, sha, textfile, utc, write
from .baseline import checked_zip


def export(out, destination):
    if destination.exists():
        raise FileExistsError("NO_RELEASE_REPLACEMENT")
    baseline = PRIOR / "uir_repr_private_review_release_v3.zip"
    checked_zip(baseline, RELEASE_SHA)
    overlay = {}
    for directory in (ROOT / "projects/uir_base/representation_research", ROOT / "protocol", out, DOC):
        for path in directory.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or any(p.startswith("release_verification") for p in path.parts) or path.suffix in {".pyc", ".zip"}:
                continue
            if path.is_symlink():
                raise ValueError("NO_SYMLINK_RELEASE")
            overlay[relative(path)] = path
    for path in [ROOT / "src/uir_common/query_contract.py", ROOT / "tests/uir_base/test_s_representation_research.py",
                 ROOT / "crates/poa-uir/src/bin/uir_contract_eval.rs", PRIOR / "111_validation.zip", baseline]:
        overlay[relative(path)] = path
    from .standalone import FIXTURES
    for rel in FIXTURES:
        overlay[rel] = ROOT / rel
    from .whole_suite import files as whole_suite_files
    for path in whole_suite_files():
        overlay[relative(path)] = path
    records = []
    with zipfile.ZipFile(baseline) as original, zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as result:
        for name in sorted(set(original.namelist()) | set(overlay)):
            if name == "archive_manifest.json":
                continue
            info = None if name in overlay else original.getinfo(name)
            if info is not None and info.is_dir():
                continue
            content = overlay[name].read_bytes() if name in overlay else original.read(name)
            result.writestr(name, content)
            records.append({"path": name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
        result.writestr("archive_manifest.json", json.dumps({"files": records, "scope": "PRIVATE_REVIEW_ONLY; public rights and author approval pending",
                "baseline_release_sha256": RELEASE_SHA, "self_hash": "NOT_APPLICABLE_DETACHED_RECEIPT"}, indent=2, sort_keys=True))
    return {"archive": relative(destination), "archive_sha256": sha(destination), "N_manifest_files": len(records), "created_at_utc": utc(),
            "rights": "PRIVATE_REVIEW_ONLY"}


def reproduce(archive, report_dir):
    report_dir.mkdir(parents=True, exist_ok=True)
    verified = checked_zip(archive)
    scratch = Path(tempfile.mkdtemp(prefix="uir-s-final-release-"))
    checkout = scratch / "checkout"
    with zipfile.ZipFile(archive) as source:
        source.extractall(checkout)
    envdir = scratch / "venv"
    from .standalone import execute
    venv = execute([sys.executable, "-m", "venv", "--copies", str(envdir)], scratch, report_dir / "venv.log")
    if venv["exit_code"]:
        raise RuntimeError("VENV_FAILED")
    python = str(envdir / "bin/python")
    old = checkout / "projects/uir_base/results/uir_repr_validation_2026_10_12_v1"
    install = execute([python, "-m", "pip", "install", "--no-index", "--no-deps", "--require-hashes", "--find-links", str(old / "wheelhouse"),
                       "-r", str(old / "requirements.lock")], scratch, report_dir / "install.log")
    if install["exit_code"]:
        raise RuntimeError("OFFLINE_LOCK_INSTALL_FAILED")
    result_dir = next((checkout / "projects/uir_base/results/uir_repr_semantics_2026_10_13_v1").glob("run_*"))
    build_install = execute([python, "-m", "pip", "install", "--no-index", "--no-deps", "--require-hashes", "--find-links",
        str(result_dir / "build_wheelhouse"), "-r", str(result_dir / "build_requirements.lock")], scratch, report_dir / "build_install.log")
    editable = execute([python, "-m", "pip", "install", "--no-index", "--no-build-isolation", "--no-deps", "-e", str(checkout)],
                       scratch, report_dir / "editable_install.log")
    if build_install["exit_code"] or editable["exit_code"]:
        raise RuntimeError("OFFLINE_PROJECT_INSTALL_FAILED")
    # Execute tests/replays in a real isolated mount+network namespace. The
    # physical host, interpreter and Rust toolchain provisioning remain shared.
    import shlex
    from .isolation import command
    prefix = ("mount -t tmpfs -o size=1m uir-s-source-hidden /mnt/d/_Work/goat_bank\n"
              "test ! -e /mnt/d/_Work/goat_bank/uir/Cargo.toml\n"
              f"cd {shlex.quote(str(checkout))}\n")
    tests = execute(command(prefix + f"PYTHONPATH=src:. {shlex.quote(python)} -m pytest -q "
                    f"--junitxml={shlex.quote(str(scratch / 'standalone_python.xml'))}"), scratch, report_dir / "standalone_python.log")
    if (scratch / "standalone_python.xml").exists():
        shutil.copyfile(scratch / "standalone_python.xml", report_dir / "standalone_python.xml")
    # Archive includes exactly the selected S run; absolute paths are resolved in
    # the extracted checkout, never imported from the original repository.
    program = ("from pathlib import Path;import json;from projects.uir_base.validation.release import reconstruct as r;"
               "from projects.uir_base.representation_research.replay import reconstruct as s;"
               f"print(json.dumps({{'R':r(Path.cwd()),'S':s(Path({str(result_dir)!r}))}}))")
    replay = execute(command(prefix + f"PYTHONPATH=src:. {shlex.quote(python)} -c {shlex.quote(program)}"), scratch, report_dir / "CPU_raw_replay.log")
    # All locked Rust dependencies are supplied by the immutable vendor sources.
    config = checkout / ".cargo/config.toml"
    if not config.exists():
        textfile(config, '[source.crates-io]\nreplace-with = "s-stage-vendor"\n[source.s-stage-vendor]\ndirectory = "projects/uir_base/results/uir_repr_validation_2026_10_12_v1/rust_vendor"\n')
    cargoenv = {"PATH": "/home/sam/.cargo/bin:/usr/bin:/bin", "HOME": str(scratch), "RUSTUP_HOME": "/home/sam/.rustup",
                "CARGO_HOME": str(scratch / "cargo-home"), "CARGO_BUILD_JOBS": "2", "CARGO_TARGET_DIR": str(scratch / "cargo-target")}
    rust = execute(command(prefix + "/home/sam/.cargo/bin/cargo test --offline --locked --workspace --all-features"), scratch, report_dir / "standalone_rust.log", cargoenv)
    environment = {"status": "PASS_SCOPED" if tests["exit_code"] == replay["exit_code"] == rust["exit_code"] == 0 else "FAIL",
                   "archive_sha256": verified["archive_sha256"], "N_manifest_files": verified["manifest_tracked"],
                   "created_at_utc": utc(), "namespace": "actual user/mount/network isolation", "original_workspace_hidden": True,
                   "same_physical_host": True, "shared_interpreter_toolchain_provisioning": True, "GPU_model_calls": 0,
                   "scratch": str(scratch), "venv": venv, "install": install, "build_install": build_install, "editable_install": editable,
                   "python_tests": tests, "CPU_replay": replay, "rust_tests": rust,
                   "Python_scope": "entire repository collection: prior296 plus32new S tests; exact-source closure included",
                   "network_replay": "unshare network namespace plus pip --no-index/cargo --offline", "independent_human_replication": False}
    write(report_dir / "S_FINAL_REPRODUCE_REPORT.json", environment)
    print(json.dumps(environment))
    if environment["status"] != "PASS_SCOPED":
        raise RuntimeError("OFFLINE_REPRODUCTION_FAILED_SEE_PRESERVED_REPORT")
    return environment


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--reproduce", type=Path)
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args()
    if args.export:
        if not args.out:
            parser.error("--out required with --export")
        print(json.dumps(export(args.out.resolve(), args.export.resolve())))
    elif args.reproduce:
        if not args.report_dir:
            parser.error("--report-dir required with --reproduce")
        reproduce(args.reproduce.resolve(), args.report_dir.resolve())
    else:
        parser.error("choose --export or --reproduce")
