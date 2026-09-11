"""Matched LAW-200 pipeline transitions; this module never reads oracle data."""
from __future__ import annotations

import json
from typing import Any

from evaluation.uir_law.law200.common import sha256_text
from evaluation.uir_law.law200.legal_ir import (
    case_names_match,
    compile_legal_uir,
    extract_citation,
    registry_index,
    verify_entity,
)
from evaluation.uir_law.law200.model import OllamaModel
from evaluation.uir_law.law200.retrieval import retrieve

ANSWER_SCHEMA = (
    '{"decision":"ANSWER|REJECT|CLARIFY|CORRECT",'
    '"citation":"canonical citation or null","case_name":"case name or null",'
    '"answer":"brief metadata-only answer","evidence_ids":["source id"]}'
)
UIR_SELECTION_SCHEMA = '{"selected_evidence_ids":["one admissible source id"]}'
REJECTION = {
    "decision": "REJECT",
    "citation": None,
    "case_name": None,
    "answer": "The requested legal entity could not be authoritatively verified.",
    "evidence_ids": [],
}


def parse_object(text: str) -> dict[str, Any] | None:
    candidates = [text.strip()]
    start, end = text.find("{"), text.rfind("}")
    if 0 <= start < end:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict):
            return value
    return None


def answer_prompt(query: str, context: list[dict[str, Any]] | None, instruction: str) -> str:
    parts = [f"USER_QUERY:\n{query}"]
    if context is not None:
        parts.append("RETRIEVED_AUTHORITY_METADATA:\n" + json.dumps(context, ensure_ascii=False, sort_keys=True))
    parts.extend([
        instruction,
        "Do not invent holdings or facts. Report only identity metadata explicitly present in authority metadata.",
        f"Return one JSON object matching this schema exactly: {ANSWER_SCHEMA}",
    ])
    return "\n\n".join(parts)


def invoke(model: OllamaModel, prompt: str, system: str) -> dict[str, Any]:
    generated = model.generate(prompt, system)
    return {
        "prompt_sha256": sha256_text(prompt),
        "system_sha256": sha256_text(system),
        "prompt": prompt,
        "system": system,
        **generated,
    }


def exact_citation_context(citation: str | None, corpus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not citation:
        return []
    return [row for row in corpus if row.get("citation_canonical") == citation][:1]


def post_guard(raw: str, admissible: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    value = parse_object(raw)
    if not value or str(value.get("decision", "")).upper() not in {"ANSWER", "CORRECT"}:
        return REJECTION.copy(), "MODEL_REJECT_OR_INVALID_CONTRACT"
    citation = extract_citation(str(value.get("citation") or ""))
    name = str(value.get("case_name") or "")
    evidence_ids = value.get("evidence_ids")
    for source in admissible:
        if (
            citation == source.get("citation_canonical")
            and case_names_match(name, str(source.get("case_name", "")))
            and isinstance(evidence_ids, list)
            and str(source.get("source_id")) in evidence_ids
        ):
            return value, "OUTPUT_CONTRACT_PASS"
    return REJECTION.copy(), "OUTPUT_CONTRACT_REJECT"


def render_verified_selection(
    raw: str,
    admissible: list[dict[str, Any]],
    language_hint: str,
) -> tuple[dict[str, Any], str]:
    """Resolve a model-selected reference, then render facts from trusted metadata.

    The replaceable model is not allowed to restate citations, party/case names, or
    provenance.  It selects an immutable reference; the UIR runtime supplies all
    publishable fields from the already-bound authority record.
    """
    value = parse_object(raw)
    selected = value.get("selected_evidence_ids") if value else None
    if not isinstance(selected, list) or len(selected) != 1:
        return REJECTION.copy(), "MODEL_SELECTION_INVALID"
    selected_id = str(selected[0])
    source = next((row for row in admissible if str(row.get("source_id")) == selected_id), None)
    if source is None:
        return REJECTION.copy(), "MODEL_SELECTION_OUT_OF_SCOPE"
    citation = str(source["citation_canonical"])
    case_name = str(source["case_name"])
    court = str(source.get("court") or "")
    date_filed = str(source.get("date_filed") or "")
    if language_hint == "ko":
        answer = f"{court} 사건번호 {citation}는 {case_name} 사건이며 선고일은 {date_filed}이다."
    else:
        answer = f"The verified {court} case {citation} is {case_name}, decided on {date_filed}."
    return {
        "decision": "ANSWER",
        "citation": citation,
        "case_name": case_name,
        "answer": answer,
        "evidence_ids": [selected_id],
    }, "REFERENCE_SELECTION_PASS"


def uir_selection_prompt(query: str, context: list[dict[str, Any]]) -> str:
    candidates = [
        {
            "source_id": row.get("source_id"),
            "citation_canonical": row.get("citation_canonical"),
            "case_name": row.get("case_name"),
        }
        for row in context
    ]
    return "\n\n".join([
        f"USER_QUERY:\n{query}",
        "ADMISSIBLE_VERIFIED_REFERENCES:\n" + json.dumps(candidates, ensure_ascii=False, sort_keys=True),
        "Select the single verified reference that answers the query. Do not restate legal facts.",
        f"Return one JSON object matching this schema exactly: {UIR_SELECTION_SCHEMA}",
    ])


def run_pipeline(
    pipeline: str,
    case: dict[str, Any],
    registry: list[dict[str, Any]],
    corpus: list[dict[str, Any]],
    model: OllamaModel,
) -> dict[str, Any]:
    query = str(case["query"])
    citation = extract_citation(query)
    index = registry_index(registry)
    common: dict[str, Any] = {
        "case_id": case["case_id"],
        "pipeline": pipeline,
        "query": query,
        "model_invoked": False,
        "model_calls": [],
        "retrieved_source_ids": [],
        "runtime_citation": citation,
    }
    if pipeline == "C0_DIRECT":
        call = invoke(
            model,
            answer_prompt(query, None, "Answer using internal model knowledge only; no external evidence is available."),
            "You are a legal metadata assistant. Be explicit when a citation cannot be verified.",
        )
        return common | {"model_invoked": True, "model_calls": [call], "final_output": call["raw_response"], "transition": "DIRECT_GENERATION"}

    lexical = retrieve(query, corpus, limit=3)
    retrieved_ids = [str(item["source_id"]) for item in lexical]
    if pipeline == "C1_NAIVE_RAG":
        call = invoke(
            model,
            answer_prompt(query, lexical, "Use retrieved metadata when relevant. Retrieval may be noisy or incomplete."),
            "You are a retrieval-augmented legal metadata assistant.",
        )
        return common | {"model_invoked": True, "model_calls": [call], "retrieved_source_ids": retrieved_ids, "final_output": call["raw_response"], "transition": "NAIVE_RETRIEVAL_GENERATION"}

    if pipeline == "C2_EXISTENCE_CHECK":
        record = index.get(citation or "")
        if not record:
            return common | {"final_output": json.dumps(REJECTION), "transition": "PRE_MODEL_EXISTENCE_REJECT"}
        context = exact_citation_context(citation, corpus)
        call = invoke(
            model,
            answer_prompt(query, context, "The citation passed an existence lookup. Case-name binding was not checked."),
            "You are a legal metadata assistant using an existence-checked citation.",
        )
        return common | {"model_invoked": True, "model_calls": [call], "retrieved_source_ids": [record["source_id"]], "final_output": call["raw_response"], "transition": "EXISTENCE_PERMIT"}

    if pipeline == "C4_TOOL_AGENT":
        tool_prompt = (
            f"USER_QUERY:\n{query}\n\nDecide whether to use the authoritative lookup_citation tool. "
            'Return JSON only: {"name":"lookup_citation|none","arguments":{"citation":"..."}}'
        )
        first = invoke(model, tool_prompt, "You are a tool-calling legal assistant; you choose the tool and its arguments.")
        request = parse_object(first["raw_response"]) or {}
        selected = str(request.get("name", "none"))
        arguments = request.get("arguments") if isinstance(request.get("arguments"), dict) else {}
        tool_citation = extract_citation(str(arguments.get("citation", "")))
        record = index.get(tool_citation or "") if selected == "lookup_citation" else None
        tool_result = (
            {key: record.get(key) for key in ("source_id", "citation_canonical", "case_name", "court", "date_filed")}
            if record else {"status": "NOT_FOUND", "citation": tool_citation}
        )
        final_prompt = answer_prompt(query, [tool_result], "Use only the result of the tool call you chose. Reject when it did not verify an entity.")
        second = invoke(model, final_prompt, "You are a tool-using legal metadata assistant.")
        return common | {
            "model_invoked": True,
            "model_calls": [first, second],
            "retrieved_source_ids": [str(record["source_id"])] if record else [],
            "tool_request": request,
            "tool_result": tool_result,
            "final_output": second["raw_response"],
            "transition": "MODEL_SELECTED_TOOL",
        }

    if pipeline == "C5_GUARDRAIL":
        call = invoke(
            model,
            answer_prompt(query, lexical, "Safety rail: answer only from retrieved metadata and cite its exact source ID."),
            "You are a guarded retrieval assistant. Your output is checked after generation.",
        )
        guarded, transition = post_guard(call["raw_response"], lexical)
        return common | {
            "model_invoked": True,
            "model_calls": [call],
            "retrieved_source_ids": retrieved_ids,
            "pre_guard_output": call["raw_response"],
            "final_output": json.dumps(guarded, ensure_ascii=False, sort_keys=True),
            "transition": transition,
        }

    if pipeline == "C8_UIR":
        uir = compile_legal_uir(query)
        binding = verify_entity(uir, registry)
        uir_fields = uir.to_dict()
        if binding.status != "VERIFIED":
            rejection = REJECTION | {
                "citation": uir.citation,
                "answer": f"Safe rejection before generation: {binding.reason}.",
            }
            return common | {
                "uir": uir_fields,
                "binding": binding.to_dict(),
                "final_output": json.dumps(rejection, ensure_ascii=False, sort_keys=True),
                "transition": "UIR_PRE_MODEL_REJECT",
            }
        context = exact_citation_context(uir.citation, corpus)
        call = invoke(
            model,
            uir_selection_prompt(query, context),
            "You select one immutable evidence reference behind a typed UIR legal-entity contract.",
        )
        guarded, transition = render_verified_selection(call["raw_response"], context, uir.language_hint)
        return common | {
            "model_invoked": True,
            "model_calls": [call],
            "retrieved_source_ids": [str(binding.source_id)],
            "uir": uir_fields,
            "binding": binding.to_dict(),
            "pre_guard_output": call["raw_response"],
            "final_output": json.dumps(guarded, ensure_ascii=False, sort_keys=True),
            "transition": f"UIR_{transition}",
        }
    raise ValueError(f"unsupported pipeline: {pipeline}")
