"""Shared paths, hashing, and helpers for Phase UIR-4F."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "evaluation/uir_phase4f"
RESULTS_DIR = ROOT / "results/uir_phase4f"
DOCS_DIR = ROOT / "docs/work_reports/uir_phase4f"

# Prior phases (immutable sources)
P4D_RESULTS_DIR = ROOT / "results/uir_phase4d"
P4D_FROZEN_DIR = P4D_RESULTS_DIR / "frozen_inputs"
P4D_PER_CASE = P4D_RESULTS_DIR / "per_case_evidence_actual.jsonl"

P4E_RESULTS_DIR = ROOT / "results/uir_phase4e"

# Models
MODEL_ID = "microsoft/Phi-3.5-mini-instruct"
PHI_OLLAMA_MODEL = "phi3.5:latest"

SECOND_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
SECOND_MODEL_OLLAMA = "qwen2.5:7b"
QWEN_BLOB_DIGEST = "2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730"

SEED = 42

PIPELINES = (
    "C0_DIRECT_SLM",
    "C1_NAIVE_RAG",
    "C2_RAG_EXISTENCE_CHECK",
    "C3_JSON_SCHEMA_STRUCTURED",
    "C4_TOOL_CALLING_AGENT",
    "C5_GUARDRAIL_STYLE",
    "C6_CORRECTIVE_RETRIEVAL",
    "C7_GRAPH_STRUCTURED_RAG",
    "C8_FINAL_UIR_B6",
    "D1_EXTERNAL_CONSTRAINED_DECODING",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
