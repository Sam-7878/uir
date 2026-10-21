"""Relocate remaining flat project manuscripts without touching work_reports."""
import json
from organize_project_resources import ROOT, TASK, digest

def main():
    targets = {"_47.1_UIR_ZTA_kr.txt": "uir_security", "_47_1_UIR_ZTA.pdf": "uir_security",
               "_47_UIR.kr.md": "uir_base", "_47_UIR.pdf": "uir_base"}
    rows = []
    for name, project in targets.items():
        old = ROOT / "docs/papers" / name
        new = ROOT / "projects" / project / "paper" / name
        if not old.is_file() or new.exists():
            raise ValueError("FLAT_PAPER_RELOCATION_CONFLICT")
        rows.append({"old_path": str(old.relative_to(ROOT)), "new_path": str(new.relative_to(ROOT)), "sha256": digest(old)})
    for row in rows:
        (ROOT / row["old_path"]).rename(ROOT / row["new_path"])
        if digest(ROOT / row["new_path"]) != row["sha256"]:
            raise ValueError("FLAT_PAPER_HASH_MISMATCH")
    output = ROOT / "projects/uir_base/results" / TASK / "manifests/flat_paper_relocation.json"
    with output.open("x") as handle:
        json.dump({"files": rows, "all_file_hashes_preserved": True}, handle, indent=2)
    for folder in ("docs/papers", "projects/uir_base/reports", "projects/uir_security/reports", "projects/uir_law/reports"):
        path = ROOT / folder
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    print(json.dumps({"flat_paper_files_moved": len(rows)}))

if __name__ == "__main__":
    main()
