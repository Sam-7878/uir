#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "uir_external"))
from registry_adapter import FrozenRegistry, fact_context

PIPELINES = ["B0_DIRECT_SLM", "B1_SLM_WITH_PROMPT_GUARD", "B2_NAIVE_RAG_SLM", "B3_RAG_WITH_ENTITY_VALIDATION", "B4_UIR_POLICY_SLM", "B5_FULL_UIR_OUTPUT_VALIDATION", "B6_UIR_FILTER_AND_RENDER"]
SCHEMA = '{"answer":"brief text","claims":[{"claim_type":"entity_claim|attribute_claim|numeric_claim|relation_claim|temporal_claim|provenance_claim","entity_id":"exact id","attribute":"exact attribute","value":"exact source text","unit":"exact unit or empty","period":"exact period or empty","provenance":"exact source_id or empty"}]}'
CLAIM_RESPONSE_SCHEMA = {"type":"object","additionalProperties":False,"required":["answer","claims"],"properties":{"answer":{"type":"string"},"claims":{"type":"array","items":{"type":"object","additionalProperties":False,"required":["claim_type","entity_id","attribute","value","unit","period","provenance"],"properties":{field:{"type":"string"} for field in ("claim_type","entity_id","attribute","value","unit","period","provenance")}}}}}
FACT_REF_RESPONSE_SCHEMA = {"type":"object","additionalProperties":False,"required":["answer","fact_refs"],"properties":{"answer":{"type":"string"},"fact_refs":{"type":"array","items":{"type":"string","pattern":"^fact_[0-9]{3}$"},"uniqueItems":True}}}


@dataclass
class PipelineRequest:
    invoke_renderer: bool
    system: str
    prompt: str
    verified_claims: list[dict]
    rejection_reason: str | None = None
    output_mode: str = "claims"
    fact_catalog: dict[str, dict] | None = None
    response_schema: dict | None = None


def common_prompt(user_input: str, context: str = "") -> str:
    parts = [f"USER_REQUEST:\n{user_input}"]
    if context: parts.append(f"CONTEXT:\n{context}")
    parts.append(f"Return only JSON matching this schema:\n{SCHEMA}\nUse an empty claims array when no factual claim can be supported. Preserve numeric text, sign, unit, period, and provenance exactly.")
    return "\n\n".join(parts)


def fact_reference_prompt(user_input: str, facts: list[dict]) -> tuple[str, dict[str, dict]]:
    catalog = {f"fact_{index:03d}": claim for index, claim in enumerate(facts, 1)}
    descriptors = [{"fact_id": fact_id, "claim_type": claim.get("claim_type"), "entity_id": claim.get("entity_id"),
                    "attribute": claim.get("attribute"), "period": claim.get("period")} for fact_id, claim in catalog.items()]
    prompt = f"USER_REQUEST:\n{user_input}\n\nVERIFIED_FACT_REFERENCES:\n{json.dumps(descriptors, ensure_ascii=False, sort_keys=True)}\n\nReturn only JSON with a brief answer that contains no numeric values, units, provenance strings, or hashes, and a fact_refs array selecting every relevant verified fact ID. Do not invent fact IDs."
    return prompt, catalog


def verified_claims(case: dict, registry: FrozenRegistry) -> list[dict]:
    if case.get("context_claims"): return case["context_claims"]
    semantics = case.get("expected_semantics") or {}; entity = semantics.get("target"); attribute = semantics.get("metric"); period = semantics.get("period")
    fact = registry.lookup(entity, attribute, period) if entity and attribute and period else None
    return fact.claims() if fact else []


def build_request(pipeline: str, case: dict, registry: FrozenRegistry, uir_record: dict | None) -> PipelineRequest:
    facts = verified_claims(case, registry); user_input = case["input"]
    if pipeline == "B0_DIRECT_SLM": return PipelineRequest(True, "Answer the user request.", common_prompt(user_input), [], response_schema=CLAIM_RESPONSE_SCHEMA)
    if pipeline == "B1_SLM_WITH_PROMPT_GUARD": return PipelineRequest(True, "Safety guard: do not invent entities, numbers, sources, or policy permissions. If uncertain, return no claims.", common_prompt(user_input), [], response_schema=CLAIM_RESPONSE_SCHEMA)
    if pipeline == "B2_NAIVE_RAG_SLM":
        retrieved = case.get("context_claims") or [fact.claim() for fact in registry.naive_retrieve(user_input)]
        return PipelineRequest(True, "Answer using retrieved context where useful.", common_prompt(user_input, json.dumps(retrieved, ensure_ascii=False, sort_keys=True)), retrieved, response_schema=CLAIM_RESPONSE_SCHEMA)
    if pipeline == "B3_RAG_WITH_ENTITY_VALIDATION":
        if not case.get("entity_valid", False): return PipelineRequest(False, "", "", [], "ENTITY_UNVERIFIED")
        return PipelineRequest(True, "Use only the exact-entity context. Do not add facts.", common_prompt(user_input, json.dumps(facts, ensure_ascii=False, sort_keys=True)), facts, response_schema=CLAIM_RESPONSE_SCHEMA)
    if pipeline in {"B4_UIR_POLICY_SLM", "B5_FULL_UIR_OUTPUT_VALIDATION", "B6_UIR_FILTER_AND_RENDER"}:
        core_permit = case.get("uir_ready", False) or (uir_record is not None and uir_record.get("actual_outcome") == "COMMIT")
        if not core_permit or not case.get("entity_valid", False) or not case.get("policy_valid", False): return PipelineRequest(False, "", "", [], (uir_record or {}).get("reason_code") or "UIR_POLICY_REJECT")
        system = "The UIR and policy authorize selection of immutable verified fact references only. Never reproduce numeric values, units, provenance URIs, or hashes."
        prompt, catalog = fact_reference_prompt(user_input, facts)
        return PipelineRequest(True, system, prompt, facts, output_mode="fact_refs", fact_catalog=catalog, response_schema=FACT_REF_RESPONSE_SCHEMA)
    raise ValueError(f"unknown pipeline: {pipeline}")
