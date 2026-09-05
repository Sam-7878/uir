"""Shared paths, hashing, constants, and JSONL helpers for Phase UIR-4D."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "evaluation/uir_phase4d"
RESULTS_DIR = ROOT / "results/uir_phase4d"
P4C_RESULTS_DIR = ROOT / "results/uir_phase4c"
DOCS_DIR = ROOT / "docs/uir_phase4d"
FROZEN_DIR = RESULTS_DIR / "frozen_inputs"
SOURCE_DIR = ROOT / "evaluation/uir_phase4c/official_sources"
RAW_DIR = RESULTS_DIR / "raw_captures"
MANIFEST_4C = RESULTS_DIR / "PHASE4C_PARENT_MANIFEST.json"
MANIFEST_4D = RESULTS_DIR / "PHASE4D_RUN_MANIFEST.json"
PHASE4C_DIR = ROOT / "evaluation/uir_phase4c"

MODEL_ID = "microsoft/Phi-3.5-mini-instruct"
MODEL_REVISION = "2fe192450127e6a83f7441aef6e3ca586c338b77"
SECOND_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
SEED = 42
MAX_NEW_TOKENS = 128

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
EXTERNAL_PIPELINES = (
    "C1_NAIVE_RAG",
    "C2_RAG_EXISTENCE_CHECK",
    "C4_TOOL_CALLING_AGENT",
    "C8_FINAL_UIR_B6",
)
SECOND_MODEL_INTERNAL_PIPELINES = (
    "C1_NAIVE_RAG",
    "C5_GUARDRAIL_STYLE",
    "C6_CORRECTIVE_RETRIEVAL",
    "C8_FINAL_UIR_B6",
)
SECOND_MODEL_EXTERNAL_PIPELINES = (
    "C1_NAIVE_RAG",
    "C8_FINAL_UIR_B6",
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


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


def extract_json(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    candidates = [stripped]
    start, end = stripped.find("{"), stripped.rfind("}")
    if 0 <= start < end:
        candidates.append(stripped[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
            if isinstance(value, dict):
                return value
        except (ValueError, TypeError):
            continue
    return None

