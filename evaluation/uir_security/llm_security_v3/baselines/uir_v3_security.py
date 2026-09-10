"""HETE UIR-v3 Security Pipeline: Strict Zero-Trust Architecture.

Crucial Architectural Guarantees:
1. ZERO ORACLE LEAKAGE: Ingests ONLY RuntimeCase. Never reads attack_class,
   attack_goal, or any evaluation oracle field.
2. INDEPENDENT PRINCIPALS: User trust and capabilities derive exclusively
   from authenticated session state (principal_id), identical across benign
   and attack rows.
3. TYPED PROVENANCE: Strictly validates evidence authorities and hashes,
   eliminating substring spoofing vulnerabilities.
4. DEFENSE-IN-DEPTH: Layered InputGuard, ContextFirewall, PolicyEngine,
   CapabilityGate, and OutputGuard.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from llm_trust import (
    ContextFirewall,
    InputGuard,
    InputTaint,
    LanguageRouter,
    OutputGuard,
    OutputValidationStatus,
    PolicyOutcome,
    ResourceBudget,
    ResourceTracker,
    SecurityPolicyEngine,
    TrustLevel,
    create_trusted_security_context,
)
from llm_trust.evidence.provenance import EvidenceRecord, EvidenceTrust, SourceType
from llm_trust.evidence.trusted_resolver import (
    ResolutionResult,
    ResolutionStatus,
    TrustedEvidenceResolver,
)
from llm_trust.inference.base import BaseInferenceBackend, GenerationResult
from llm_trust.inference.renderer import UirPromptRenderer
from llm_trust.uir.builder import UirV2Builder

from ..schema.runtime_case import RuntimeCase
from ..provenance import ProvenanceTier, ProvenanceVerifier, TypedEvidenceRecord


def load_principal_config(principal_id: str) -> Dict[str, Any]:
    """Load principal configuration from trusted fixtures."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "principals.json"
    if fixture_path.exists():
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            principals = data.get("principals", {})
            if principal_id in principals:
                return principals[principal_id]
    return {
        "principal_id": principal_id,
        "trust_level": "AUTHENTICATED",
        "allowed_capabilities": [
            "read:financial_records",
            "read:market_data",
            "compute:financial_metrics",
            "generate:summary_report",
        ],
        "data_clearance": "CONFIDENTIAL",
    }


class UirV3SecurityPipeline:
    """Production HETE v3 Pipeline with Zero-Trust Enforcement."""

    def __init__(
        self,
        backend: BaseInferenceBackend,
        router: Optional[LanguageRouter] = None,
        builder: Optional[UirV2Builder] = None,
        renderer: Optional[UirPromptRenderer] = None,
        policy_engine: Optional[SecurityPolicyEngine] = None,
        resolver: Optional[TrustedEvidenceResolver] = None,
        provenance_verifier: Optional[ProvenanceVerifier] = None,
        context_firewall: Optional[ContextFirewall] = None,
        output_guard: Optional[OutputGuard] = None,
        input_guard: Optional[InputGuard] = None,
        enable_provenance: bool = True,
        enable_context_firewall: bool = True,
        enable_capability_gate: bool = True,
        enable_output_guard: bool = True,
        enable_resource_guard: bool = True,
        enable_entity_verifier: bool = True,
    ):
        self.backend = backend
        self.router = router or LanguageRouter()
        self.builder = builder or UirV2Builder()
        self.renderer = renderer or UirPromptRenderer()
        self.policy_engine = policy_engine or SecurityPolicyEngine()
        self.resolver = resolver or TrustedEvidenceResolver()
        self.provenance_verifier = provenance_verifier or ProvenanceVerifier()
        self.context_firewall = context_firewall if enable_context_firewall else None
        self.output_guard = output_guard or OutputGuard()
        self.input_guard = input_guard or InputGuard()

        self.enable_provenance = enable_provenance
        self.enable_context_firewall = enable_context_firewall
        self.enable_capability_gate = enable_capability_gate
        self.enable_output_guard = enable_output_guard
        self.enable_resource_guard = enable_resource_guard
        self.enable_entity_verifier = enable_entity_verifier

    def run_case(self, case: RuntimeCase | Dict[str, Any]) -> Dict[str, Any]:
        start_ns = time.perf_counter_ns()

        # Enforce RuntimeCase view - zero access to oracle fields
        if isinstance(case, RuntimeCase):
            runtime_case = case
        else:
            runtime_case = RuntimeCase.from_dict(case)

        case_id = runtime_case.case_id
        user_input = runtime_case.user_input
        language = runtime_case.language
        raw_context = runtime_case.retrieved_context
        principal_id = runtime_case.principal_id

        record: Dict[str, Any] = {
            "case_id": case_id,
            "baseline": "HETE UIR-v3 Security",
            "language": language,
            "principal_id": principal_id,
            "policy_outcome": "NOT_EVALUATED",
            "model_output": "",
            "final_output": "",
            "tool_calls": [],
            "retrieved_evidence_ids": [str(c.get("source_id", "")) for c in raw_context],
            "accepted_evidence_ids": [],
            "blocked_evidence_ids": [],
            "data_disclosures": [],
            "resource_usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "retrieval_count": len(raw_context),
                "tool_call_count": 0,
                "recursion_depth": 1,
                "elapsed_ms": 0.0,
                "path": "UNKNOWN",
            },
            "guard_events": [],
            "terminal_status": "ERROR",
            "model_compromised": False,
        }

        # [1] Input Guard: normalization, size limit, and telemetry
        guarded = self.input_guard.sanitize(user_input, source_taint=InputTaint.USER)
        if guarded.suspicious_telemetry_flags:
            for flag in guarded.suspicious_telemetry_flags:
                record["guard_events"].append({"component": "InputGuard", "decision": "FLAGGED", "detail": flag})

        # [2] Frontend Parsing
        draft = self.router.route_and_parse(guarded.normalized_text)

        # [3] Trusted Security Context Binding from Principal Configuration (Label-Independent)
        principal_config = load_principal_config(principal_id)
        trust_str = principal_config.get("trust_level", "AUTHENTICATED")
        user_trust = TrustLevel(trust_str) if trust_str in TrustLevel.__members__ else TrustLevel.AUTHENTICATED

        sec_ctx = create_trusted_security_context(
            principal=principal_id,
            trust_level=user_trust,
            taint_sources=guarded.taint_sources,
        )

        # [4] Resource Tracking
        tracker = ResourceTracker(ResourceBudget()) if self.enable_resource_guard else None

        # [5] Evidence Resolution & Provenance Checking
        evidence_records: List[EvidenceRecord] = []
        resolution_result = None

        if self.resolver and draft.target_entities and self.enable_entity_verifier:
            resolution_result = self.resolver.resolve_entity(draft.target_entities[0])
            if resolution_result.status == ResolutionStatus.RESOLVED:
                evidence_records.extend(resolution_result.evidence)

        # Evaluate external retrieved context with ProvenanceVerifier
        if raw_context:
            for item in raw_context:
                src_id = item.get("source_id", "unknown")
                cnt = item.get("content", "")
                sha = item.get("sha256")
                signer = item.get("signer")
                is_instr = bool(item.get("instruction_bearing", False))

                typed_rec = self.provenance_verifier.verify_record(
                    raw_source_id=src_id,
                    content=cnt,
                    provided_sha256=sha,
                    signer_id=signer,
                    instruction_bearing_hint=is_instr,
                )

                if typed_rec.is_authoritative() or not self.enable_provenance:
                    record["accepted_evidence_ids"].append(typed_rec.source_id)
                    evidence_records.append(
                        EvidenceRecord(
                            source_id=typed_rec.source_id,
                            source_type=SourceType.RAG,
                            trust=EvidenceTrust.TRUSTED,
                            sha256=typed_rec.identity.content_sha256,
                            verified=True,
                            instruction_bearing=False,
                            signer=typed_rec.identity.signer_id,
                            content_payload=cnt,
                        )
                    )
                else:
                    record["blocked_evidence_ids"].append(typed_rec.source_id)

        # [6] Context Firewall
        sanitized_context_text = ""
        if self.context_firewall and evidence_records:
            fw_verdict = self.context_firewall.enforce(evidence_records)
            sanitized_context_text = fw_verdict.sanitized_context
            if not fw_verdict.is_safe:
                resolution_result = None
                record["guard_events"].append({
                    "component": "ContextFirewall",
                    "decision": "QUARANTINED",
                    "detail": "Instruction payload detected and quarantined",
                })
        elif evidence_records:
            sanitized_context_text = "\n".join(e.content_payload for e in evidence_records if e.content_payload)

        # [7] Zero-Trust Policy Decision Point (PDP / PEP)
        if self.policy_engine:
            policy_res = self.policy_engine.evaluate_request(
                guarded_input=guarded,
                security_context=sec_ctx,
                action=draft.action,
                target_entities=draft.target_entities,
                resolution_result=resolution_result,
                resource_tracker=tracker,
            )
            outcome = policy_res.outcome
            matched_rule = policy_res.matched_rule
        else:
            outcome = PolicyOutcome.ALLOW
            matched_rule = "POLICY_ENGINE_DISABLED"

        record["policy_outcome"] = outcome.value

        # [8] Execution Gate: early block on policy denial
        if outcome in {PolicyOutcome.DENY, PolicyOutcome.QUARANTINE_EVIDENCE, PolicyOutcome.REQUIRE_APPROVAL}:
            record["terminal_status"] = "BLOCKED"
            record["final_output"] = f"[BLOCKED_BY_ZERO_TRUST_POLICY: {outcome.value} - {matched_rule}]"
            record["guard_events"].append({
                "component": "PolicyEngine",
                "decision": outcome.value,
                "detail": matched_rule,
            })
            total_elapsed = (time.perf_counter_ns() - start_ns) / 1_000_000.0
            record["resource_usage"]["elapsed_ms"] = total_elapsed
            record["resource_usage"]["path"] = "ATTACK_BLOCKED_PRE_LLM"
            return record

        # [9] Authorized Path: Build UIR and render prompt
        uir_doc = self.builder.build(
            request_id=f"req-{case_id}",
            parsed_draft=draft,
            security_context=sec_ctx,
            evidence_records=evidence_records,
            resource_budget=ResourceBudget(),
        )

        prompts = self.renderer.render_prompt(uir_doc, sanitized_context_text)
        gen_start_ns = time.perf_counter_ns()
        gen_result: GenerationResult = self.backend.generate(
            prompt=prompts["user_prompt"],
            system_prompt=prompts["system_prompt"],
            max_new_tokens=512,
            temperature=0.0,
        )

        record["model_output"] = gen_result.text
        record["model_name"] = gen_result.model_name
        record["resource_usage"]["input_tokens"] = gen_result.input_tokens
        record["resource_usage"]["output_tokens"] = gen_result.output_tokens

        # [10] Output Guard Verification
        if self.enable_output_guard and self.output_guard:
            valid_citations = set(record["accepted_evidence_ids"])
            if draft.target_entities:
                valid_citations.add(f"registry:{draft.target_entities[0].upper()}")

            out_verdict = self.output_guard.validate(
                raw_output=gen_result.text,
                expected_schema_id="financial_summary_v2",
                admissible_evidence_ids=valid_citations,
            )

            if not out_verdict.is_safe:
                record["guard_events"].append({
                    "component": "OutputGuard",
                    "decision": "REJECTED",
                    "detail": out_verdict.rejection_reason,
                })
                record["terminal_status"] = "BLOCKED"
                record["final_output"] = f"[OUTPUT_GUARD_BLOCKED]: {out_verdict.rejection_reason}"
                total_elapsed = (time.perf_counter_ns() - start_ns) / 1_000_000.0
                record["resource_usage"]["elapsed_ms"] = total_elapsed
                record["resource_usage"]["path"] = "ATTACK_LLM_INVOKED_BLOCKED_POST_LLM"
                return record

        total_elapsed = (time.perf_counter_ns() - start_ns) / 1_000_000.0
        record["resource_usage"]["elapsed_ms"] = total_elapsed
        record["resource_usage"]["path"] = "BENIGN_ALLOWED"
        record["terminal_status"] = "RESPONDED"
        record["final_output"] = gen_result.text
        return record
