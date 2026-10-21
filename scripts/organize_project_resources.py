"""Audited, byte-preserving directory relocation; explicit apply, no aliases.

This is a layout operation, NOT scientific revalidation or a Git publication.
Every destination is preflighted before the first move. No merging or overwriting.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from uir_common.paths import PROJECTS, relocated_relative, repo_root

ROOT = repo_root()
TASK = "114_project_layout_2026_10_21"


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def plan(root=ROOT):
    moves = []
    for project in sorted(PROJECTS):
        # Owner exception: never relocate docs/work_reports.
        archive = root / "archive" / project / "results"
        if archive.is_dir():
            for task in sorted(archive.iterdir()):
                moves.append((task, root / relocated_relative(str(task.relative_to(root)))))
        for kind in ("formal", "evaluation", "architecture"):
            source = root / "docs" / kind / project
            if source.is_dir():
                moves.append((source, root / relocated_relative(str(source.relative_to(root)))))
    for name in ("_47_UIR", "_47_UIR_revision_next", "_47_1_UIR_ZTA", "_47_2_UIR_Law"):
        source = root / "docs/papers" / name
        if source.is_dir():
            moves.append((source, root / relocated_relative(str(source.relative_to(root)))))
    references = root / "docs/papers/[RES]"
    if references.is_dir():
        moves.append((references, root / "docs/resources/reference_literature"))
    for source, target in moves:
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"Destination exists; no merge allowed: {target}")
        if any(p.is_symlink() for p in (source, *source.parents, target, *target.parents)):
            raise ValueError("Symlink in relocation")
        if any(p.is_symlink() for p in source.rglob("*")):
            raise ValueError(f"Symlink inside source: {source}")
    return moves


def apply(root=ROOT):
    moves = plan(root)
    if not moves:
        raise ValueError("Empty relocation plan; refusing a false success")
    receipt = root / "projects/uir_base/results" / TASK / "manifests/relocation_manifest.json"
    if receipt.exists():
        raise FileExistsError(receipt)
    records = []
    for source, target in moves:
        files = sorted(p for p in source.rglob("*") if p.is_file()) if source.is_dir() else [source]
        for path in files:
            suffix = path.relative_to(source) if source.is_dir() else Path()
            records.append({"old_path": str(path.relative_to(root)), "new_path": str((target / suffix).relative_to(root)),
                            "sha256": digest(path), "size": path.stat().st_size})
    receipt.parent.mkdir(parents=True, exist_ok=True)
    pending = receipt.with_name("relocation_plan.json")
    document = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "scope": "LAYOUT_ONLY_NOT_SCIENCE_REVALIDATION",
                "directories": [{"old": str(a.relative_to(root)), "new": str(b.relative_to(root))} for a, b in moves],
                "files": records, "public_approved": False, "storage": "LOCAL_ONLY"}
    with pending.open("x") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
    for source, target in moves:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
    for row in records:
        if digest(root / row["new_path"]) != row["sha256"] or (root / row["old_path"]).exists():
            raise ValueError(f"Relocation integrity failure: {row['old_path']}")
    document["all_file_hashes_preserved"] = True
    with receipt.open("x") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
    # Remove only explicitly enumerated, now-empty containers. Never recursive delete.
    for parent in ("docs/work_reports/uir_base", "docs/work_reports/uir_security", "docs/work_reports/uir_law",
                   "docs/work_reports", "docs/papers", "docs/formal", "docs/evaluation",
                   "archive/uir_base/results", "archive/uir_base", "archive/uir_security/results", "archive/uir_security",
                   "archive/uir_law/results", "archive/uir_law", "archive"):
        path = root / parent
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    return {"directories_moved": len(moves), "files_verified": len(records), "manifest": str(receipt)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(apply() if args.apply else [{"old": str(a.relative_to(ROOT)), "new": str(b.relative_to(ROOT))}
                                               for a, b in plan()], ensure_ascii=False, indent=2))
