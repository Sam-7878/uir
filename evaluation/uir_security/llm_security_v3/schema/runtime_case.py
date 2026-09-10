"""Runtime case schema: Strictly SUT-visible fields.

Under no circumstances may this class or any object passed into the System
Under Test contain attack_class, attack_goal, expected_policy_outcome, or
any evaluation-oracle metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RuntimeCase:
    case_id: str
    language: str
    user_input: str
    retrieved_context: List[Dict[str, Any]] = field(default_factory=list)
    principal_id: str = "finance_analyst_authenticated"
    environment_id: str = "enterprise_fin_prod"
    session_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "language": self.language,
            "user_input": self.user_input,
            "retrieved_context": self.retrieved_context,
            "principal_id": self.principal_id,
            "environment_id": self.environment_id,
            "session_metadata": self.session_metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RuntimeCase:
        # Guarantee that no oracle fields leak into RuntimeCase even if present in raw json
        return cls(
            case_id=str(data["case_id"]),
            language=str(data.get("language", "en")),
            user_input=str(data.get("user_input") or data.get("prompt", "")),
            retrieved_context=list(data.get("retrieved_context") or data.get("context", [])),
            principal_id=str(data.get("principal_id", "finance_analyst_authenticated")),
            environment_id=str(data.get("environment_id", "enterprise_fin_prod")),
            session_metadata=dict(data.get("session_metadata", {})),
        )
