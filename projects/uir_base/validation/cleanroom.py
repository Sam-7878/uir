"""Fresh --copies venv + hash-pinned offline wheels + archive-only replay."""
import argparse
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from .common import ARCHIVE, OUT, ROOT, check_frozen, load, sha, utc, write


def run():
    check_frozen()
    wheels = OUT / "wheelhouse"
    for entry in load(OUT / "wheel_manifest.json")["files"]:
        if sha(wheels / entry["filename"]) != entry["sha256"]:
            raise ValueError("WHEEL_HASH_MISMATCH")
    directory = Path(tempfile.mkdtemp(prefix="uir-r00-"))
    subprocess.run([sys.executable, "-m", "venv", "--copies", str(directory / "venv")], check=True)
    python = directory / "venv/bin/python"
    env = {"PATH": "/usr/bin:/bin", "HOME": str(directory / "home"), "PYTHONNOUSERSITE": "1",
           "PIP_CONFIG_FILE": os.devnull, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}
    (directory / "home").mkdir()
    logs = []
    install = subprocess.run([str(python), "-m", "pip", "install", "--no-index", "--no-deps", "--require-hashes",
                              "--find-links", str(wheels), "-r", str(OUT / "requirements.lock")],
                             env=env, capture_output=True, text=True)
    logs.append(install.stdout + install.stderr)
    if install.returncode:
        raise RuntimeError(logs[-1])
    copied = directory / "frozen_v3.zip"; shutil.copyfile(ARCHIVE, copied)
    # Bootstrap code comes from the frozen archive, not from an editable import.
    bootstrap = directory / "bootstrap"; bootstrap.mkdir()
    import zipfile
    with zipfile.ZipFile(copied) as source:
        code = source.read("projects/uir_base/scripts/next_verify.py")
    (bootstrap / "verify.py").write_bytes(code)
    program = (
        "import importlib.util,sys,json,importlib.metadata as m; from pathlib import Path;"
        f"spec=importlib.util.spec_from_file_location('frozen_verifier', {str(bootstrap / 'verify.py')!r});"
        "mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);"
        f"mod.reproduce(Path({str(copied)!r}),Path({str(directory / 'checkout')!r}));"
        "print('INSTALLED_PACKAGES='+json.dumps(sorted(d.metadata['Name']+'=='+d.version for d in m.distributions())))"
    )
    result = subprocess.run([str(python), "-I", "-c", program], cwd=directory, env=env, capture_output=True, text=True)
    logs.append(result.stdout + result.stderr)
    with (OUT / "clean_room_v2.log").open("x") as handle:
        handle.write("\n".join(logs))
    if result.returncode:
        write(OUT / "independent_replay_report.json", {"status": "FAIL", "exit_code": result.returncode, "created_at_utc": utc()})
        raise RuntimeError(logs[-1])
    proof = load(directory / "checkout/clean_room_report.json")
    inventory = subprocess.check_output([str(python), "-I", "-c",
        "import sys,json,importlib.metadata as m;print(json.dumps({'prefix':sys.prefix,'base_prefix':sys.base_prefix,'paths':sys.path,'packages':sorted(d.metadata['Name']+'=='+d.version for d in m.distributions())}))"],
        cwd=directory, env=env, text=True)
    # Dependency absence is an executed negative test, not merely a missing package note.
    missing = subprocess.run([str(python), "-I", "-S", "-c", "import rfc8785"], env=env, capture_output=True, text=True)
    if missing.returncode == 0 or "ModuleNotFoundError" not in missing.stderr:
        raise ValueError("MISSING_DEPENDENCY_NEGATIVE_DID_NOT_FAIL")
    (OUT / "missing_rfc8785_negative.log").write_text(missing.stderr)
    report = {"status": "FRESH_VENV_ARCHIVE_REPLAY_PASS", "created_at_utc": utc(), "exit_code": result.returncode,
              "new_environment": json_load(inventory), "proof": proof, "missing_rfc8785_negative_exit": missing.returncode,
              "wheel_lock_sha256": sha(OUT / "requirements.lock"), "model_calls": 0,
              "physical_independent_machine": False, "independent_human_operator": False,
              "network_used_in_replay": False, "network_disable_enforced": False,
              "secret_read_proof": "NOT_OS_SANDBOXED; environment sanitized and extracted import scope checked, native/hidden host access not proven",
              "environment_path": str(directory), "host_python_shared_site_packages": False}
    write(OUT / "independent_replay_report.json", report)
    print(json_load(inventory)["packages"])
    print(report["status"])


def json_load(value):
    import json
    return json.loads(value)


if __name__ == "__main__":
    run()
