"""One-time mechanical update of live consumers, never frozen data/manifests."""
import hashlib
import json
from pathlib import Path
from uir_common.paths import repo_root

ROOT = repo_root()
OUT = ROOT / "projects/uir_base/results/114_project_layout_2026_10_21/manifests"


def main():
    if (OUT / "live_consumer_changes.json").exists():
        raise FileExistsError("One-time migration already executed; owner exception supersedes its old mapping")
    relocation = json.loads((OUT / "relocation_manifest.json").read_text())
    replacements = [(row["old"], row["new"]) for row in relocation["directories"]]
    replacements += [("archive/uir_base/results", "projects/uir_base/results")]
    # Legacy flat report locations are assigned to their owning task, not recreated.
    for task in ("uir_phase3b", "uir_phase4b", "uir_phase4c", "uir_phase4e", "uir_phase4f"):
        replacements.append(("docs/work_reports/" + task, "projects/uir_base/results/" + task + "/reports"))
    replacements += [("docs/work_reports/uir_base/104_uir_pahse_4d", "projects/uir_base/results/104_uir_pahse_4d/reports"),
                     ("docs/work_reports/106_uir_pahse_4f", "projects/uir_base/results/106_uir_pahse_4f/reports"),
                     ("docs/work_reports/300_uir", "projects/uir_base/results/uir/reports"),
                     ("docs/work_reports/301_uir_phase_2", "projects/uir_base/results/uir_slm/reports"),
                     ("docs/work_reports/uir_phase3", "projects/uir_base/results/uir_phase3/reports"),
                     ("docs/work_reports/307_uir_3d_evidence", "projects/uir_base/results/uir_phase3d/reports"),
                     ("docs/work_reports/311_uir_phase_3D_role_separated_validation", "projects/uir_base/results/uir_phase3d/reports")]
    replacements.sort(key=lambda row: len(row[0]), reverse=True)
    candidates = [ROOT / "README.md"]
    for folder in ("projects", "tests", "scripts"):
        for path in (ROOT / folder).rglob("*"):
            if path.suffix not in {".py", ".sh", ".yaml"} or any(part in {"results", "paper", "data", "vendor", "__pycache__"} for part in path.relative_to(ROOT).parts):
                continue
            if path.name in {"organize_project_resources.py", "update_project_path_consumers.py"}:
                continue
            candidates.append(path)
    changes = []
    for path in candidates:
        before = path.read_bytes()
        after = before.decode("utf-8")
        for old, new in replacements:
            after = after.replace(old, new)
        encoded = after.encode("utf-8")
        if encoded != before:
            path.write_bytes(encoded)
            changes.append({"path": str(path.relative_to(ROOT)), "before_sha256": hashlib.sha256(before).hexdigest(),
                            "after_sha256": hashlib.sha256(encoded).hexdigest()})
    with (OUT / "live_consumer_changes.json").open("x") as handle:
        json.dump(changes, handle, indent=2)
    print(json.dumps({"live_files_updated": len(changes), "frozen_contents_edited": False}))


if __name__ == "__main__":
    main()
