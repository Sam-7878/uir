"""Oracle case schema: Ground truth and evaluation parameters.

These fields are reserved EXCLUSIVELY for the evaluation harness and behavioral
judges after the SUT completes execution. They must NEVER be passed to any SUT
pipeline component.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class OracleCase:
    case_id: str
    attack_class: str
    attack_goal: Dict[str, Any]
    expected_answer: Optional[Dict[str, Any]] = None
    forbidden_actions: List[str] = field(default_factory=list)
    forbidden_output_patterns: List[str] = field(default_factory=list)
    canaries: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "attack_class": self.attack_class,
            "attack_goal": self.attack_goal,
            "expected_answer": self.expected_answer,
            "forbidden_actions": self.forbidden_actions,
            "forbidden_output_patterns": self.forbidden_output_patterns,
            "canaries": self.canaries,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OracleCase:
        return cls(
            case_id=str(data["case_id"]),
            attack_class=str(data.get("attack_class", "unknown")),
            attack_goal=dict(data.get("attack_goal", {})),
            expected_answer=data.get("expected_answer"),
            forbidden_actions=list(data.get("forbidden_actions", [])),
            forbidden_output_patterns=list(data.get("forbidden_output_patterns", [])),
            canaries=list(data.get("canaries", [])),
            metadata=dict(data.get("metadata", {})),
        )
