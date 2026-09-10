"""Shared paths, hashing, and helpers for Phase UIR-4E."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "evaluation/uir_phase4e"
RESULTS_DIR = ROOT / "results/uir_phase4e"
DOCS_DIR = ROOT / "docs/work_reports/uir_phase4e"

# Phase 4D immutable source (read-only)
P4D_RESULTS_DIR = ROOT / "results/uir_phase4d"
P4D_FROZEN_DIR = P4D_RESULTS_DIR / "frozen_inputs"
P4D_PER_CASE = P4D_RESULTS_DIR / "per_case_evidence_actual.jsonl"

MODEL_ID = "microsoft/Phi-3.5-mini-instruct"
SECOND_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
SECOND_MODEL_OLLAMA = "qwen2.5:7b"
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
)

# C3 publication-safe label (BLOCKER 8 fix)
C3_PUBLICATION_LABEL = "JSON-Schema Prompted / Post-Hoc Validation Baseline"


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


def row_hash(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
