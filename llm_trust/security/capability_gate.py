"""Capability Gate: Least-Privilege Action Binding and Approval Enforcement."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ..uir.security_context import HIGH_IMPACT_CAPABILITIES, SecurityContext


class CapabilityGateVerdict(str, Enum):
    PERMITTED = "PERMITTED"
    DENIED = "DENIED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    DEGRADED_TO_READ_ONLY = "DEGRADED_TO_READ_ONLY"


# Action-to-Capability mapping
ACTION_CAPABILITY_REQUIREMENTS: Dict[str, List[str]] = {
    "SUMMARIZE": ["summarize"],
    "EXTRACT": ["read:public"],
    "LOOKUP": ["query:standard"],
    "ANALYZE": ["query:standard", "explain"],
    "COMPARE": ["query:standard"],
    "VERIFY": ["verify:facts"],
    "CAUSE_TRACE": ["cause_trace"],
    "AUDIT": ["audit:logs"],
    "EXECUTE_TOOL": ["execute:safe_tool"],
    "TRANSFER": ["wire_transfer", "mutate:state"],
}


@dataclass(frozen=True)
class GateDecision:
    verdict: CapabilityGateVerdict
    action: str
    required_capabilities: List[str]
    missing_capabilities: List[str]
    is_high_impact: bool
    rejection_reason: str = ""


class CapabilityGate:
    """Enforces least privilege and human-in-the-loop approval on executable UIR actions."""

    def evaluate(
        self,
        action: str,
        security_context: SecurityContext,
        approval_token: Optional[str] = None,
        enforce_read_only_fallback: bool = False,
    ) -> GateDecision:
        """Evaluates whether the given action is authorized under security_context."""
        req_caps = ACTION_CAPABILITY_REQUIREMENTS.get(action.upper(), ["query:standard"])
        missing: List[str] = []
        is_high_impact = any(cap in HIGH_IMPACT_CAPABILITIES for cap in req_caps)

        for cap in req_caps:
            if not security_context.is_capability_allowed(cap):
                missing.append(cap)

        # Check explicit denials
        for cap in req_caps:
            if cap in security_context.denied_capabilities:
                if cap not in missing:
                    missing.append(cap)

        if missing:
            # Only non-high-impact/informational queries can degrade to read-only
            if (
                enforce_read_only_fallback
                and not is_high_impact
                and action not in {"TRANSFER", "EXECUTE_TOOL"}
                and "read:public" in security_context.allowed_capabilities
            ):
                return GateDecision(
                    verdict=CapabilityGateVerdict.DEGRADED_TO_READ_ONLY,
                    action="LOOKUP",
                    required_capabilities=req_caps,
                    missing_capabilities=missing,
                    is_high_impact=is_high_impact,
                    rejection_reason=f"Action '{action}' requires missing capabilities {missing}. Degraded to read-only.",
                )
            return GateDecision(
                verdict=CapabilityGateVerdict.DENIED,
                action=action,
                required_capabilities=req_caps,
                missing_capabilities=missing,
                is_high_impact=is_high_impact,
                rejection_reason=f"Unauthorized action '{action}': Principal '{security_context.principal}' lacks {missing}.",
            )

        # High-impact approval check
        if is_high_impact or security_context.requires_human_approval:
            # Valid approval token must be present
            valid_token = approval_token or security_context.approval_token
            if not valid_token or not valid_token.startswith("APPROVED_BY_"):
                return GateDecision(
                    verdict=CapabilityGateVerdict.REQUIRES_APPROVAL,
                    action=action,
                    required_capabilities=req_caps,
                    missing_capabilities=[],
                    is_high_impact=True,
                    rejection_reason=f"Action '{action}' is a high-impact operation requiring explicit verified human approval.",
                )

        return GateDecision(
            verdict=CapabilityGateVerdict.PERMITTED,
            action=action,
            required_capabilities=req_caps,
            missing_capabilities=[],
            is_high_impact=is_high_impact,
        )
