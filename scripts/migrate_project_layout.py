"""Recoverable mechanical migration; hashes sources and raw evidence before moving."""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ("uir_base", "uir_security", "uir_law")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def alias(source, target):
    if source.is_symlink():
        if source.resolve() != target.resolve():
            raise RuntimeError(f"Conflicting alias: {source}")
    elif source.exists():
        raise RuntimeError(f"Refusing to overwrite {source}")
    else:
        source.parent.mkdir(parents=True, exist_ok=True)
        source.symlink_to(os.path.relpath(target, source.parent), target_is_directory=True)


def main():
    manifest = ROOT / "docs/work_reports/uir_base/107_Astra_review/layout_migration_manifest.json"
    if manifest.exists():
        raise SystemExit("Already migrated; verify manifest instead of re-running")
    moves = [(ROOT / "llm_trust", ROOT / "src/llm_trust")]
    for project in PROJECTS:
        portal = ROOT / "projects" / project
        portal.mkdir(parents=True, exist_ok=True)
        for kind in ("evaluation", "results"):
            old = ROOT / kind / project
            if old.is_dir():
                moves.append((old, portal / kind))
        for kind in ("scripts", "reports", "paper/current"):
            (portal / kind).mkdir(parents=True, exist_ok=True)
        (ROOT / "archive" / project / "results").mkdir(parents=True, exist_ok=True)
    rows = []
    for old, new in moves:
        if new.exists():
            raise RuntimeError(f"Refusing to overwrite {new}")
        for path in sorted(old.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                rows.append({"old_path": str(path.relative_to(ROOT)), "new_path": str((new / path.relative_to(old)).relative_to(ROOT)), "sha256_before": sha(path)})
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old), str(new))
        alias(old, new)
    for project in PROJECTS:
        portal = ROOT / "projects" / project
        for kind in ("evaluation", "results"):
            directory = portal / kind
            if directory.is_dir():
                for child in directory.iterdir():
                    if child.is_dir() and child.name != "__pycache__":
                        alias(ROOT / kind / child.name, child)
        alias(portal / "reports/work_reports", ROOT / "docs/work_reports" / project)
    active = {"uir_phase4d", "uir_phase4e", "uir_phase4f"}
    base = ROOT / "projects/uir_base/results"
    for old in list(base.iterdir()):
        if old.is_dir() and old.name not in active and not old.is_symlink():
            new = ROOT / "archive/uir_base/results" / old.name
            shutil.move(str(old), str(new))
            alias(old, new)
    rewritten = []
    pattern = re.compile(r"((?:ROOT|REPO|REPO_ROOT|root_dir|project_root|root|base)\s*=\s*)Path\(__file__\)\.resolve\(\)\.parents\[\d+\]")
    for path in (ROOT / "projects").rglob("*.py"):
        content = path.read_text(encoding="utf-8")
        changed = pattern.sub(r"\1next(p for p in Path(__file__).resolve().parents if (p / 'Cargo.toml').is_file())", content)
        changed = changed.replace("REPO_ROOT = PACKAGE_ROOT.parents[2]", "REPO_ROOT = next(p for p in PACKAGE_ROOT.parents if (p / 'Cargo.toml').is_file())")
        if changed != content:
            path.write_text(changed, encoding="utf-8")
            rewritten.append(str(path.relative_to(ROOT)))
    for row in rows:
        row["sha256_after"] = sha(ROOT / row["new_path"])
        row["bytes_preserved"] = row["sha256_before"] == row["sha256_after"]
        if not row["bytes_preserved"] and not row["new_path"].endswith(".py"):
            raise RuntimeError(f"Non-source bytes changed: {row['new_path']}")
    manifest.write_text(json.dumps({"moves": rows, "mechanical_source_rewrites": rewritten, "raw_bytes_preserved": all(r["bytes_preserved"] for r in rows if not r["new_path"].endswith(".py"))}, indent=2) + "\n")
    print(f"Migrated {len(rows)} files; rewrote repository roots in {len(rewritten)} Python files")


if __name__ == "__main__":
    main()
