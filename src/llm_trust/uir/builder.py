"""UIR v2 Builder, Canonicalization, and Schema Validator."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema

from ..evidence.provenance import EvidenceRecord
from ..frontends.base import ParsedDraft
from ..security.resource_guard import ResourceBudget
from .security_context import SecurityContext


SCHEMA_V2_PATH = Path(__file__).parent / "schema_v2.json"


def _load_schema_v2() -> Dict[str, Any]:
    with open(SCHEMA_V2_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_COMPILED_SCHEMA_V2 = jsonschema.Draft202012Validator(_load_schema_v2())


def canonicalize_json(data: Any) -> str:
    """Deterministic RFC 8785 (JCS) JSON canonical serialization."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class UirV2Builder:
    """Builds valid UIR v2 documents with cryptographic digests and schema compliance."""

    def __init__(self, validator: Optional[jsonschema.Draft202012Validator] = None):
        self.validator = validator or _COMPILED_SCHEMA_V2

    def build(
        self,
        request_id: str,
        parsed_draft: ParsedDraft,
        security_context: SecurityContext,
        evidence_records: Optional[List[EvidenceRecord]] = None,
        resource_budget: Optional[ResourceBudget] = None,
        policy_constraints: Optional[List[Dict[str, Any]]] = None,
        expected_output: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Constructs a full UIR v2 document."""
        if evidence_records is None:
            evidence_records = []
        if resource_budget is None:
            resource_budget = ResourceBudget()
        if policy_constraints is None:
            policy_constraints = [
                {
                    "id": "POL-SYS-001",
                    "level": "L0_SYSTEM",
                    "condition": {"operator": "EQ", "left": "untrusted_override", "right": False},
                    "enforcement": "BLOCK_EXECUTION",
                    "source": "kernel_security_policy",
                }
            ]
        if expected_output is None:
            expected_output = {
                "schema_id": "structured_fact_response",
                "citations_required": True,
                "numeric_exactness": True,
                "allow_external_inference": False,
                "unsupported_claim_behavior": "FILTER_AND_RENDER",
            }

        source_hash = f"sha256:{compute_sha256(parsed_draft.raw_prompt)}"
        created_at = datetime.now(timezone.utc).isoformat()

        uir_doc: Dict[str, Any] = {
            "uir_version": "2.0",
            "metadata": {
                "request_id": request_id,
                "source_lang": parsed_draft.language,
                "domain": parsed_draft.domain,
                "target_id": parsed_draft.target_entities,
                "source_hash": source_hash,
                "created_at": created_at,
            },
            "intent": {
                "action": parsed_draft.action,
                "arguments": parsed_draft.arguments,
                "conditions": parsed_draft.conditions,
                "temporal_scope": parsed_draft.temporal_scope,
            },
            "security_context": security_context.to_dict(),
            "evidence": [ev.to_dict() for ev in evidence_records],
            "resource_budget": resource_budget.to_dict(),
            "policy_constraints": policy_constraints,
            "expected_output": expected_output,
        }

        # Validate strictly against JSON Schema v2
        self.validator.validate(uir_doc)

        return uir_doc

    def compute_digests(self, uir_doc: Dict[str, Any]) -> Dict[str, str]:
        """Calculates uir_digest, semantic_digest, and policy_digest."""
        # 1. uir_digest: full canonical representation
        full_canonical = canonicalize_json(uir_doc)
        uir_dig = compute_sha256(full_canonical)

        # 2. semantic_digest: intent + target_id + domain (excludes request_id, timestamp, hashes)
        semantic_view = {
            "intent": uir_doc["intent"],
            "target_id": uir_doc["metadata"]["target_id"],
            "domain": uir_doc["metadata"]["domain"],
        }
        semantic_canonical = canonicalize_json(semantic_view)
        sem_dig = compute_sha256(semantic_canonical)

        # 3. policy_digest: security_context + policy_constraints + resource_budget
        policy_view = {
            "security_context": uir_doc["security_context"],
            "policy_constraints": uir_doc["policy_constraints"],
            "resource_budget": uir_doc["resource_budget"],
        }
        policy_canonical = canonicalize_json(policy_view)
        pol_dig = compute_sha256(policy_canonical)

        return {
            "uir_digest": uir_dig,
            "semantic_digest": sem_dig,
            "policy_digest": pol_dig,
        }
