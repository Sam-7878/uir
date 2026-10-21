"""R00 exact environment/wheel lock and snapshot provenance; never upgrade host."""
import argparse
import importlib.metadata as metadata
import platform
import subprocess
import sys
import zipfile
from .common import ARCHIVE, DOC, OLD, OUT, ROOT, check_frozen, csvfile, load, sha, utc, write

PACKAGES = ("rfc8785", "jsonschema", "attrs", "jsonschema-specifications", "referencing", "rpds-py",
            "typing-extensions", "numpy", "scipy", "PyYAML", "requests", "charset-normalizer",
            "idna", "urllib3", "certifi", "pytest", "iniconfig", "packaging", "pluggy", "Pygments")


def prepare():
    proof = check_frozen()
    versions = {n: metadata.version(n) for n in PACKAGES}
    OUT.mkdir(parents=True, exist_ok=True); DOC.mkdir(parents=True, exist_ok=True)
    requirements = OUT / "requirements.exact.txt"
    with requirements.open("x") as handle:
        handle.write("".join(f"{n}=={v}\n" for n, v in versions.items()))
    lock = {"created_at_utc": utc(), "python": platform.python_version(), "python_implementation": platform.python_implementation(),
            "platform": platform.platform(), "machine": platform.machine(), "packages": versions,
            "rustc": subprocess.check_output(["/home/sam/.cargo/bin/rustc", "--version"], text=True).strip(),
            "cargo": subprocess.check_output(["/home/sam/.cargo/bin/cargo", "--version"], text=True).strip(),
            "cargo_lock_sha256": sha(ROOT / "Cargo.lock"), "python_shared_environment_modified": False,
            "platform_scope": "Linux x86_64 CPython 3.14; not arbitrary platforms", "frozen": proof}
    write(OUT / "environment.lock", lock)
    v2 = ROOT / "projects/uir_base/results/110_mdpi_rev/uir_next_offline_source_evidence_v2.zip"
    with zipfile.ZipFile(v2) as before, zipfile.ZipFile(ARCHIVE) as after:
        old = {n: before.read(n) for n in before.namelist()}
        new = {n: after.read(n) for n in after.namelist()}
    rows = [{"path": n, "change": "ADDED" if n not in old else "MODIFIED" if old[n] != new[n] else "UNCHANGED",
             "v2_sha256": __import__("hashlib").sha256(old[n]).hexdigest() if n in old else None,
             "v3_sha256": __import__("hashlib").sha256(new[n]).hexdigest()} for n in sorted(new)]
    csvfile(OUT / "snapshot_changelog.csv", rows)
    delivery = ROOT / "projects/uir_base/results/110_mdpi_rev/110_mdpi_rev.zip"
    write(OUT / "input_provenance.json", {"created_at_utc": utc(), "v3": proof,
          "previous_work_order_sha256": sha(ROOT / "docs/work_reports/uir_base/110_mdpi_rev/UIR_Next_Development_Work_Order_2026-10-11.md"),
          "report_delivery_zip_status": "MISSING" if not delivery.is_file() else "PRESENT_UNCHECKED",
          "expected_delivery_zip_sha256": "007ae2715abb8a996d6376d5786d529d19608c7857769a5f2d7214ffe2e5b3e8",
          "detached_receipt_sha256": sha(ROOT / "projects/uir_base/results/110_mdpi_rev/FINAL_RELEASE_RECEIPT.json"),
          "modified_shared": [r["path"] for r in rows if r["change"] == "MODIFIED"],
          "N_v3_added": sum(r["change"] == "ADDED" for r in rows),
          "human_signoff": False, "physical_independent_machine": False})
    print(requirements)


def wheels():
    directory = OUT / "wheelhouse"; directory.mkdir(exist_ok=False)
    command = [sys.executable, "-m", "pip", "download", "--only-binary=:all:", "--no-deps",
               "-r", str(OUT / "requirements.exact.txt"), "--dest", str(directory)]
    subprocess.run(command, check=True)
    paths = sorted(directory.glob("*.whl"))
    if len(paths) != len(PACKAGES):
        raise RuntimeError("INCOMPLETE_WHEELHOUSE")
    rows = [{"filename": p.name, "sha256": sha(p), "bytes": p.stat().st_size} for p in paths]
    write(OUT / "wheel_manifest.json", {"status": "HASH_PINNED_PLATFORM_WHEELS", "files": rows})
    # Match each exact requested distribution to its wheel's own METADATA.
    requirements = []
    for p in paths:
        with zipfile.ZipFile(p) as wheel:
            text = wheel.read(next(n for n in wheel.namelist() if n.endswith(".dist-info/METADATA"))).decode()
        name = next(l[6:] for l in text.splitlines() if l.startswith("Name: "))
        version = next(l[9:] for l in text.splitlines() if l.startswith("Version: "))
        requirements.append(f"{name}=={version} --hash=sha256:{sha(p)}\n")
    with (OUT / "requirements.lock").open("x") as handle:
        handle.write("".join(sorted(requirements)))
    print("Wheel lock complete; install into a NEW --copies venv with --no-index --require-hashes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--wheels", action="store_true")
    args = parser.parse_args()
    if args.prepare: prepare()
    elif args.wheels: wheels()
    else: parser.error("Explicit --prepare or --wheels required")
