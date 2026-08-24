"""HETE UIR Zero-Trust LLM Security Architecture Package."""
from .audit.security_event import SecurityEvent, UnifiedZeroTrustEnvelope
from .evidence.provenance import EvidenceRecord, EvidenceTrust, SourceType, create_evidence_record
from .evidence.trusted_resolver import ResolutionResult, ResolutionStatus, TrustedEvidenceResolver
from .frontends.base import BaseFrontend, ParsedDraft
from .frontends.router import LanguageRouter
from .inference.base import BaseInferenceBackend, GenerationResult
from .inference.ollama_client import OllamaClient
from .inference.renderer import UirPromptRenderer
from .policy.security_policy_engine import PolicyEvaluationResult, PolicyOutcome, SecurityPolicyEngine
from .security.capability_gate import CapabilityGate, CapabilityGateVerdict, GateDecision
from .security.context_firewall import ContextFirewall, FirewallVerdict
from .security.input_guard import GuardedInput, InputGuard
from .security.output_guard import OutputGuard, OutputGuardVerdict, OutputValidationStatus
from .security.resource_guard import ResourceBudget, ResourceTracker
from .uir.builder import UirV2Builder, canonicalize_json, compute_sha256
from .uir.security_context import (
    DataClassification,
    HIGH_IMPACT_CAPABILITIES,
    InputTaint,
    ROLE_CAPABILITY_MAP,
    SecurityContext,
    TrustLevel,
    create_trusted_security_context,
)

__all__ = [
    "SecurityEvent",
    "UnifiedZeroTrustEnvelope",
    "EvidenceRecord",
    "EvidenceTrust",
    "SourceType",
    "create_evidence_record",
    "ResolutionResult",
    "ResolutionStatus",
    "TrustedEvidenceResolver",
    "BaseFrontend",
    "ParsedDraft",
    "LanguageRouter",
    "BaseInferenceBackend",
    "GenerationResult",
    "OllamaClient",
    "UirPromptRenderer",
    "PolicyEvaluationResult",
    "PolicyOutcome",
    "SecurityPolicyEngine",
    "CapabilityGate",
    "CapabilityGateVerdict",
    "GateDecision",
    "ContextFirewall",
    "FirewallVerdict",
    "GuardedInput",
    "InputGuard",
    "OutputGuard",
    "OutputGuardVerdict",
    "OutputValidationStatus",
    "ResourceBudget",
    "ResourceTracker",
    "UirV2Builder",
    "canonicalize_json",
    "compute_sha256",
    "DataClassification",
    "HIGH_IMPACT_CAPABILITIES",
    "InputTaint",
    "ROLE_CAPABILITY_MAP",
    "SecurityContext",
    "TrustLevel",
    "create_trusted_security_context",
]
