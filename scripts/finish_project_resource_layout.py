"""Complete LAW-200 embedded-resource separation and obvious legacy root paths."""
import json
import re
from uir_common.paths import repo_root
from organize_project_resources import digest

ROOT = repo_root()
OUT = ROOT / "projects/uir_base/results/114_project_layout_2026_10_21/manifests"
LAW = ROOT / "projects/uir_law/evaluation/law200"


def main():
    task = ROOT / "projects/uir_law/results/law200"
    moves = [(LAW / "results", task / "execution"), (LAW / "data", task / "data")]
    for name in ("LAW200_KR_AUDIT_REPORT.md", "LAW200_KR_REPORT.md", "KAIC_MANUSCRIPT_UPDATE_KR.md", "CLAIM_EVIDENCE_MAP.yaml"):
        source = LAW / name
        if source.exists():
            moves.append((source, task / "reports" / name))
    for name in ("LAW200_PROTOCOL.md", "DATASET_CARD.md"):
        moves.append((LAW / name, ROOT / "projects/uir_law/docs/law200" / name))
    rows = []
    for source, target in moves:
        if not source.exists() or target.exists():
            raise ValueError(f"Missing source or occupied destination: {source}")
        for path in sorted(source.rglob("*")) if source.is_dir() else [source]:
            if path.is_symlink():
                raise ValueError("Symlink resource")
            if path.is_file():
                new = target / path.relative_to(source) if source.is_dir() else target
                rows.append({"old_path": str(path.relative_to(ROOT)), "new_path": str(new.relative_to(ROOT)), "sha256": digest(path)})
    for source, target in moves:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
    for row in rows:
        if digest(ROOT / row["new_path"]) != row["sha256"]:
            raise ValueError("LAW_RESOURCE_HASH_MISMATCH")
    with (OUT / "law_resource_relocation.json").open("x") as handle:
        json.dump({"files": rows, "all_file_hashes_preserved": True}, handle, indent=2)
    changed = []
    for project in ("uir_base", "uir_security", "uir_law"):
        for path in (ROOT / "projects" / project).rglob("*.py"):
            if any(p in {"results", "data", "paper", "vendor"} for p in path.relative_to(ROOT).parts):
                continue
            original = path.read_text()
            text = re.sub(r'(?P<quote>["\x27])(results|evaluation)/',
                          lambda m: m["quote"] + "projects/" + project + "/" + m[0][1:], original)
            if project == "uir_law":
                # PACKAGE_ROOT remains the real source root. Resources have a separate root.
                text = text.replace('PACKAGE_ROOT / "data"', 'TASK_ROOT / "data"')
                text = text.replace('PACKAGE_ROOT / "results"', 'TASK_ROOT / "execution"')
                text = text.replace('PACKAGE_ROOT / "benchmark_manifest.json"', 'TASK_ROOT / "benchmark_manifest.json"')
                text = re.sub(r'PACKAGE_ROOT / "((?:LAW200|KAIC_)[^"]+\.md)"', r'TASK_ROOT / "reports/\1"', text)
                text = text.replace('raw_path = PACKAGE_ROOT / relative', 'raw_path = TASK_ROOT / relative')
                if "TASK_ROOT" in text and path.name != "common.py":
                    # Insert after __future__ imports rather than ahead of them.
                    marker = "from __future__ import annotations\n"
                    text = text.replace(marker, marker + "from projects.uir_law.evaluation.law200.common import TASK_ROOT\n", 1)
            if text != original:
                path.write_text(text)
                changed.append(str(path.relative_to(ROOT)))
    with (OUT / "additional_consumer_changes.json").open("x") as handle:
        json.dump(changed, handle, indent=2)
    print(json.dumps({"law_files_moved": len(rows), "additional_consumers_updated": len(changed)}))


if __name__ == "__main__":
    main()
