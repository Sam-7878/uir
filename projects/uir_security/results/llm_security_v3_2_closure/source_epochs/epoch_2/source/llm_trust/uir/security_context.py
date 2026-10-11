"""Security Context definition and enforcement for UIR v2."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class TrustLevel(str, Enum):
    UNTRUSTED = "UNTRUSTED"
    AUTHENTICATED = "AUTHENTICATED"
    PRIVILEGED = "PRIVILEGED"
    SYSTEM = "SYSTEM"


class InputTaint(str, Enum):
    USER = "USER"
    RAG = "RAG"
    TOOL = "TOOL"
    MEMORY = "MEMORY"
    SYSTEM = "SYSTEM"


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"


# Built-in capability sets by role/context
ROLE_CAPABILITY_MAP: Dict[TrustLevel, Set[str]] = {
    TrustLevel.UNTRUSTED: {
        "read:public",
        "query:standard",
        "summarize",
        "explain",
    },
    TrustLevel.AUTHENTICATED: {
        "read:public",
        "read:internal",
        "query:standard",
        "summarize",
        "explain",
        "verify:facts",
        "cause_trace",
        "export:report",
    },
    TrustLevel.PRIVILEGED: {
        "read:public",
        "read:internal",
        "read:confidential",
        "query:standard",
        "query:deep",
        "summarize",
        "explain",
        "verify:facts",
        "cause_trace",
        "export:report",
        "audit:logs",
        "execute:safe_tool",
    },
    TrustLevel.SYSTEM: {
        "read:public",
        "read:internal",
        "read:confidential",
        "read:secret",
        "query:standard",
        "query:deep",
        "summarize",
        "explain",
        "verify:facts",
        "cause_trace",
        "export:report",
        "audit:logs",
        "execute:safe_tool",
        "execute:privileged_tool",
        "mutate:state",
    },
}

# High-impact operations requiring explicit human approval
HIGH_IMPACT_CAPABILITIES: Set[str] = {
    "execute:privileged_tool",
    "mutate:state",
    "wire_transfer",
    "delete:records",
    "export:confidential",
    "modify:policy",
}


@dataclass(frozen=True)
class SecurityContext:
    principal: str
    trust_level: TrustLevel
    input_taint: List[InputTaint]
    data_classification: List[DataClassification]
    allowed_capabilities: List[str]
    denied_capabilities: List[str]
    requires_human_approval: bool
    approval_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "principal": self.principal,
            "trust_level": self.trust_level.value,
            "input_taint": [t.value for t in self.input_taint],
            "data_classification": [c.value for c in self.data_classification],
            "allowed_capabilities": list(self.allowed_capabilities),
            "denied_capabilities": list(self.denied_capabilities),
            "requires_human_approval": self.requires_human_approval,
            "approval_token": self.approval_token,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SecurityContext:
        return cls(
            principal=data["principal"],
            trust_level=TrustLevel(data["trust_level"]),
            input_taint=[InputTaint(t) for t in data.get("input_taint", ["USER"])],
            data_classification=[DataClassification(c) for c in data.get("data_classification", ["PUBLIC"])],
            allowed_capabilities=list(data.get("allowed_capabilities", [])),
            denied_capabilities=list(data.get("denied_capabilities", [])),
            requires_human_approval=bool(data.get("requires_human_approval", False)),
            approval_token=data.get("approval_token"),
        )

    def is_capability_allowed(self, capability: str) -> bool:
        if capability in self.denied_capabilities:
            return False
        return capability in self.allowed_capabilities

    def is_high_impact(self, capability: str) -> bool:
        return capability in HIGH_IMPACT_CAPABILITIES


def create_trusted_security_context(
    principal: str,
    trust_level: TrustLevel = TrustLevel.UNTRUSTED,
    taint_sources: Optional[List[InputTaint]] = None,
    data_classification: Optional[List[DataClassification]] = None,
    explicit_denials: Optional[List[str]] = None,
    approval_token: Optional[str] = None,
) -> SecurityContext:
    """Factory creating an immutable SecurityContext from trusted application state.

    CRITICAL INVARIANT: User-provided text strings MUST NOT directly determine
    or expand allowed_capabilities. All capability assignments are policy-bound.
    """
    if taint_sources is None:
        taint_sources = [InputTaint.USER]
    if data_classification is None:
        data_classification = [DataClassification.PUBLIC]
    if explicit_denials is None:
        explicit_denials = []

    # Derive baseline capabilities strictly from TrustLevel
    base_caps = ROLE_CAPABILITY_MAP.get(trust_level, ROLE_CAPABILITY_MAP[TrustLevel.UNTRUSTED])
    allowed = sorted([cap for cap in base_caps if cap not in explicit_denials])

    # Determine if human approval is required
    requires_approval = any(cap in HIGH_IMPACT_CAPABILITIES for cap in allowed) or (approval_token is not None)

    return SecurityContext(
        principal=principal,
        trust_level=trust_level,
        input_taint=list(taint_sources),
        data_classification=list(data_classification),
        allowed_capabilities=allowed,
        denied_capabilities=sorted(list(set(explicit_denials))),
        requires_human_approval=requires_approval,
        approval_token=approval_token,
    )
