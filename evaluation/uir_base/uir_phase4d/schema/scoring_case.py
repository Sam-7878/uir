"""Scoring-only ground-truth schemas for Phase UIR-4D.

These fields are isolated strictly to post-generation evaluation modules and
must NEVER be loaded or referenced during generation or runtime pipeline steps.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AttackGoal:
    type: str  # instruction_override, unsupported_fact_coercion, policy_bypass, entity_manipulation
    target: str
    forbidden_output: str
    forbidden_transition: str


@dataclass(frozen=True)
class InternalScoringCase:
    case_id: str
    source_row_hash: str
    stratum: str
    expected_claims: list[str]
    expected_outcome: str  # COMMIT or REJECT
    is_adversarial: bool
    is_invalid_entity: bool
    is_policy_violation: bool
    numeric_eligible: bool
    attack_goal: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FinQAScoringCase:
    case_id: str
    source_row_hash: str
    gold_program: str
    gold_answer: float | str | None
    gold_evidence_spans: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HaluEvalScoringCase:
    case_id: str
    source_row_hash: str
    gold_judgement: str  # "Yes" (hallucinated) or "No" (grounded/faithful)
    ground_truth_answer: str
    hallucinated_answer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
