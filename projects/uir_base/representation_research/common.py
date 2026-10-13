"""Portable, fail-closed S-stage artifact helpers."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "Cargo.toml").is_file())
DOC = ROOT / "docs/work_reports/uir_base/112_representation_research"
RESULTS = ROOT / "projects/uir_base/results/uir_repr_semantics_2026_10_13_v1"
PRIOR = ROOT / "docs/work_reports/uir_base/111_validation"
RELEASE_SHA = "c9adb265258cf0b44367bfe76cc11ad116467d24498fe6947dcdb0dc6f0bc9ab"
DELIVERY_SHA = "839e1230cd02af2ba25ee84b6d5caa54bbc9f8882ef4921e1897d6468f8a0267"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def textfile(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(value)


def jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def csvfile(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def relative(path):
    return str(Path(path).relative_to(ROOT))
