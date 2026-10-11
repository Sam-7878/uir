"""Evidence package."""
from .provenance import (
    EvidenceRecord,
    EvidenceTrust,
    SourceType,
    create_evidence_record,
)
from .trusted_resolver import (
    ALLOWED_SOURCE_DOMAINS,
    NONEXISTENT_ENTITIES,
    VERIFIED_ENTITY_REGISTRY,
    ResolutionResult,
    ResolutionStatus,
    TrustedEvidenceResolver,
)

__all__ = [
    "EvidenceRecord",
    "EvidenceTrust",
    "SourceType",
    "create_evidence_record",
    "ALLOWED_SOURCE_DOMAINS",
    "NONEXISTENT_ENTITIES",
    "VERIFIED_ENTITY_REGISTRY",
    "ResolutionResult",
    "ResolutionStatus",
    "TrustedEvidenceResolver",
]
