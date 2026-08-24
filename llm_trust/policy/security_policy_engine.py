"""Zero-Trust Policy Enforcement Point (PEP) for UIR v2."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ..evidence.provenance import EvidenceRecord, EvidenceTrust
from ..evidence.trusted_resolver import ResolutionResult, ResolutionStatus
from ..security.capability_gate import CapabilityGate, CapabilityGateVerdict, GateDecision
from ..security.context_firewall import ContextFirewall, FirewallVerdict
from ..security.input_guard import GuardedInput
from ..security.resource_guard import ResourceBudget, ResourceTracker
from ..uir.security_context import DataClassification, InputTaint, SecurityContext, TrustLevel


class PolicyOutcome(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    CLARIFY = "CLARIFY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    QUARANTINE_EVIDENCE = "QUARANTINE_EVIDENCE"
    DEGRADE_TO_READ_ONLY = "DEGRADE_TO_READ_ONLY"


@dataclass(frozen=True)
class PolicyEvaluationResult:
    outcome: PolicyOutcome
    matched_rule: str
    decision_details: str
    is_authoritative: bool
    quarantined_evidence: List[EvidenceRecord] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)


class SecurityPolicyEngine:
    """Deterministic Zero-Trust Policy Decision Point (PDP) and Enforcement Point (PEP)."""

    def __init__(
        self,
        capability_gate: Optional[CapabilityGate] = None,
        context_firewall: Optional[ContextFirewall] = None,
    ):
        self.capability_gate = capability_gate or CapabilityGate()
        self.context_firewall = context_firewall or ContextFirewall()

    def evaluate_request(
        self,
        guarded_input: GuardedInput,
        security_context: SecurityContext,
        action: str,
        target_entities: List[str],
        resolution_result: Optional[ResolutionResult] = None,
        resource_tracker: Optional[ResourceTracker] = None,
        approval_token: Optional[str] = None,
    ) -> PolicyEvaluationResult:
        """Evaluates all deterministic security invariants outside the LLM."""

        # 1. Resource Budget Check (Rule: POL-RES-001)
        if resource_tracker:
            tok_ok, tok_msg = resource_tracker.check_and_consume_tokens(guarded_input.estimated_tokens)
            if not tok_ok:
                return PolicyEvaluationResult(
                    outcome=PolicyOutcome.DENY,
                    matched_rule="POL-RES-001:TOKEN_BUDGET_EXCEEDED",
                    decision_details=tok_msg,
                    is_authoritative=False,
                )
            time_ok, time_msg = resource_tracker.check_timeout()
            if not time_ok:
                return PolicyEvaluationResult(
                    outcome=PolicyOutcome.DENY,
                    matched_rule="POL-RES-002:TIMEOUT_EXCEEDED",
                    decision_details=time_msg,
                    is_authoritative=False,
                )

        # 2. Privilege Escalation Defense (Rule: POL-PRIV-001)
        # Verify that security_context has not been tainted by user natural-language text
        if "PRIVILEGE_INJECTION_MARKER" in guarded_input.suspicious_telemetry_flags:
            if security_context.trust_level == TrustLevel.UNTRUSTED and "execute:privileged_tool" in security_context.allowed_capabilities:
                # Invariant violated if unauthenticated user somehow obtained privileged caps
                return PolicyEvaluationResult(
                    outcome=PolicyOutcome.DENY,
                    matched_rule="POL-PRIV-001:UNAUTHORIZED_PRIVILEGE_ELEVATION",
                    decision_details="User input attempted unauthorized role/privilege escalation.",
                    is_authoritative=False,
                )

        # 3. Capability and Action Authorization Gate (Rule: POL-CAP-001)
        gate_decision: GateDecision = self.capability_gate.evaluate(
            action=action,
            security_context=security_context,
            approval_token=approval_token,
            enforce_read_only_fallback=True,
        )

        if gate_decision.verdict == CapabilityGateVerdict.DENIED:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.DENY,
                matched_rule="POL-CAP-001:CAPABILITY_DENIED",
                decision_details=gate_decision.rejection_reason,
                is_authoritative=False,
                required_capabilities=gate_decision.required_capabilities,
            )

        if gate_decision.verdict == CapabilityGateVerdict.REQUIRES_APPROVAL:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.REQUIRE_APPROVAL,
                matched_rule="POL-CAP-002:HUMAN_APPROVAL_REQUIRED",
                decision_details=gate_decision.rejection_reason,
                is_authoritative=False,
                required_capabilities=gate_decision.required_capabilities,
            )

        # 4. Entity Verification & Hallucination Prevention (Rule: POL-ENT-001)
        if resolution_result:
            if resolution_result.status == ResolutionStatus.NO_VERIFIED_EVIDENCE:
                return PolicyEvaluationResult(
                    outcome=PolicyOutcome.DENY,
                    matched_rule="POL-ENT-001:FICTITIOUS_OR_UNVERIFIED_ENTITY",
                    decision_details=resolution_result.rejection_reason or "Entity not verified in authoritative registry.",
                    is_authoritative=False,
                )

            if resolution_result.status == ResolutionStatus.QUARANTINED:
                return PolicyEvaluationResult(
                    outcome=PolicyOutcome.QUARANTINE_EVIDENCE,
                    matched_rule="POL-EVD-001:UNTRUSTED_OR_POISONED_EVIDENCE",
                    decision_details=resolution_result.rejection_reason or "Evidence quarantined due to provenance failure.",
                    is_authoritative=False,
                    quarantined_evidence=resolution_result.evidence,
                )

            if resolution_result.status == ResolutionStatus.INTEGRITY_FAILURE:
                return PolicyEvaluationResult(
                    outcome=PolicyOutcome.DENY,
                    matched_rule="POL-EVD-002:INTEGRITY_HASH_MISMATCH",
                    decision_details=resolution_result.rejection_reason or "Evidence SHA-256 hash mismatch.",
                    is_authoritative=False,
                )

        # 5. Data Flow & Confidentiality Invariant (Rule: POL-DATA-001)
        if DataClassification.SECRET in security_context.data_classification:
            if security_context.trust_level not in {TrustLevel.PRIVILEGED, TrustLevel.SYSTEM}:
                return PolicyEvaluationResult(
                    outcome=PolicyOutcome.DENY,
                    matched_rule="POL-DATA-001:CONFIDENTIAL_DATA_FLOW_VIOLATION",
                    decision_details="Access to SECRET data classification denied for current principal trust level.",
                    is_authoritative=False,
                )

        # 6. Read-Only Fallback Handling
        if gate_decision.verdict == CapabilityGateVerdict.DEGRADED_TO_READ_ONLY:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.DEGRADE_TO_READ_ONLY,
                matched_rule="POL-CAP-003:DEGRADED_TO_READ_ONLY",
                decision_details=gate_decision.rejection_reason,
                is_authoritative=True,
                required_capabilities=gate_decision.required_capabilities,
            )

        # All invariants satisfied
        return PolicyEvaluationResult(
            outcome=PolicyOutcome.ALLOW,
            matched_rule="POL-ALLOW-001:ALL_INVARIANTS_SATISFIED",
            decision_details="Request verified and authorized under UIR security context.",
            is_authoritative=True,
            required_capabilities=gate_decision.required_capabilities,
        )
