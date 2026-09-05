"""Strict runtime input schemas for Phase UIR-4D.

Guaranteed zero leakage: prohibited fields such as stratum, gold labels,
expected outcomes, and pre-evaluated runtime flags are strictly excluded.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

FORBIDDEN_RUNTIME_KEYS = frozenset({
    "stratum",
    "category",
    "split",
    "runtime_entity_exists",
    "runtime_policy_permit",
    "runtime_uir_compiles",
    "expected_outcome",
    "expected_policy_decision",
    "expected_claims",
    "required_claims",
    "entity_valid",
    "policy_valid",
    "uir_ready",
    "is_adversarial",
    "is_policy_violation",
    "is_invalid_entity",
    "attack_goal",
    "gold",
    "gold_program",
    "exe_ans",
    "qa.program",
    "right_answer",
    "hallucinated_answer",
    "gold_judgement",
})


def validate_clean_runtime_dict(data: dict[str, Any], context: str = "") -> None:
    leaked = sorted(FORBIDDEN_RUNTIME_KEYS.intersection(data.keys()))
    if leaked:
        raise ValueError(f"CRITICAL LEAKAGE: Forbidden key(s) {leaked} in runtime case {context}: {data.get('case_id')}")


@dataclass(frozen=True)
class InternalRuntimeCase:
    case_id: str
    language: str
    input: str
    requested_entity: str
    requested_attribute: str
    requested_period: str
    context_claims: list[dict[str, Any]]
    source_dataset: str
    source_row_hash: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        validate_clean_runtime_dict(d, "InternalRuntimeCase")
        return d


@dataclass(frozen=True)
class FinQARuntimeCase:
    case_id: str
    question: str
    pre_text: list[str]
    post_text: list[str]
    table: list[list[str]]
    filename: str
    source_dataset: str
    source_row_hash: str
    source_original_id: str
    source_file_sha256: str
    source_index: int

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        validate_clean_runtime_dict(d, "FinQARuntimeCase")
        return d


@dataclass(frozen=True)
class HaluEvalRuntimeCase:
    case_id: str
    question: str
    knowledge: str
    candidate_answer: str
    source_dataset: str
    source_row_hash: str
    source_original_id: str
    source_file_sha256: str
    source_index: int

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        validate_clean_runtime_dict(d, "HaluEvalRuntimeCase")
        return d
