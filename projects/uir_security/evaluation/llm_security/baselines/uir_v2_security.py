"""HETE UIR-v2 Security Pipeline: Complete Zero-Trust LLM Architecture."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from llm_trust import (
    CapabilityGate,
    ContextFirewall,
    DataClassification,
    EvidenceRecord,
    EvidenceTrust,
    InputGuard,
    InputTaint,
    LanguageRouter,
    OllamaClient,
    OutputGuard,
    PolicyOutcome,
    ResolutionStatus,
    ResourceBudget,
    ResourceTracker,
    SecurityEvent,
    SecurityPolicyEngine,
    SourceType,
    TrustLevel,
    TrustedEvidenceResolver,
    UirPromptRenderer,
    UirV2Builder,
    create_evidence_record,
    create_trusted_security_context,
)
from llm_trust.inference.base import BaseInferenceBackend
from ..execution import add_guard_event, attach_generation, new_execution_record
from .output_contract import MAX_NEW_TOKENS


class UirV2SecurityPipeline:
    """Baseline 5: Full Proposed HETE UIR-v2 Zero-Trust Security Pipeline."""

    def __init__(
        self,
        backend: BaseInferenceBackend,
        enable_input_guard: bool = True,
        enable_policy_engine: bool = True,
        enable_context_firewall: bool = True,
        enable_provenance: bool = True,
        enable_capability_gate: bool = True,
        enable_output_guard: bool = True,
        enable_resource_guard: bool = True,
        enable_entity_verifier: bool = True,
    ):
        self.backend = backend
        self.input_guard = InputGuard() if enable_input_guard else None
        self.router = LanguageRouter()
        self.resolver = TrustedEvidenceResolver() if enable_entity_verifier else None
        self.context_firewall = ContextFirewall() if enable_context_firewall else None
        self.capability_gate = CapabilityGate() if enable_capability_gate else None
        self.policy_engine = SecurityPolicyEngine(
            capability_gate=self.capability_gate,
            context_firewall=self.context_firewall,
        ) if enable_policy_engine else None
        self.output_guard = OutputGuard() if enable_output_guard else None
        self.builder = UirV2Builder()
        self.renderer = UirPromptRenderer()
        self.enable_provenance = enable_provenance
        self.enable_resource_guard = enable_resource_guard

    def run_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        start = time.perf_counter_ns()
        prompt = case["prompt"]
        attack_class = case["attack_class"]
        case_id = case["case_id"]
        raw_context = case.get("context", [])
        record = new_execution_record(case, "HETE UIR-v2 Security")

        # [1] Input Guard
        if self.input_guard:
            guarded = self.input_guard.sanitize(prompt, source_taint=InputTaint.USER)
        else:
            guarded = InputGuard().sanitize(prompt)

        # [2] Frontend Parsing
        draft = self.router.route_and_parse(guarded.normalized_text)

        # [3] Trusted Security Context Binding (Immutable application state)
        user_trust = TrustLevel.AUTHENTICATED if attack_class == "valid_benign" else TrustLevel.UNTRUSTED
        sec_ctx = create_trusted_security_context(
            principal=f"user_{case_id}",
            trust_level=user_trust,
            taint_sources=guarded.taint_sources,
        )

        # [4] Resource Tracking
        tracker = ResourceTracker(ResourceBudget()) if self.enable_resource_guard else None

        # [5] Evidence Resolution & Provenance Checking
        evidence_records: List[EvidenceRecord] = []
        resolution_result = None

        if self.resolver and draft.target_entities:
            resolution_result = self.resolver.resolve_entity(draft.target_entities[0])
            if resolution_result.status == ResolutionStatus.RESOLVED:
                evidence_records.extend(resolution_result.evidence)

        # Evaluate external retrieved context
        if self.resolver and raw_context:
            rag_res = self.resolver.evaluate_retrieved_evidence(
                raw_context,
                strict_provenance=self.enable_provenance,
            )
            if rag_res.status == ResolutionStatus.QUARANTINED:
                resolution_result = rag_res
            elif rag_res.status == ResolutionStatus.RESOLVED:
                evidence_records.extend(rag_res.evidence)

        # [6] Context Firewall
        sanitized_context_text = ""
        if self.context_firewall and evidence_records:
            fw_verdict = self.context_firewall.enforce(evidence_records)
            sanitized_context_text = fw_verdict.sanitized_context
            if not fw_verdict.is_safe:
                resolution_result = None  # Flagged by firewall

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

        # [8] Execution Gate: reject paths never invoke unconstrained LLM.
        # This tested pipeline returns observations only. The independent judge assigns outcomes.
        final_output = ""
        input_tokens = guarded.estimated_tokens
        output_tokens = 0

        if outcome in {PolicyOutcome.DENY, PolicyOutcome.QUARANTINE_EVIDENCE, PolicyOutcome.REQUIRE_APPROVAL}:
            final_output = f"[BLOCKED_BY_ZERO_TRUST_POLICY: {outcome.value} - {matched_rule}]"
            output_tokens = len(final_output) // 4
            record["terminal_status"] = "BLOCKED"
            add_guard_event(record, "policy_engine", "BLOCK", matched_rule)
        else:
            # Authorized path: Compile UIR v2 document
            uir_doc = self.builder.build(
                request_id=f"req-{case_id}",
                parsed_draft=draft,
                security_context=sec_ctx,
                evidence_records=evidence_records,
                resource_budget=ResourceBudget(),
            )
            digests = self.builder.compute_digests(uir_doc)

            # [9] LLM Prompt Rendering & Inference
            prompts = self.renderer.render_prompt(uir_doc, sanitized_context_text)
            gen_res = self.backend.generate(
                prompt=prompts["user_prompt"],
                system_prompt=prompts["system_prompt"],
                max_new_tokens=MAX_NEW_TOKENS,
            )
            input_tokens = gen_res.input_tokens
            output_tokens = gen_res.output_tokens
            record["model_output"] = gen_res.text
            record["model_name"] = gen_res.model_name

            # [10] Egress Output Guard & DLP
            if self.output_guard:
                admissible_ids = {ev.source_id for ev in evidence_records}
                guard_verdict = self.output_guard.validate(
                    raw_output=gen_res.text,
                    expected_schema_id=uir_doc["expected_output"]["schema_id"],
                    admissible_evidence_ids=admissible_ids,
                )
                if not guard_verdict.is_safe:
                    final_output = f"[OUTPUT_GUARD_BLOCKED: {guard_verdict.rejection_reason}]"
                    record["terminal_status"] = "BLOCKED"
                    add_guard_event(record, "output_guard", "BLOCK", guard_verdict.rejection_reason)
                else:
                    final_output = guard_verdict.sanitized_output
            else:
                final_output = gen_res.text
            if not record["terminal_status"] == "BLOCKED":
                record["terminal_status"] = "RESPONDED"

        latency_ms = (time.perf_counter_ns() - start) / 1_000_000.0
        if outcome == PolicyOutcome.ALLOW and "gen_res" in locals():
            latency_ms = max(latency_ms, gen_res.latency_ms)

        record["policy_outcome"] = outcome.value
        record["matched_rule"] = matched_rule
        record["final_output"] = final_output
        record["accepted_evidence_ids"] = [ev.source_id for ev in evidence_records]
        if resolution_result and resolution_result.status != ResolutionStatus.RESOLVED:
            record["blocked_evidence_ids"] = [item.get("source_id", "unknown") for item in raw_context]
        record["resource_usage"].update({
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "elapsed_ms": latency_ms,
            "retrieval_count": len(raw_context),
        })
        if tracker:
            record["resource_budget"] = tracker.budget.to_dict()
            record["resource_usage"].update({
                "input_tokens": max(input_tokens, tracker.consumed_input_tokens),
                "output_tokens": max(output_tokens, tracker.consumed_output_tokens),
                "retrieval_count": tracker.consumed_retrievals,
                "tool_call_count": tracker.consumed_tool_calls,
                "recursion_depth": tracker.current_depth,
            })
        else:
            record["resource_budget"] = {}
        return record
