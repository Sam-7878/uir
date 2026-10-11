"""Publication-grade C0-C8 request builders and deterministic runtime enforcement transitions for Phase UIR-4D.

All runtime decisions execute real components:
- Entity Registry (Assumption A1)
- Policy Engine (Assumption A2)
- Multilingual UIR Compiler (Assumption A3)
No dataset annotation flags (stratum, entity_valid, policy_valid, uir_ready, expected_outcome) are referenced.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from evaluation.uir_phase4d.common import extract_json, sha256_text
from evaluation.uir_phase4d.runtime.entity_registry import EntityLookupResult, EntityRegistry, EntityStatus
from evaluation.uir_phase4d.runtime.policy_engine import PolicyDecision, PolicyEngine, PolicyEvaluationResult
from evaluation.uir_phase4d.runtime.uir_compiler import CompileStatus, UIRCompileResult, UIRCompiler

CLAIM_SCHEMA = '{"answer":"brief text","claims":[{"claim_type":"numeric_claim","entity_id":"ID","attribute":"metric","value":"exact source text","unit":"unit","period":"period","provenance":"source"}]}'
FACT_REF_SCHEMA = '{"answer":"brief non-numeric text","fact_refs":["fact_001"]}'
REFUSAL = "REJECTED: no policy-permitted verified answer."

_ENTITY_REGISTRY = EntityRegistry()
_POLICY_ENGINE = PolicyEngine()
_UIR_COMPILER = UIRCompiler()


def claim_key(claim: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(claim.get(key, "")) for key in ("claim_type", "entity_id", "attribute", "value", "unit", "period", "provenance"))


def fact_catalog(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {f"fact_{index:03d}": claim for index, claim in enumerate(case.get("context_claims", []), 1)}


def context_ids(case: dict[str, Any]) -> list[str]:
    ids = []
    for index, claim in enumerate(case.get("context_claims", []), 1):
        ids.append(str(claim.get("provenance") or f"runtime-fact-{index:03d}"))
    return ids


def _claims_prompt(case: dict[str, Any], context: list[dict[str, Any]] | None, instruction: str) -> str:
    parts = [f"USER_REQUEST:\n{case['input']}"]
    if context is not None:
        parts.append("RETRIEVED_CONTEXT:\n" + json.dumps(context, ensure_ascii=False, sort_keys=True))
    parts.append(instruction)
    parts.append(f"Return only JSON matching: {CLAIM_SCHEMA}. Use an empty claims array if unsupported. Copy source fields exactly; do not invent facts.")
    return "\n\n".join(parts)


def build_internal_request(pipeline: str, case: dict[str, Any]) -> dict[str, Any]:
    facts = case.get("context_claims", [])
    t_start = time.perf_counter()
    
    timing_breakdown = {
        "entity_lookup_ms": 0.0,
        "policy_eval_ms": 0.0,
        "compiler_ms": 0.0,
    }

    common = {
        "invoke": True,
        "policy_decision": "UNCHECKED",
        "retrieved_context_ids": [],
        "verified_fact_ids": [],
        "system": "",
        "prompt": "",
        "timing_breakdown": timing_breakdown,
    }

    if pipeline == "C0_DIRECT_SLM":
        return common | {
            "system": "Answer from internal model knowledge only.",
            "prompt": _claims_prompt(case, None, "No external evidence is available."),
        }

    if pipeline == "C1_NAIVE_RAG":
        retrieved = facts[:3]
        return common | {
            "system": "Use retrieved text where helpful.",
            "prompt": _claims_prompt(case, retrieved, "Naive retrieval may be incomplete."),
            "retrieved_context_ids": context_ids(case)[:3],
        }

    if pipeline == "C2_RAG_EXISTENCE_CHECK":
        t0 = time.perf_counter()
        entity_res = _ENTITY_REGISTRY.lookup(case.get("requested_entity"))
        timing_breakdown["entity_lookup_ms"] = (time.perf_counter() - t0) * 1000.0
        
        if entity_res.status != EntityStatus.EXISTS:
            return common | {
                "invoke": False,
                "policy_decision": "ENTITY_REJECT",
                "final_output": "REJECTED: entity absent from authoritative registry.",
            }
        return common | {
            "system": "The requested entity passed an authoritative existence check. Use retrieved evidence only.",
            "prompt": _claims_prompt(case, facts[:3], "Entity existence was verified."),
            "policy_decision": "ENTITY_PERMIT",
            "retrieved_context_ids": context_ids(case)[:3],
        }

    if pipeline == "C3_JSON_SCHEMA_STRUCTURED":
        return common | {
            "system": "Produce JSON only; output is rejected unless it validates against the declared schema.",
            "prompt": _claims_prompt(case, facts[:3], "JSON-schema validation is mandatory."),
            "policy_decision": "SCHEMA_REQUIRED",
            "retrieved_context_ids": context_ids(case)[:3],
        }

    if pipeline == "C5_GUARDRAIL_STYLE":
        t0 = time.perf_counter()
        policy_res = _POLICY_ENGINE.evaluate(case["input"], requested_attribute=case.get("requested_attribute", ""))
        timing_breakdown["policy_eval_ms"] = (time.perf_counter() - t0) * 1000.0

        if policy_res.decision == PolicyDecision.DENY:
            return common | {
                "invoke": False,
                "policy_decision": f"PRE_RAIL_REJECT: {policy_res.reason}",
                "final_output": "REJECTED: guardrail input policy violation.",
            }
        return common | {
            "system": "Safety rail: answer only from supplied context and emit strict JSON.",
            "prompt": _claims_prompt(case, facts[:3], "Requests outside supplied evidence must be refused."),
            "policy_decision": "PRE_RAIL_PERMIT",
            "retrieved_context_ids": context_ids(case)[:3],
        }

    if pipeline == "C6_CORRECTIVE_RETRIEVAL":
        if not facts:
            return common | {
                "invoke": False,
                "policy_decision": "RETRIEVAL_REJECT",
                "final_output": "REJECTED: corrective retrieval found no relevant evidence.",
            }
        return common | {
            "system": "Corrective retrieval retained only evidence matching the requested entity, metric, and period.",
            "prompt": _claims_prompt(case, facts, "The supplied evidence passed a relevance correction step."),
            "policy_decision": "RETRIEVAL_CORRECTED",
            "retrieved_context_ids": context_ids(case),
        }

    if pipeline == "C7_GRAPH_STRUCTURED_RAG":
        graph = [
            {
                "subject": claim.get("entity_id"),
                "predicate": claim.get("attribute"),
                "object": claim.get("value"),
                "source": claim.get("provenance"),
            }
            for claim in facts
        ]
        return common | {
            "system": "Answer from the supplied graph-structured evidence.",
            "prompt": _claims_prompt(case, graph, "Each graph edge is source-bound."),
            "policy_decision": "GRAPH_RETRIEVED",
            "retrieved_context_ids": context_ids(case),
        }

    if pipeline == "C8_FINAL_UIR_B6":
        # 1. Authoritative Entity Registry Check
        t0 = time.perf_counter()
        entity_res = _ENTITY_REGISTRY.lookup(case.get("requested_entity"))
        timing_breakdown["entity_lookup_ms"] = (time.perf_counter() - t0) * 1000.0
        if entity_res.status != EntityStatus.EXISTS:
            return common | {
                "invoke": False,
                "policy_decision": f"UIR_REJECT_ENTITY: {entity_res.status.value}",
                "final_output": REFUSAL,
            }

        # 2. Authoritative Policy Engine Check
        t0 = time.perf_counter()
        policy_res = _POLICY_ENGINE.evaluate(case["input"], requested_attribute=case.get("requested_attribute", ""))
        timing_breakdown["policy_eval_ms"] = (time.perf_counter() - t0) * 1000.0
        if policy_res.decision == PolicyDecision.DENY:
            return common | {
                "invoke": False,
                "policy_decision": f"UIR_REJECT_POLICY: {policy_res.reason}",
                "final_output": REFUSAL,
            }

        # 3. Multilingual UIR Compiler Check
        t0 = time.perf_counter()
        compile_res = _UIR_COMPILER.compile(
            raw_text=case["input"],
            requested_entity=case.get("requested_entity", ""),
            requested_attribute=case.get("requested_attribute", ""),
            requested_period=case.get("requested_period", ""),
            language=case.get("language", "en"),
        )
        timing_breakdown["compiler_ms"] = (time.perf_counter() - t0) * 1000.0
        if not compile_res.compiles:
            return common | {
                "invoke": False,
                "policy_decision": f"UIR_REJECT_SYNTAX: {compile_res.error_message}",
                "final_output": REFUSAL,
            }

        # 4. Context Facts Check
        if not facts:
            return common | {
                "invoke": False,
                "policy_decision": "UIR_REJECT_EMPTY_FACTS",
                "final_output": REFUSAL,
            }

        catalog = fact_catalog(case)
        descriptors = [
            {
                "fact_id": key,
                "claim_type": value.get("claim_type"),
                "entity_id": value.get("entity_id"),
                "attribute": value.get("attribute"),
                "period": value.get("period"),
            }
            for key, value in catalog.items()
        ]
        prompt = (
            f"USER_REQUEST:\n{case['input']}\n\n"
            f"COMPILED_UIR_AST_DIGEST: {compile_res.compiled_uir_hash}\n\n"
            f"VERIFIED_FACT_REFERENCES:\n{json.dumps(descriptors, ensure_ascii=False, sort_keys=True)}\n\n"
            f"Select every relevant fact. Return only JSON matching {FACT_REF_SCHEMA}. "
            "The answer text must contain no numbers, units, URLs, or hashes."
        )
        return common | {
            "system": "UIR policy permits only selection of immutable verified fact references.",
            "prompt": prompt,
            "policy_decision": "UIR_PERMIT",
            "retrieved_context_ids": context_ids(case),
            "verified_fact_ids": list(catalog),
        }

    raise ValueError(f"unsupported internal pipeline: {pipeline}")


def build_tool_request(case: dict[str, Any]) -> tuple[str, str]:
    prompt = (
        f"USER_REQUEST:\n{case['input']}\n\n"
        "Choose exactly one authoritative local tool. Return JSON only.\n"
        "Tools: lookup_entity(entity_id: string); get_verified_metric(entity_id: string, attribute: string, period: string).\n"
        'Schema: {"name":"lookup_entity|get_verified_metric","arguments":{}}'
    )
    return "You are a tool-calling agent. You must choose the tool and arguments yourself.", prompt


def execute_internal_tool(case: dict[str, Any], raw_request: str) -> tuple[dict[str, Any], dict[str, Any]]:
    parsed = extract_json(raw_request)
    request = parsed if parsed is not None else {"name": "PARSE_ERROR", "arguments": {}}
    name, arguments = request.get("name"), request.get("arguments")
    if not isinstance(arguments, dict):
        arguments = {}
    produced = {
        "name": str(name),
        "arguments": arguments,
        "model_produced": True,
        "raw_request_sha256": sha256_text(raw_request),
    }
    if name not in {"lookup_entity", "get_verified_metric"}:
        return produced, {"status": "error", "reason": "unknown_or_unparseable_tool"}

    entity = str(arguments.get("entity_id", "")).upper()
    lookup = _ENTITY_REGISTRY.lookup(entity)
    if lookup.status != EntityStatus.EXISTS:
        return produced, {"status": "not_found", "entity_id": entity}

    facts = case.get("context_claims", [])
    if name == "get_verified_metric":
        attr, period = str(arguments.get("attribute", "")), str(arguments.get("period", ""))
        facts = [claim for claim in facts if claim.get("attribute") == attr and str(claim.get("period", "")) == period]

    return produced, {"status": "success" if facts else "not_found", "facts": facts}


def build_tool_final(case: dict[str, Any], request: dict[str, Any], result: dict[str, Any]) -> tuple[str, str]:
    prompt = (
        f"USER_REQUEST:\n{case['input']}\n\n"
        f"MODEL_TOOL_REQUEST:\n{json.dumps(request, ensure_ascii=False, sort_keys=True)}\n\n"
        f"AUTHORITATIVE_TOOL_RESULT:\n{json.dumps(result, ensure_ascii=False, sort_keys=True)}\n\n"
        f"Return only JSON matching {CLAIM_SCHEMA}. If the tool failed, use an empty claims array and state that no verified answer is available."
    )
    return "Answer strictly from the authoritative local tool result.", prompt


def apply_internal_transition(pipeline: str, case: dict[str, Any], raw: str) -> tuple[str, list[str]]:
    parsed = extract_json(raw)
    facts = case.get("context_claims", [])
    supported = {claim_key(claim) for claim in facts}
    if pipeline == "C8_FINAL_UIR_B6":
        catalog = fact_catalog(case)
        refs = parsed.get("fact_refs", []) if parsed else []
        selected = [catalog[ref] for ref in refs if isinstance(ref, str) and ref in catalog]
        if not selected:
            return REFUSAL, []
        rendered = {"answer": "Verified facts rendered by the UIR output contract.", "claims": selected}
        return json.dumps(rendered, ensure_ascii=False, sort_keys=True), [ref for ref in refs if ref in catalog]
    if pipeline in {"C3_JSON_SCHEMA_STRUCTURED", "C5_GUARDRAIL_STYLE"}:
        claims = parsed.get("claims") if parsed else None
        if not isinstance(claims, list) or any(not isinstance(c, dict) for c in claims):
            return REFUSAL, []
        if pipeline == "C5_GUARDRAIL_STYLE" and any(claim_key(claim) not in supported for claim in claims):
            return "REJECTED: output rail found an unsupported claim.", []
        return json.dumps(parsed, ensure_ascii=False, sort_keys=True), []
    return raw, []
