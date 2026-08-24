"""Security Audit Records and Cross-Layer Zero-Trust Evidence Envelope."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class TrustDomain(str, Enum):
    NETWORK_TRUST = "NETWORK_TRUST"      # DLG-GNN Fraud & Anomaly Detection
    PROCESS_TRUST = "PROCESS_TRUST"      # POA / PBEA State Transition Isolation
    AI_DATA_TRUST = "AI_DATA_TRUST"      # HETE UIR Zero-Trust Representation


@dataclass(frozen=True)
class SecurityEvent:
    """Audit record capturing deterministic security decisions and hash chains."""
    event_id: str
    request_id: str
    uir_digest: str
    semantic_digest: str
    policy_digest: str
    policy_outcome: str
    matched_rule: str
    evidence_hashes: List[str]
    model_name: str
    output_hash: str
    terminal_outcome: str
    latency_ms: float
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "request_id": self.request_id,
            "uir_digest": self.uir_digest,
            "semantic_digest": self.semantic_digest,
            "policy_digest": self.policy_digest,
            "policy_outcome": self.policy_outcome,
            "matched_rule": self.matched_rule,
            "evidence_hashes": self.evidence_hashes,
            "model_name": self.model_name,
            "output_hash": self.output_hash,
            "terminal_outcome": self.terminal_outcome,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at,
        }

    def canonical_digest(self) -> str:
        """Calculates RFC 8785 canonical hash of the security event for immutable audit chaining."""
        raw = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class UnifiedZeroTrustEnvelope:
    """Dissertation Integration Hook: Common Zero-Trust Evidence Envelope.

    Connects:
    - Network Trust (DLG-GNN transaction risk scores)
    - Process Trust (POA/PBEA AACO execution proofs)
    - AI/Data Trust (HETE-UIR security digests and policy gates)
    """
    envelope_id: str
    timestamp: str
    session_id: str
    network_trust_evidence: Optional[Dict[str, Any]] = None   # DLG-GNN anomaly score & subgraph hash
    process_trust_evidence: Optional[Dict[str, Any]] = None   # POA/PBEA state transition & warrant hash
    ai_data_trust_evidence: Optional[Dict[str, Any]] = None   # UIR digests, policy decision & output hash
    aggregated_trust_verdict: str = "TRUSTED"                 # TRUSTED | QUARANTINED | REJECTED
    envelope_signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "network_trust_evidence": self.network_trust_evidence,
            "process_trust_evidence": self.process_trust_evidence,
            "ai_data_trust_evidence": self.ai_data_trust_evidence,
            "aggregated_trust_verdict": self.aggregated_trust_verdict,
            "envelope_signature": self.envelope_signature,
        }

    def envelope_digest(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
