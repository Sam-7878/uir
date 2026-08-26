"""UIR-v1 Baseline: Entity validation and basic policy compilation without v2 security controls."""
from __future__ import annotations

import time
from typing import Any, Dict

from llm_trust.evidence.trusted_resolver import ResolutionStatus, TrustedEvidenceResolver
from llm_trust.frontends.router import LanguageRouter
from llm_trust.inference.base import BaseInferenceBackend
from ..execution import add_guard_event, attach_generation, new_execution_record


class UirV1Baseline:
    """Baseline 4: UIR-v1 (entity verification & basic action constraints, but lacking v2 security)."""

    def __init__(self, backend: BaseInferenceBackend):
        self.backend = backend
        self.router = LanguageRouter()
        self.resolver = TrustedEvidenceResolver()

    def run_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        start = time.perf_counter_ns()
        prompt = case["prompt"]
        record = new_execution_record(case, "UIR-v1")
        draft = self.router.route_and_parse(prompt)

        # 1. UIR-v1 performs entity resolution
        res = self.resolver.resolve_entity(draft.target_entities[0] if draft.target_entities else "UNKNOWN")

        if res.status == ResolutionStatus.NO_VERIFIED_EVIDENCE:
            record.update({
                "policy_outcome": "REJECT",
                "final_output": f"[UIR-v1 Rejected: {res.status.value}]",
                "terminal_status": "BLOCKED",
            })
            add_guard_event(record, "entity_resolver", "BLOCK", res.rejection_reason or "")
        else:
            generated = self.backend.generate(prompt=prompt, system_prompt="UIR-v1 Compiler Mode", max_new_tokens=128)
            attach_generation(record, generated.text, generated.input_tokens, generated.output_tokens,
                              (time.perf_counter_ns() - start) / 1_000_000.0, generated.model_name)
            record["policy_outcome"] = "ALLOW"
            record["accepted_evidence_ids"] = [evidence.source_id for evidence in res.evidence]
        record["resource_usage"]["elapsed_ms"] = (time.perf_counter_ns() - start) / 1_000_000.0
        return record
