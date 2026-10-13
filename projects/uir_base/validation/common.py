"""Read-only historical inputs and fail-closed versioned R-stage outputs."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "Cargo.toml").is_file())
OUT = ROOT / "projects/uir_base/results/uir_repr_validation_2026_10_12_v1"
DOC = ROOT / "docs/work_reports/uir_base/111_validation/implementation"
OLD = ROOT / "projects/uir_base/results/mdpi_next_2026_10_11_v2"
FROZEN = ROOT / "projects/uir_base/results/uir_phase4d/frozen_inputs"
ARCHIVE = ROOT / "docs/work_reports/uir_base/110_mdpi_rev/uir_next_source_evidence_v3.zip"
V3_SHA = "aea0551d1b7e14cc98f5e8cfd32694cb9c1fcac25a700dee284c6d3c6814da76"
FIELDS = ("claim_type", "entity_id", "attribute", "value", "unit", "period", "provenance")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def jsonl(path, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows))


def csvfile(path, rows, fields=None):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def utc():
    return datetime.now(timezone.utc).isoformat()


def check_frozen():
    if sha(ARCHIVE) != V3_SHA:
        raise ValueError("FROZEN_V3_HASH_MISMATCH")
    manifest = load(OLD / "final_release_index.json")
    for rel, expected in manifest["files"].items():
        path = ROOT / rel
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"MISSING_OR_UNSAFE_FROZEN_INPUT: {rel}")
        if sha(path) != expected:
            raise ValueError(f"FROZEN_INPUT_HASH_MISMATCH: {rel}")
    return {"archive_sha256": V3_SHA, "N_final_index_checked": len(manifest["files"]), "status": "PASS"}
