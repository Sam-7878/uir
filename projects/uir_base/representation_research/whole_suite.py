"""Private, exact-source closure for the additional165 repository tests."""
from pathlib import Path
import shutil
from .common import ROOT, sha, relative, write

EXTRA_DIRS = ["tests", "projects/uir_security/evaluation", "projects/uir_law/evaluation"]


def files():
    selected = []
    for directory in EXTRA_DIRS:
        for path in (ROOT / directory).rglob("*"):
            if "__pycache__" in path.parts or not path.is_file():
                continue
            if path.suffix in {".py", ".json", ".yaml", ".yml", ".toml", ".csv"}:
                if path.is_symlink():
                    raise ValueError("NO_SOURCE_LINKS")
                selected.append(path)
    for rel in ["scripts/migrate_project_layout.py",
                "projects/uir_security/evaluation/llm_security_v3_1/datasets/custom_heldout_v3_1.jsonl",
                "projects/uir_security/evaluation/llm_security_v3_1/datasets/oracle_heldout_v3_1.jsonl"]:
        path = ROOT / rel
        if not path.is_file():
            raise FileNotFoundError(rel)
        selected.append(path)
    return sorted(set(selected))


def overlay(checkout, receipt):
    selected = files()
    for path in selected:
        target = checkout / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    write(receipt, {"files": [{"path": relative(p), "sha256": sha(p), "bytes": p.stat().st_size} for p in selected],
                   "scope": "exact current test+module+synthetic historical schema fixtures; private only, not newly scored benchmarks",
                   "source_generated_or_weakened": False})
