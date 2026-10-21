"""Apply the owner's exception: private work_reports retains its original root."""
import json
from pathlib import Path
from uir_common.paths import repo_root
from organize_project_resources import digest

ROOT = repo_root()
OUT = ROOT / "projects/uir_base/results/114_project_layout_2026_10_21/manifests"


def main():
    manifest = json.loads((OUT / "relocation_manifest.json").read_text())
    moves = [row for row in manifest["directories"] if row["old"].startswith("docs/work_reports/")]
    files = [row for row in manifest["files"] if row["old_path"].startswith("docs/work_reports/")]
    for row in moves:
        if not (ROOT / row["new"]).is_dir() or (ROOT / row["old"]).exists():
            raise ValueError("WORK_REPORT_RESTORE_CONFLICT")
    for row in files:
        if digest(ROOT / row["new_path"]) != row["sha256"]:
            raise ValueError("WORK_REPORT_BYTES_CHANGED")
    for row in moves:
        target = ROOT / row["old"]
        target.parent.mkdir(parents=True, exist_ok=True)
        (ROOT / row["new"]).rename(target)
    for row in files:
        if digest(ROOT / row["old_path"]) != row["sha256"]:
            raise ValueError("WORK_REPORT_RESTORE_HASH_MISMATCH")
    with (OUT / "work_reports_owner_exception.json").open("x") as handle:
        json.dump({"owner_decision": "KEEP_DOCS_WORK_REPORTS_LOCAL_PRIVATE_IN_ORIGINAL_LOCATION",
                   "directories_restored": moves, "files": files, "all_file_hashes_preserved": True}, handle, indent=2)
    candidates = [ROOT / "README.md"]
    for folder in ("projects", "tests"):
        for path in (ROOT / folder).rglob("*.py"):
            if any(part in {"results", "paper", "data", "vendor"} for part in path.relative_to(ROOT).parts):
                continue
            candidates.append(path)
    count = 0
    for path in candidates:
        before = path.read_text()
        after = before
        for row in moves:
            after = after.replace(row["new"], row["old"])
        if before != after:
            path.write_text(after)
            count += 1
    print(json.dumps({"directories_restored": len(moves), "files_verified": len(files), "consumer_files_updated": count}))


if __name__ == "__main__":
    main()
