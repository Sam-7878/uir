"""Evidence Provenance and Integrity Verification."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class SourceType(str, Enum):
    API = "API"
    SIGNED_DOC = "SIGNED_DOC"
    RAG = "RAG"
    TOOL = "TOOL"
    DATABASE = "DATABASE"
    USER_SUPPLIED = "USER_SUPPLIED"


class EvidenceTrust(str, Enum):
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True)
class EvidenceRecord:
    source_id: str
    source_type: SourceType
    trust: EvidenceTrust
    sha256: str
    verified: bool
    instruction_bearing: bool
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    signer: Optional[str] = None
    content_payload: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "trust": self.trust.value,
            "sha256": self.sha256,
            "verified": self.verified,
            "instruction_bearing": self.instruction_bearing,
            "retrieved_at": self.retrieved_at,
            "signer": self.signer,
            "content_payload": self.content_payload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceRecord:
        return cls(
            source_id=data["source_id"],
            source_type=SourceType(data["source_type"]),
            trust=EvidenceTrust(data["trust"]),
            sha256=data["sha256"],
            verified=bool(data.get("verified", False)),
            instruction_bearing=bool(data.get("instruction_bearing", False)),
            retrieved_at=data.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
            signer=data.get("signer"),
            content_payload=data.get("content_payload", ""),
        )

    def verify_integrity(self) -> bool:
        """Verify that content_payload matches sha256."""
        computed = hashlib.sha256(self.content_payload.encode("utf-8")).hexdigest()
        return computed == self.sha256


def create_evidence_record(
    source_id: str,
    content: str,
    source_type: SourceType,
    trust: EvidenceTrust = EvidenceTrust.UNTRUSTED,
    signer: Optional[str] = None,
    instruction_bearing: bool = False,
) -> EvidenceRecord:
    """Creates a cryptographic EvidenceRecord with calculated SHA-256."""
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    verified = (trust == EvidenceTrust.TRUSTED) and (signer is not None or source_type in {SourceType.API, SourceType.DATABASE})
    return EvidenceRecord(
        source_id=source_id,
        source_type=source_type,
        trust=trust,
        sha256=content_hash,
        verified=verified,
        instruction_bearing=instruction_bearing,
        signer=signer,
        content_payload=content,
    )
