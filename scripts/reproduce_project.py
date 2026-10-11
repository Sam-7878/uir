"""Public verification facade. Verification is NOT publication approval."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def verify(project):
    portal=ROOT/"projects"/project
    assert portal.is_dir()
    if project=="uir_base":
        release=portal/"results/mdpi_revision_2026_10_11"
        manifest=json.loads((release/"evidence_manifest.json").read_text())
        for row in manifest["sources"]:
            actual=hashlib.sha256((ROOT/row["path"]).read_bytes()).hexdigest()
            if actual!=row["sha256"]:
                raise ValueError(f"Evidence mismatch: {row['path']}")
        actual=hashlib.sha256((ROOT/manifest["evaluator"]).read_bytes()).hexdigest()
        if actual!=manifest["evaluator_sha256"]:
            raise ValueError("Evaluator changed; rebuild revision release")
        print(f"PASS: {len(manifest['sources'])} immutable input files and evaluator; no publication readiness implied")
    else:
        # Don't fabricate canonical releases for projects not being revised here.
        sources=list((portal/"evaluation").rglob("*.py"))
        if not sources:
            raise ValueError("Project source missing")
        print(f"PASS: {project} source portal, {len(sources)} Python files. Historical scientific results not revalidated.")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("project",choices=["uir_base","uir_security","uir_law"])
    parser.add_argument("mode",choices=["verify","tables","tests"])
    args=parser.parse_args()
    if args.mode=="verify":
        verify(args.project)
    elif args.mode=="tables":
        if args.project!="uir_base":
            raise SystemExit("No new table release declared for this project; use its historical campaign explicitly")
        subprocess.run([sys.executable,"-m","projects.uir_base.scripts.revision_audit"],cwd=ROOT,check=True)
        subprocess.run([sys.executable,"-m","projects.uir_base.scripts.revision_support"],cwd=ROOT,check=True)
    else:
        testdir=ROOT/"tests"/args.project
        if not testdir.exists():
            testdir=ROOT/"projects"/args.project/"evaluation/law200/tests"
        subprocess.run([sys.executable,"-m","pytest","-q",str(testdir)],cwd=ROOT,check=True)


if __name__=="__main__":
    main()
