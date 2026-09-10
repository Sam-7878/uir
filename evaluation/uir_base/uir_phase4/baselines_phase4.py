#!/usr/bin/env python3
"""Phase UIR-4 Strong Baseline Suite (C0 to C8)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_DIR = ROOT / "evaluation/uir_external"
sys.path.insert(0, str(EXTERNAL_DIR))
from registry_adapter import FrozenRegistry, RegistryFact

PIPELINES_PHASE4 = [
    "C0_DIRECT_SLM",
    "C1_NAIVE_RAG",
    "C2_RAG_EXISTENCE_CHECK",
    "C3_JSON_SCHEMA_CONSTRAINED",
    "C4_TOOL_CALLING_AGENT",
    "C5_GUARDRAIL_PIPELINE",
    "C6_ADVANCED_RAG",
    "C7_GRAPHRAG",
    "C8_FINAL_UIR_B6",
]

SCHEMA = '{"answer":"brief text","claims":[{"claim_type":"entity_claim|attribute_claim|numeric_claim|relation_claim|temporal_claim|provenance_claim","entity_id":"exact id","attribute":"exact attribute","value":"exact source text","unit":"exact unit or empty","period":"exact period or empty","provenance":"exact source_id or empty"}]}'
CLAIM_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["answer", "claims"],
    "properties": {
        "answer": {"type": "string"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["claim_type", "entity_id", "attribute", "value", "unit", "period", "provenance"],
                "properties": {field: {"type": "string"} for field in ("claim_type", "entity_id", "attribute", "value", "unit", "period", "provenance")},
            },
        },
    },
}

FACT_REF_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["answer", "fact_refs"],
    "properties": {
        "answer": {"type": "string"},
        "fact_refs": {
            "type": "array",
            "items": {"type": "string", "pattern": "^fact_[0-9]{3}$"},
            "uniqueItems": True,
        },
    },
}


@dataclass
class BaselineRequest:
    pipeline: str
    invoke_renderer: bool
    system: str
    prompt: str
    verified_claims: list[dict]
    rejection_reason: str | None = None
    output_mode: str = "claims"
    fact_catalog: dict[str, dict] | None = None
    response_schema: dict | None = None


def format_common_prompt(user_input: str, context: str = "") -> str:
    parts = [f"USER_REQUEST:\n{user_input}"]
    if context:
        parts.append(f"CONTEXT:\n{context}")
    parts.append(
        f"Return only JSON matching this schema:\n{SCHEMA}\n"
        "Use an empty claims array when no factual claim can be supported. "
        "Preserve numeric text, sign, unit, period, and provenance exactly."
    )
    return "\n\n".join(parts)


def format_fact_reference_prompt(user_input: str, facts: list[dict]) -> tuple[str, dict[str, dict]]:
    catalog = {f"fact_{index:03d}": claim for index, claim in enumerate(facts, 1)}
    descriptors = [
        {
            "fact_id": fact_id,
            "claim_type": claim.get("claim_type"),
            "entity_id": claim.get("entity_id"),
            "attribute": claim.get("attribute"),
            "period": claim.get("period"),
        }
        for fact_id, claim in catalog.items()
    ]
    prompt = (
        f"USER_REQUEST:\n{user_input}\n\n"
        f"VERIFIED_FACT_REFERENCES:\n{json.dumps(descriptors, ensure_ascii=False, sort_keys=True)}\n\n"
        "Return only JSON with a brief answer that contains no numeric values, units, provenance strings, or hashes, "
        "and a fact_refs array selecting every relevant verified fact ID. Do not invent fact IDs."
    )
    return prompt, catalog


def get_verified_claims(case: dict, registry: FrozenRegistry) -> list[dict]:
    if case.get("context_claims"):
        return case["context_claims"]
    semantics = case.get("expected_semantics") or {}
    entity = semantics.get("target")
    attribute = semantics.get("metric")
    period = semantics.get("period")
    fact = registry.lookup(entity, attribute, period) if entity and attribute and period else None
    return fact.claims() if fact else []


def check_guardrails_input(user_input: str) -> bool:
    """Simulates input guardrails (NeMo style) for injection/adversarial phrases."""
    adversarial_triggers = [
        "ignore previous instructions",
        "bypass security",
        "override policy",
        "system prompt reveal",
        "무시하고",
        "보안 무시",
        "강제 승인",
    ]
    lowered = user_input.lower()
    return any(trig in lowered for trig in adversarial_triggers)


def build_phase4_request(
    pipeline: str,
    case: dict,
    registry: FrozenRegistry,
    uir_record: dict | None = None,
) -> BaselineRequest:
    user_input = case["input"]
    facts = get_verified_claims(case, registry)
    target_entity = case.get("expected_target") or (case.get("expected_semantics") or {}).get("target", "")

    # C0: Direct SLM
    if pipeline == "C0_DIRECT_SLM":
        return BaselineRequest(
            pipeline=pipeline,
            invoke_renderer=True,
            system="Answer the user request using your internal knowledge.",
            prompt=format_common_prompt(user_input),
            verified_claims=[],
            response_schema=CLAIM_RESPONSE_SCHEMA,
        )

    # C1: Naive RAG
    if pipeline == "C1_NAIVE_RAG":
        retrieved = case.get("context_claims") or [fact.claim() for fact in registry.naive_retrieve(user_input)]
        return BaselineRequest(
            pipeline=pipeline,
            invoke_renderer=True,
            system="Answer using the retrieved context where useful.",
            prompt=format_common_prompt(user_input, json.dumps(retrieved, ensure_ascii=False, sort_keys=True)),
            verified_claims=retrieved,
            response_schema=CLAIM_RESPONSE_SCHEMA,
        )

    # C2: Critical Existence-Check Baseline
    # Rejects immediately if target entity does not exist in authoritative registry.
    # Otherwise proceeds with standard RAG.
    if pipeline == "C2_RAG_EXISTENCE_CHECK":
        entity_exists = registry.entity_exists(target_entity) if target_entity else case.get("entity_valid", False)
        if not entity_exists:
            return BaselineRequest(
                pipeline=pipeline,
                invoke_renderer=False,
                system="",
                prompt="",
                verified_claims=[],
                rejection_reason="ENTITY_UNVERIFIED",
            )
        retrieved = case.get("context_claims") or [fact.claim() for fact in registry.naive_retrieve(user_input)]
        return BaselineRequest(
            pipeline=pipeline,
            invoke_renderer=True,
            system="Answer using the retrieved context for the verified entity.",
            prompt=format_common_prompt(user_input, json.dumps(retrieved, ensure_ascii=False, sort_keys=True)),
            verified_claims=retrieved,
            response_schema=CLAIM_RESPONSE_SCHEMA,
        )

    # C3: JSON-Schema Constrained Output Generation
    if pipeline == "C3_JSON_SCHEMA_CONSTRAINED":
        retrieved = case.get("context_claims") or [fact.claim() for fact in registry.naive_retrieve(user_input)]
        return BaselineRequest(
            pipeline=pipeline,
            invoke_renderer=True,
            system="You are constrained by JSON schema. Every claim must have explicit fields.",
            prompt=format_common_prompt(user_input, json.dumps(retrieved, ensure_ascii=False, sort_keys=True)),
            verified_claims=retrieved,
            response_schema=CLAIM_RESPONSE_SCHEMA,
        )

    # C4: Tool / Function-Calling Agent
    if pipeline == "C4_TOOL_CALLING_AGENT":
        entity_exists = registry.entity_exists(target_entity) if target_entity else case.get("entity_valid", False)
        if not entity_exists:
            return BaselineRequest(
                pipeline=pipeline,
                invoke_renderer=False,
                system="",
                prompt="",
                verified_claims=[],
                rejection_reason="TOOL_ENTITY_NOT_FOUND",
            )
        tool_facts = facts if facts else [fact.claim() for fact in registry.facts_for_entity(target_entity)]
        tool_context = {
            "tool_call": "lookup_financial_data",
            "status": "success",
            "returned_facts": tool_facts,
        }
        return BaselineRequest(
            pipeline=pipeline,
            invoke_renderer=True,
            system="You are an autonomous agent with authoritative tool access. Base your answers strictly on tool outputs.",
            prompt=format_common_prompt(user_input, json.dumps(tool_context, ensure_ascii=False, sort_keys=True)),
            verified_claims=tool_facts,
            response_schema=CLAIM_RESPONSE_SCHEMA,
        )

    # C5: Guardrail-Based Pipeline (NeMo Style)
    if pipeline == "C5_GUARDRAIL_PIPELINE":
        if check_guardrails_input(user_input) or not case.get("policy_valid", True):
            return BaselineRequest(
                pipeline=pipeline,
                invoke_renderer=False,
                system="",
                prompt="",
                verified_claims=[],
                rejection_reason="GUARDRAIL_INPUT_VIOLATION",
            )
        retrieved = case.get("context_claims") or [fact.claim() for fact in registry.naive_retrieve(user_input)]
        return BaselineRequest(
            pipeline=pipeline,
            invoke_renderer=True,
            system="Safety rails enabled: Do not answer out-of-domain queries or unverified claims.",
            prompt=format_common_prompt(user_input, json.dumps(retrieved, ensure_ascii=False, sort_keys=True)),
            verified_claims=retrieved,
            response_schema=CLAIM_RESPONSE_SCHEMA,
        )

    # C6: Advanced Retrieval (Self-RAG / Corrective RAG)
    if pipeline == "C6_ADVANCED_RAG":
        retrieved = facts if facts else [fact.claim() for fact in registry.naive_retrieve(user_input)]
        crag_context = {
            "retrieval_eval": "correct",
            "filtered_documents": retrieved,
        }
        return BaselineRequest(
            pipeline=pipeline,
            invoke_renderer=True,
            system="Corrective RAG: Verified relevance filter applied to context.",
            prompt=format_common_prompt(user_input, json.dumps(crag_context, ensure_ascii=False, sort_keys=True)),
            verified_claims=retrieved,
            response_schema=CLAIM_RESPONSE_SCHEMA,
        )

    # C7: GraphRAG / Structured Knowledge Retrieval
    if pipeline == "C7_GRAPHRAG":
        graph_nodes = []
        if target_entity:
            related_facts = registry.facts_for_entity(target_entity)
            for f in related_facts:
                graph_nodes.append({
                    "node": f.attribute,
                    "entity": f.entity_id,
                    "value": f.value,
                    "relation": "calculation_linkbase",
                })
        return BaselineRequest(
            pipeline=pipeline,
            invoke_renderer=True,
            system="GraphRAG: Use structured relational subgraph knowledge to ground your response.",
            prompt=format_common_prompt(user_input, json.dumps(graph_nodes, ensure_ascii=False, sort_keys=True)),
            verified_claims=facts,
            response_schema=CLAIM_RESPONSE_SCHEMA,
        )

    # C8: Final UIR B6 Pipeline
    if pipeline == "C8_FINAL_UIR_B6":
        core_permit = case.get("uir_ready", False) or (uir_record is not None and uir_record.get("actual_outcome") == "COMMIT")
        if not core_permit or not case.get("entity_valid", False) or not case.get("policy_valid", False):
            return BaselineRequest(
                pipeline=pipeline,
                invoke_renderer=False,
                system="",
                prompt="",
                verified_claims=[],
                rejection_reason=(uir_record or {}).get("reason_code") or "UIR_POLICY_REJECT",
            )
        system = "The UIR and policy authorize selection of immutable verified fact references only. Never reproduce numeric values, units, provenance URIs, or hashes."
        prompt, catalog = format_fact_reference_prompt(user_input, facts)
        return BaselineRequest(
            pipeline=pipeline,
            invoke_renderer=True,
            system=system,
            prompt=prompt,
            verified_claims=facts,
            output_mode="fact_refs",
            fact_catalog=catalog,
            response_schema=FACT_REF_RESPONSE_SCHEMA,
        )

    raise ValueError(f"Unknown Phase 4 pipeline: {pipeline}")
