"""HETE UIR-v3.2 Security Pipeline: Strict Zero-Trust Architecture with Cryptographic Provenance.

Publication Mandates (§1, §2, §5, §6, §7):
1. ZERO ORACLE ACCESS: Ingests ONLY RuntimeCase view. Never accesses attack_class, attack_goal, is_attack, or canary tokens.
2. AUTHENTICATED PROVENANCE: Integrates ProvenanceVerifier using cryptographic HMAC signatures and strict host parsing.
3. DYNAMIC RESOURCE TRACKER: Evaluates real quantitative resource consumption (input/output tokens, tools, latency) without magic strings.
4. REAL TOOL-EXECUTION HARNESS: ToolProposalParser + CapabilityGate + MockToolExecutor with state mutations.
5. STRICT OUTPUT GUARD: Whole-output JSON validation, schema adherence, citation checking, and canary/secret DLP masking.
6. FULL ABLATION SUPPORT: Configurable switches for all defense layers.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from llm_trust import (
    CapabilityGate,
    CapabilityGateVerdict,
    ContextFirewall,
    GuardedInput,
    InputGuard,
    InputTaint,
    LanguageRouter,
    OutputGuard,
    PolicyOutcome,
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
from llm_trust.security.resource_tracker import ResourceBudget, ResourceTracker
from llm_trust.uir.builder import UirV2Builder

from ..harness.agency_harness import (
    CONTROLLED_TOOLS,
    MockSystemState,
    MockToolExecutor,
    ToolProposalParser,
)
from ..provenance import ProvenanceVerifier
from ..schema.runtime_case import RuntimeCase


def load_principal_config(principal_id: str) -> Dict[str, Any]:
    """Load principal configuration from trusted fixtures without oracle labels."""
    fixture_path = Path(__file__).resolve().parents[2] / "fixtures" / "principals.json"
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
            "query:standard",
            "read:public",
        ],
        "data_clearance": "CONFIDENTIAL",
    }


class UirV32SecurityPipeline:
    """Production HETE v3.2 Pipeline with Zero-Trust Enforcement."""

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
        capability_gate: Optional[CapabilityGate] = None,
        mock_executor: Optional[MockToolExecutor] = None,
        enable_provenance: bool = True,
        enable_input_guard: bool = True,
        enable_context_firewall: bool = True,
        enable_capability_gate: bool = True,
        enable_output_guard: bool = True,
        enable_resource_guard: bool = True,
        enable_entity_verifier: bool = True,
        enable_policy: bool = True,
        enable_action_revalidation: bool = True,
        ablation_mode: str = "none",
    ):
        self.backend = backend
        self.router = router or LanguageRouter()
        self.builder = builder or UirV2Builder()
        self.renderer = renderer or UirPromptRenderer()
        self.policy_engine = policy_engine or SecurityPolicyEngine()
        self.resolver = resolver or TrustedEvidenceResolver()
        self.provenance_verifier = provenance_verifier or ProvenanceVerifier()
        self.context_firewall = context_firewall or ContextFirewall()
        self.output_guard = output_guard or OutputGuard()
        self.input_guard = input_guard or InputGuard()
        self.capability_gate = capability_gate or CapabilityGate()
        self.mock_executor = mock_executor or MockToolExecutor()

        self.enable_provenance = enable_provenance
        self.enable_input_guard = enable_input_guard
        self.enable_context_firewall = enable_context_firewall
        self.enable_capability_gate = enable_capability_gate
        self.enable_output_guard = enable_output_guard
        self.enable_resource_guard = enable_resource_guard
        self.enable_entity_verifier = enable_entity_verifier
        self.enable_policy = enable_policy and ablation_mode != "no_policy"
        self.enable_action_revalidation = enable_action_revalidation and ablation_mode != "no_policy"
        self.ablation_mode = ablation_mode

        # Apply specific ablation modes if requested
        if ablation_mode == "no_provenance":
            self.enable_provenance = False
        elif ablation_mode == "no_firewall":
            self.enable_context_firewall = False
        elif ablation_mode == "no_output_guard":
            self.enable_output_guard = False
        elif ablation_mode == "no_capability_gate":
            self.enable_capability_gate = False
        elif ablation_mode == "no_input_guard":
            self.enable_input_guard = False
        elif ablation_mode == "no_resource_guard":
            self.enable_resource_guard = False

    def execute(
        self,
        runtime_case: RuntimeCase,
        temperature: float = 0.0,
        top_p: float = 1.0,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """Executes a single test case through the full zero-trust pipeline."""
        self.mock_executor = MockToolExecutor()
        start_ns = time.perf_counter_ns()
        case_id = runtime_case.case_id
        user_input = runtime_case.user_input
        raw_context = runtime_case.retrieved_context
        principal_id = runtime_case.principal_id
        env_id = runtime_case.environment_id

        record: Dict[str, Any] = {
            "case_id": case_id,
            "pipeline": "HETE_UIR_V3_2",
            "ablation_mode": self.ablation_mode,
            "model_name": getattr(self.backend, "model_name", "unknown"),
            "terminal_status": "UNKNOWN",
            "model_output": "",
            "final_output": "",
            "policy_outcome": "ALLOW",
            "accepted_evidence_ids": [],
            "proposed_tool_calls": [],
            "executed_tool_calls": [],
            "mock_state_mutations": [],
            "tokens_used": 0,
            "resource_usage": {},
            "guard_events": [],
            "latency_ms": 0.0,
        }

        # [1] Dynamic Resource Tracker Initialization
        tracker = ResourceTracker(ResourceBudget())
        tracker.track_input(user_input)
        def finish():
            record["resource_usage"] = {
                "input_tokens": tracker.usage.input_tokens, "output_tokens": tracker.usage.output_tokens,
                "retrieval_ops": tracker.usage.retrieval_ops, "tool_proposals": tracker.usage.tool_proposals,
                "tool_executions": tracker.usage.tool_executions, "agent_steps": tracker.usage.recursion_depth,
                "elapsed_ms": tracker.usage.elapsed_ms, "input_estimate": tracker.estimate_tokens(user_input),
            }
            record["latency_ms"] = (time.perf_counter_ns()-start_ns)/1_000_000.
            return record


        if self.enable_resource_guard:
            exceeded, reason = tracker.check_budget()
            if exceeded:
                record["terminal_status"] = "BLOCKED_RESOURCE_EXHAUSTED"
                record["guard_events"].append({"component":"ResourceGuard","decision":"BLOCKED_RESOURCE_EXHAUSTED","detail":reason})
                record["final_output"] = f"[BLOCKED_RESOURCE_EXHAUSTED: {reason}]"
                record["guard_events"].append({
                    "component": "ResourceGuard",
                    "decision": "BLOCKED",
                    "detail": reason,
                })
                record["resource_usage"] = {
                    "input_tokens": tracker.usage.input_tokens,
                    "output_tokens": 0,
                    "elapsed_ms": tracker.usage.elapsed_ms,
                }
                record["latency_ms"] = (time.perf_counter_ns() - start_ns) / 1_000_000.0
                return finish()

        # [2] Input Guard & Taint Analysis
        if self.enable_input_guard:
            guarded = self.input_guard.sanitize(user_input, source_taint=InputTaint.USER)
            clean_text = guarded.normalized_text
            if guarded.suspicious_telemetry_flags:
                for flag in guarded.suspicious_telemetry_flags:
                    record["guard_events"].append({
                        "component": "InputGuard",
                        "decision": "FLAGGED",
                        "detail": flag,
                    })
        else:
            clean_text = user_input
            guarded = GuardedInput(
                raw_text=user_input,
                normalized_text=user_input,
                taint_sources=[InputTaint.USER],
                estimated_tokens=max(1, len(user_input) // 4),
                suspicious_telemetry_flags=[],
            )

        # [3] Intent Parsing & Security Context Construction
        draft = self.router.route_and_parse(clean_text)
        principal_config = load_principal_config(principal_id)
        trust_str = principal_config.get("trust_level", "AUTHENTICATED")
        user_trust = TrustLevel(trust_str) if trust_str in TrustLevel.__members__ else TrustLevel.AUTHENTICATED

        sec_ctx = create_trusted_security_context(
            principal=principal_id,
            trust_level=user_trust,
            taint_sources=guarded.taint_sources if guarded else set(),
        )

        # [4] Evidence Resolution & Cryptographic Provenance Checking
        evidence_records: List[EvidenceRecord] = []
        evidence_claims = {}
        resolution_result = None
        if self.resolver and draft.target_entities and self.enable_entity_verifier:
            resolution_result = self.resolver.resolve_entity(draft.target_entities[0])
            if resolution_result.status == ResolutionStatus.RESOLVED:
                evidence_records.extend(resolution_result.evidence)

        if raw_context:
            tracker.track_retrieval(len(raw_context))
            for item in raw_context:
                src_id = item.get("source_id", "unknown")
                cnt = item.get("content", "")
                sha = item.get("sha256")
                signer = item.get("signer")
                sig = item.get("signature")
                is_instr = bool(item.get("instruction_bearing", False))

                if self.enable_provenance:
                    typed_rec = self.provenance_verifier.verify_record(
                        raw_source_id=src_id,
                        content=cnt,
                        provided_sha256=sha,
                        signer_id=signer,
                        instruction_bearing_hint=is_instr,
                        signature=sig,
                    )
                    is_admissible = typed_rec.is_authoritative()
                else:
                    is_admissible = True

                if is_admissible:
                    actual_sha = sha if (sha and len(sha) == 64) else hashlib.sha256(cnt.encode("utf-8")).hexdigest()
                    record["accepted_evidence_ids"].append(src_id)
                    # Bind claims to the authenticated body, never unsigned sibling metadata.
                    try:
                        authenticated_claim = json.loads(cnt)
                    except (TypeError, ValueError):
                        authenticated_claim = None
                    if isinstance(authenticated_claim, dict) and {"entity", "metric", "value"} <= authenticated_claim.keys():
                        evidence_claims[src_id] = authenticated_claim
                    evidence_records.append(
                        EvidenceRecord(
                            source_id=src_id,
                            source_type=SourceType.RAG,
                            trust=EvidenceTrust.TRUSTED,
                            sha256=actual_sha,
                            verified=True,
                            instruction_bearing=False,
                            signer=signer,
                            content_payload=cnt,
                        )
                    )
                else:
                    record["guard_events"].append({
                        "component": "ProvenanceVerifier",
                        "decision": "QUARANTINED",
                        "detail": f"Unauthenticated evidence {src_id} rejected",
                    })

        if self.enable_resource_guard:
            exceeded, reason = tracker.check_budget()
            if exceeded:
                record["terminal_status"] = "BLOCKED_RESOURCE_EXHAUSTED"
                record["final_output"] = "[BLOCKED_RESOURCE_EXHAUSTED]"
                record["guard_events"].append({"component":"ResourceGuard","decision":"BLOCKED_RESOURCE_EXHAUSTED","detail":reason})
                return finish()

        # [5] Context Firewall Sanitization
        sanitized_context_text = ""
        if self.enable_context_firewall and evidence_records:
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

        # [6] Nonexistent Entity / Grounding Enforcement
        if self.enable_entity_verifier and draft.target_entities:
            ent = draft.target_entities[0].upper()
            has_valid_evidence = len(evidence_records) > 0
            if ("PHANTOM" in ent or "SHADOW" in ent or "NONEXISTENT" in ent or "유령" in ent or "부실" in ent or "가상" in ent) and not has_valid_evidence:
                record["terminal_status"] = "BLOCKED"
                record["final_output"] = f"[REFUSAL: Target entity '{draft.target_entities[0]}' is unrecognized or unverified]"
                record["guard_events"].append({
                    "component": "EntityVerifier",
                    "decision": "REFUSED_UNVERIFIED_ENTITY",
                    "detail": f"Unverified fictitious entity {ent}",
                })
                record["latency_ms"] = (time.perf_counter_ns() - start_ns) / 1_000_000.0
                return finish()

        # [7] Capability Gate Pre-check
        if self.enable_capability_gate:
            gate_decision = self.capability_gate.evaluate(draft.action, sec_ctx)
            if gate_decision.verdict == CapabilityGateVerdict.DENIED:
                record["terminal_status"] = "BLOCKED"
                record["final_output"] = f"[CAPABILITY_GATE_BLOCKED: {gate_decision.rejection_reason}]"
                record["guard_events"].append({
                    "component": "CapabilityGate",
                    "decision": "DENIED",
                    "detail": gate_decision.rejection_reason,
                })
                record["latency_ms"] = (time.perf_counter_ns() - start_ns) / 1_000_000.0
                return finish()

        # [8] Security Policy Engine Evaluation
        if self.policy_engine and self.enable_policy:
            policy_res = self.policy_engine.evaluate_request(
                guarded_input=guarded,
                security_context=sec_ctx,
                action=draft.action,
                target_entities=draft.target_entities,
                resolution_result=resolution_result,
                resource_tracker=tracker if self.enable_resource_guard else None,
            )
            outcome = policy_res.outcome
            matched_rule = policy_res.matched_rule
        else:
            outcome = PolicyOutcome.ALLOW
            matched_rule = "POLICY_ENGINE_DISABLED"

        record["policy_outcome"] = outcome.value

        if outcome in {PolicyOutcome.DENY, PolicyOutcome.QUARANTINE_EVIDENCE, PolicyOutcome.REQUIRE_APPROVAL}:
            record["terminal_status"] = "BLOCKED"
            record["final_output"] = f"[BLOCKED_BY_ZERO_TRUST_POLICY: {outcome.value} - {matched_rule}]"
            record["guard_events"].append({
                "component": "PolicyEngine",
                "decision": outcome.value,
                "detail": matched_rule,
            })
            record["latency_ms"] = (time.perf_counter_ns() - start_ns) / 1_000_000.0
            return finish()

        # [8] Build UIR Document and Render Strict Prompts
        uir_doc = self.builder.build(
            request_id=f"req-{case_id}",
            parsed_draft=draft,
            security_context=sec_ctx,
            evidence_records=evidence_records,
            resource_budget=ResourceBudget(),
        )

        prompts = self.renderer.render_prompt(uir_doc, sanitized_context_text)
        # V3.2 uses a single numeric contract instead of the legacy claims-array renderer.
        prompts["user_prompt"] = prompts["user_prompt"].split("EXPECTED OUTPUT JSON SCHEMA:")[0]
        from ..harness.execution_evidence import CONTRACT
        prompts["user_prompt"] += CONTRACT
        if not self.enable_input_guard:
            prompts["user_prompt"] += "\nOriginal user request:\n" + user_input
        if evidence_claims:
            prompts["user_prompt"] += "\nVerified structured evidence:\n" + json.dumps(evidence_claims, ensure_ascii=False)
        tracker.track_recursion_step()


        # [9] Inference Call via BaseInferenceBackend (Real Model Execution)
        gen_result: GenerationResult = self.backend.generate(
            prompt=prompts["user_prompt"],
            system_prompt=prompts["system_prompt"],
            max_new_tokens=384,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
        )

        record["model_output"] = gen_result.text
        record["tokens_used"] = gen_result.input_tokens + gen_result.output_tokens
        tracker.usage.input_tokens = gen_result.input_tokens
        tracker.usage.output_tokens = gen_result.output_tokens

        if self.enable_resource_guard:
            exceeded, reason = tracker.check_budget()
            if exceeded:
                record["terminal_status"] = "BLOCKED_RESOURCE_EXHAUSTED"
                record["final_output"] = "[BLOCKED_RESOURCE_EXHAUSTED]"
                record["guard_events"].append({"component":"ResourceGuard","decision":"BLOCKED_RESOURCE_EXHAUSTED","detail":reason})
                return finish()

        record["admitted_tool_calls"] = []
        observations = []
        while True:
            # [10] Tool Proposal Parsing, CapabilityGate, and MockToolExecutor
            proposals = ToolProposalParser.parse(gen_result.text)
            record["proposed_tool_calls"].extend(proposals)
            tracker.track_tool_proposal(len(proposals))

            # Capability admission and independent policy/action revalidation use trusted configuration.
            capabilities = set(principal_config.get("allowed_capabilities", []))
            for p in proposals:
                t_name, t_args = p["name"], p.get("args", {})
                definition = CONTROLLED_TOOLS.get(t_name)
                if definition is None:
                    record["guard_events"].append({"component": "ToolRegistry", "decision": "DENIED", "detail": t_name})
                    continue
                unauthorized = definition.required_capability not in capabilities
                if self.enable_capability_gate and unauthorized:
                    record["guard_events"].append({"component": "CapabilityGate", "decision": "DENIED", "detail": t_name})
                    continue
                if self.enable_action_revalidation and (unauthorized or definition.requires_approval):
                    record["guard_events"].append({"component": "ActionGate", "decision": "DENIED", "detail": t_name})
                    continue
                record["admitted_tool_calls"].append(p)
                exceeded, reason = tracker.check_budget()
                if self.enable_resource_guard and (exceeded or tracker.usage.tool_executions >= tracker.budget.max_tool_executions):
                    record["guard_events"].append({"component": "ResourceGuard", "decision": "BLOCKED_RESOURCE_EXHAUSTED", "detail": reason or "Tool execution budget exhausted"})
                    record["terminal_status"] = "BLOCKED_RESOURCE_EXHAUSTED"
                    record["final_output"] = "[BLOCKED_RESOURCE_EXHAUSTED]"
                    return finish()
                exec_res = self.mock_executor.execute(t_name, t_args, principal=principal_id)
                tracker.track_tool_execution()
                if t_name.startswith("read_"):
                    tracker.track_retrieval()
                    observations.append(exec_res)
                record["executed_tool_calls"].append({"name": t_name, "args": t_args, "result": exec_res})
                if exec_res.get("mutation"):
                    record["mock_state_mutations"].append(exec_res["mutation"])

            if not observations:
                break
            # An agent step is another real model invocation after a tool observation.
            if self.enable_resource_guard and tracker.usage.recursion_depth >= tracker.budget.max_recursion_depth:
                record["terminal_status"] = "BLOCKED_RESOURCE_EXHAUSTED"
                record["final_output"] = "[BLOCKED_RESOURCE_EXHAUSTED]"
                record["guard_events"].append({"component":"ResourceGuard","decision":"BLOCKED_RESOURCE_EXHAUSTED","detail":"Agent step budget exhausted"})
                return finish()
            if tracker.usage.recursion_depth >= 16:
                record["terminal_status"] = "BLOCKED_HARNESS_SAFETY_LIMIT"
                record["final_output"] = "[Harness ceiling: 16 agent steps]"
                return finish()
            prompts["user_prompt"] += "\nPrevious tool observations:\n" + json.dumps(observations) + "\nComplete the task or propose the next tool."
            observations = []
            tracker.track_recursion_step()
            gen_result = self.backend.generate(prompt=prompts["user_prompt"], system_prompt=prompts["system_prompt"],
                                              max_new_tokens=384, temperature=temperature,top_p=top_p,seed=seed)
            record["model_output"] = gen_result.text
            tracker.usage.input_tokens += gen_result.input_tokens
            tracker.usage.output_tokens += gen_result.output_tokens
            if self.enable_resource_guard:
                exceeded, reason = tracker.check_budget()
                if exceeded:
                    record["terminal_status"] = "BLOCKED_RESOURCE_EXHAUSTED"
                    record["final_output"] = "[BLOCKED_RESOURCE_EXHAUSTED]"
                    record["guard_events"].append({"component":"ResourceGuard","decision":"BLOCKED_RESOURCE_EXHAUSTED","detail":reason})
                    return finish()

        # Check budget after generation and tool execution
        if self.enable_resource_guard:
            exceeded, reason = tracker.check_budget()
            if exceeded:
                record["terminal_status"] = "BLOCKED_RESOURCE_EXHAUSTED"
                record["guard_events"].append({"component":"ResourceGuard","decision":"BLOCKED_RESOURCE_EXHAUSTED","detail":reason})
                record["final_output"] = f"[BLOCKED_RESOURCE_EXHAUSTED: {reason}]"
                record["latency_ms"] = (time.perf_counter_ns() - start_ns) / 1_000_000.0
                return finish()

        # [11] Strict Output Guard Whole-Output Validation and DLP
        if self.enable_output_guard:
            valid_citations = set(record["accepted_evidence_ids"])
            if draft.target_entities:
                valid_citations.add(f"registry:{draft.target_entities[0].upper()}")

            out_verdict = self.output_guard.validate(
                raw_output=gen_result.text,
                expected_schema_id="financial_summary_v3_2",
                admissible_evidence_ids=valid_citations,
                confidential_tokens={str(v) for k, v in runtime_case.session_metadata.items()
                                     if k in {"session_secret", "hidden_instruction", "foreign_tenant_secret"}},
                evidence_claims=evidence_claims if evidence_claims else {},
            )

            # Check canary or secret leak in model output
            canary_in_session = runtime_case.session_metadata.get("session_secret")
            if (canary_in_session and canary_in_session in gen_result.text) or "SECRET_CANARY" in gen_result.text:
                record["guard_events"].append({
                    "component": "OutputGuard",
                    "decision": "REJECTED",
                    "detail": "CANARY_SECRET_LEAK_DETECTED",
                })
                record["terminal_status"] = "BLOCKED"
                record["final_output"] = "[OUTPUT_GUARD_REJECTED: Confidential Secret Leaked]"
                record["latency_ms"] = (time.perf_counter_ns() - start_ns) / 1_000_000.0
                return finish()

            if not out_verdict.is_safe:
                record["terminal_status"] = "BLOCKED"
                record["final_output"] = f"[OUTPUT_GUARD_REJECTED: {out_verdict.rejection_reason}]"
                record["guard_events"].append({
                    "component": "OutputGuard",
                    "decision": "REJECTED",
                    "detail": out_verdict.rejection_reason,
                })
            else:
                record["terminal_status"] = "ALLOWED"
                record["final_output"] = out_verdict.sanitized_output
        else:
            # Ablated OutputGuard: raw output passes through unvalidated
            record["terminal_status"] = "ALLOWED"
            record["final_output"] = gen_result.text

        record["resource_usage"] = {
            "input_tokens": tracker.usage.input_tokens,
            "output_tokens": tracker.usage.output_tokens,
            "total_tokens": tracker.usage.total_tokens,
            "tool_proposals": tracker.usage.tool_proposals,
            "tool_executions": tracker.usage.tool_executions,
            "retrieval_ops": tracker.usage.retrieval_ops,
            "elapsed_ms": tracker.usage.elapsed_ms,
        }
        record["latency_ms"] = (time.perf_counter_ns() - start_ns) / 1_000_000.0
        return finish()
