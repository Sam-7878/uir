"""Oracle Case Schema for HETE V3.1.

Work Order Mandate:
Maintains privileged evaluation ground truth securely decoupled from RuntimeCase.
Maps the opaque case_id to true intent, expected policy outcome, and target behavioral metrics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class OracleCase:
    case_id: str
    attack_class: str
    is_attack: bool = True
    original_case_id: str = ""
    attack_goal: Dict[str, Any] = field(default_factory=dict)
    forbidden_actions: List[str] = field(default_factory=list)
    forbidden_output_patterns: List[str] = field(default_factory=list)
    target_entities: List[str] = field(default_factory=list)
    expected_numeric_values: List[str] = field(default_factory=list)
    admissible_evidence_ids: List[str] = field(default_factory=list)
    expected_policy_outcome: str = "DENY"
    split: str = "heldout"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.original_case_id:
            object.__setattr__(self, "original_case_id", self.case_id)
        if self.attack_class == "valid_benign":
            object.__setattr__(self, "is_attack", False)
            if self.expected_policy_outcome == "DENY":
                object.__setattr__(self, "expected_policy_outcome", "ALLOW")
        if self.forbidden_actions:
            combined = list(self.forbidden_output_patterns)
            for fa in self.forbidden_actions:
                if fa not in combined:
                    combined.append(fa)
            object.__setattr__(self, "forbidden_output_patterns", combined)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OracleCase:
        attack_class = data.get("attack_class", "valid_benign")
        is_attack = data.get("is_attack", (attack_class != "valid_benign"))

        return cls(
            case_id=data["case_id"],
            original_case_id=data.get("original_case_id", data["case_id"]),
            attack_class=attack_class,
            is_attack=is_attack,
            attack_goal=data.get("attack_goal", {}),
            forbidden_actions=data.get("forbidden_actions", []),
            forbidden_output_patterns=data.get("forbidden_output_patterns", []),
            target_entities=data.get("target_entities", []),
            expected_numeric_values=data.get("expected_numeric_values", []),
            admissible_evidence_ids=data.get("admissible_evidence_ids", []),
            expected_policy_outcome=data.get(
                "expected_policy_outcome", "ALLOW" if not is_attack else "DENY"
            ),
            split=data.get("split", "heldout"),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "original_case_id": self.original_case_id,
            "attack_class": self.attack_class,
            "is_attack": self.is_attack,
            "attack_goal": self.attack_goal,
            "forbidden_actions": self.forbidden_actions,
            "forbidden_output_patterns": self.forbidden_output_patterns,
            "target_entities": self.target_entities,
            "expected_numeric_values": self.expected_numeric_values,
            "admissible_evidence_ids": self.admissible_evidence_ids,
            "expected_policy_outcome": self.expected_policy_outcome,
            "split": self.split,
            "metadata": self.metadata,
        }
