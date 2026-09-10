"""Runtime Case Schema for HETE V3.2.

Work Order Mandates:
- Opaque case IDs: zero attack/benign tokens in runtime-visible IDs.
- Strict field allow-list: only explicitly approved runtime fields are accepted.
- Any attempt to pass oracle fields or unapproved fields raises a ValueError.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

ALLOWED_RUNTIME_FIELDS: Set[str] = {
    "case_id",
    "language",
    "user_input",
    "retrieved_context",
    "principal_id",
    "environment_id",
    "session_metadata",
}

LEAKY_PATTERNS = re.compile(r"(atk|attack|benign|malicious|jailbreak|poison|exfil)", re.IGNORECASE)


@dataclass(frozen=True)
class RuntimeCase:
    case_id: str
    language: str
    user_input: str
    retrieved_context: List[Dict[str, Any]] = field(default_factory=list)
    principal_id: str = "finance_analyst_authenticated"
    environment_id: str = "enterprise_fin_prod"
    session_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # 1. Enforce opaque case_id (no semantic hints in ID)
        if LEAKY_PATTERNS.search(self.case_id):
            raise ValueError(
                f"Runtime case_id '{self.case_id}' violates opacity mandate: contains leaky token."
            )

        # 2. Enforce valid principal
        if not self.principal_id:
            raise ValueError("RuntimeCase requires a valid principal_id.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RuntimeCase:
        # Strict allow-list verification
        incoming_keys = set(data.keys())
        disallowed = incoming_keys - ALLOWED_RUNTIME_FIELDS
        if disallowed:
            raise ValueError(
                f"RuntimeCase rejected unauthorized fields: {sorted(list(disallowed))}. "
                f"Allowed fields: {sorted(list(ALLOWED_RUNTIME_FIELDS))}"
            )

        return cls(
            case_id=data["case_id"],
            language=data.get("language", "en"),
            user_input=data["user_input"],
            retrieved_context=data.get("retrieved_context", []),
            principal_id=data.get("principal_id", "finance_analyst_authenticated"),
            environment_id=data.get("environment_id", "enterprise_fin_prod"),
            session_metadata=data.get("session_metadata", {}),
        )

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
