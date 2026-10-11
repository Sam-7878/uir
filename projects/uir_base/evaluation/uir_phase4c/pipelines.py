"""Publication-safe C0-C8 request builders and deterministic enforcement transitions."""
from __future__ import annotations

import ast
import json
import operator
import re
from typing import Any

from evaluation.uir_phase4c.common import sha256_text

CLAIM_SCHEMA = '{"answer":"brief text","claims":[{"claim_type":"numeric_claim","entity_id":"ID","attribute":"metric","value":"exact source text","unit":"unit","period":"period","provenance":"source"}]}'
FACT_REF_SCHEMA = '{"answer":"brief non-numeric text","fact_refs":["fact_001"]}'
REFUSAL = "REJECTED: no policy-permitted verified answer."


def extract_json(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    candidates = [stripped]
    start, end = stripped.find("{"), stripped.rfind("}")
    if 0 <= start < end:
        candidates.append(stripped[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
            if isinstance(value, dict):
                return value
        except (ValueError, TypeError):
            continue
    return None


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
    common = {"invoke": True, "policy_decision": "UNCHECKED", "retrieved_context_ids": [], "verified_fact_ids": [], "system": "", "prompt": ""}
    if pipeline == "C0_DIRECT_SLM":
        return common | {"system": "Answer from internal model knowledge only.", "prompt": _claims_prompt(case, None, "No external evidence is available.")}
    if pipeline == "C1_NAIVE_RAG":
        retrieved = facts[:3]
        return common | {"system": "Use retrieved text where helpful.", "prompt": _claims_prompt(case, retrieved, "Naive retrieval may be incomplete."), "retrieved_context_ids": context_ids(case)[:3]}
    if pipeline == "C2_RAG_EXISTENCE_CHECK":
        if not case["runtime_entity_exists"]:
            return common | {"invoke": False, "policy_decision": "ENTITY_REJECT", "final_output": "REJECTED: entity absent from authoritative registry."}
        return common | {"system": "The requested entity passed an authoritative existence check. Use retrieved evidence only.", "prompt": _claims_prompt(case, facts[:3], "Entity existence was verified."), "policy_decision": "ENTITY_PERMIT", "retrieved_context_ids": context_ids(case)[:3]}
    if pipeline == "C3_JSON_SCHEMA_STRUCTURED":
        return common | {"system": "Produce JSON only; output is rejected unless it validates against the declared schema.", "prompt": _claims_prompt(case, facts[:3], "JSON-schema validation is mandatory."), "policy_decision": "SCHEMA_REQUIRED", "retrieved_context_ids": context_ids(case)[:3]}
    if pipeline == "C5_GUARDRAIL_STYLE":
        if not case["runtime_policy_permit"] or _input_rail_blocks(case["input"]):
            return common | {"invoke": False, "policy_decision": "PRE_RAIL_REJECT", "final_output": "REJECTED: guardrail input policy violation."}
        return common | {"system": "Safety rail: answer only from supplied context and emit strict JSON.", "prompt": _claims_prompt(case, facts[:3], "Requests outside supplied evidence must be refused."), "policy_decision": "PRE_RAIL_PERMIT", "retrieved_context_ids": context_ids(case)[:3]}
    if pipeline == "C6_CORRECTIVE_RETRIEVAL":
        if not facts:
            return common | {"invoke": False, "policy_decision": "RETRIEVAL_REJECT", "final_output": "REJECTED: corrective retrieval found no relevant evidence."}
        return common | {"system": "Corrective retrieval retained only evidence matching the requested entity, metric, and period.", "prompt": _claims_prompt(case, facts, "The supplied evidence passed a relevance correction step."), "policy_decision": "RETRIEVAL_CORRECTED", "retrieved_context_ids": context_ids(case)}
    if pipeline == "C7_GRAPH_STRUCTURED_RAG":
        graph = [{"subject": claim.get("entity_id"), "predicate": claim.get("attribute"), "object": claim.get("value"), "source": claim.get("provenance")} for claim in facts]
        return common | {"system": "Answer from the supplied graph-structured evidence.", "prompt": _claims_prompt(case, graph, "Each graph edge is source-bound."), "policy_decision": "GRAPH_RETRIEVED", "retrieved_context_ids": context_ids(case)}
    if pipeline == "C8_FINAL_UIR_B6":
        if not (case["runtime_entity_exists"] and case["runtime_policy_permit"] and case["runtime_uir_compiles"] and facts):
            return common | {"invoke": False, "policy_decision": "UIR_FAIL_CLOSED", "final_output": REFUSAL}
        catalog = fact_catalog(case)
        descriptors = [{"fact_id": key, "claim_type": value.get("claim_type"), "entity_id": value.get("entity_id"), "attribute": value.get("attribute"), "period": value.get("period")} for key, value in catalog.items()]
        prompt = f"USER_REQUEST:\n{case['input']}\n\nVERIFIED_FACT_REFERENCES:\n{json.dumps(descriptors, ensure_ascii=False, sort_keys=True)}\n\nSelect every relevant fact. Return only JSON matching {FACT_REF_SCHEMA}. The answer text must contain no numbers, units, URLs, or hashes."
        return common | {"system": "UIR policy permits only selection of immutable verified fact references.", "prompt": prompt, "policy_decision": "UIR_PERMIT", "retrieved_context_ids": context_ids(case), "verified_fact_ids": list(catalog)}
    raise ValueError(f"unsupported internal pipeline: {pipeline}")


def _input_rail_blocks(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("ignore previous", "bypass", "override policy", "무시하고", "강제 승인", "보안 무시"))


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
    produced = {"name": str(name), "arguments": arguments, "model_produced": True, "raw_request_sha256": sha256_text(raw_request)}
    if name not in {"lookup_entity", "get_verified_metric"}:
        return produced, {"status": "error", "reason": "unknown_or_unparseable_tool"}
    entity = str(arguments.get("entity_id", "")).upper()
    expected_entity = str(case.get("requested_entity", "")).upper()
    if not case["runtime_entity_exists"] or entity != expected_entity:
        return produced, {"status": "not_found", "entity_id": entity}
    facts = case.get("context_claims", [])
    if name == "get_verified_metric":
        attr, period = str(arguments.get("attribute", "")), str(arguments.get("period", ""))
        facts = [claim for claim in facts if claim.get("attribute") == attr and str(claim.get("period", "")) == period]
    return produced, {"status": "success" if facts else "not_found", "facts": facts}


def build_tool_final(case: dict[str, Any], request: dict[str, Any], result: dict[str, Any]) -> tuple[str, str]:
    prompt = f"USER_REQUEST:\n{case['input']}\n\nMODEL_TOOL_REQUEST:\n{json.dumps(request, ensure_ascii=False, sort_keys=True)}\n\nAUTHORITATIVE_TOOL_RESULT:\n{json.dumps(result, ensure_ascii=False, sort_keys=True)}\n\nReturn only JSON matching {CLAIM_SCHEMA}. If the tool failed, use an empty claims array and state that no verified answer is available."
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


def lexical_context(case: dict[str, Any], limit: int = 12) -> list[str]:
    question_tokens = set(re.findall(r"[a-z0-9%$.-]+", case["question"].lower()))
    candidates: list[tuple[int, int, str]] = []
    order = 0
    for text in case.get("pre_text", []) + case.get("post_text", []):
        tokens = set(re.findall(r"[a-z0-9%$.-]+", text.lower()))
        candidates.append((len(question_tokens & tokens), order, text)); order += 1
    for row in case.get("table", []):
        text = " | ".join(str(cell) for cell in row)
        tokens = set(re.findall(r"[a-z0-9%$.-]+", text.lower()))
        candidates.append((len(question_tokens & tokens) + 1, order, text)); order += 1
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return [text for _, _, text in candidates[:limit]]


def parse_final_answer(text: str) -> str:
    match = re.search(r"FINAL_ANSWER\s*:\s*([^\n]+)", text, re.I)
    return match.group(1).strip() if match else text.strip().splitlines()[-1].strip() if text.strip() else ""


def parse_yes_no(text: str) -> str:
    tokens = re.findall(r"\b(yes|no)\b", text.lower())
    return tokens[0].title() if tokens and all(token == tokens[0] for token in tokens) else "INVALID"


_BIN_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}


def safe_calculate(expression: str, source_text: str) -> dict[str, Any]:
    if len(expression) > 200 or not re.fullmatch(r"[0-9.,%+*/()\s-]+", expression):
        return {"status": "error", "reason": "expression_not_allowed"}
    normalized = expression.replace(",", "").replace("%", "/100")
    source_numbers = {token.replace(",", "") for token in re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", source_text)}
    expression_numbers = set(re.findall(r"\d+(?:\.\d+)?", normalized))
    if not expression_numbers.issubset(source_numbers | {"100"}):
        return {"status": "error", "reason": "number_not_in_source"}
    try:
        value = _eval_ast(ast.parse(normalized, mode="eval").body)
        return {"status": "success", "value": value, "expression": expression}
    except (ValueError, ZeroDivisionError, OverflowError, SyntaxError):
        return {"status": "error", "reason": "calculation_failed"}


def _eval_ast(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_ast(node.operand)
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return float(_BIN_OPS[type(node.op)](_eval_ast(node.left), _eval_ast(node.right)))
    raise ValueError("unsupported expression")
