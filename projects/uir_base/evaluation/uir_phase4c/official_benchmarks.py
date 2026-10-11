"""Runtime-only adapters for official FinQA and HaluEval-QA inputs."""
from __future__ import annotations

import json
import re
from typing import Any

from evaluation.uir_phase4c.pipelines import extract_json, lexical_context, parse_final_answer, parse_yes_no, safe_calculate


def finqa_prompt(case: dict[str, Any], pipeline: str) -> tuple[str, str, list[str]]:
    context = lexical_context(case)
    context_text = "\n".join(f"E{i:02d}: {text}" for i, text in enumerate(context, 1))
    prefix = f"REPORT_ID: {case['source_original_id']}\nQUESTION: {case['question']}\nEVIDENCE:\n{context_text}"
    if pipeline == "C1_NAIVE_RAG":
        system = "Solve the financial question from retrieved report evidence."
    elif pipeline == "C2_RAG_EXISTENCE_CHECK":
        system = "The report ID passed an authoritative existence check. Solve only from its retrieved evidence."
    elif pipeline == "C8_FINAL_UIR_B6":
        system = "Produce a source-bound FinQA arithmetic program. Do not use numbers absent from evidence."
        prompt = prefix + '\nReturn JSON only: {"program":"add|subtract|multiply|divide|exp|greater(arg1, arg2), ..."}. Use #0 for prior results.'
        return system, prompt, [f"E{i:02d}" for i in range(1, len(context) + 1)]
    else:
        raise ValueError(pipeline)
    prompt = prefix + "\nCompute the answer. End with exactly FINAL_ANSWER: <value>."
    return system, prompt, [f"E{i:02d}" for i in range(1, len(context) + 1)]


def finqa_tool_request(case: dict[str, Any]) -> tuple[str, str, str]:
    context = lexical_context(case)
    source_text = "\n".join(context)
    prompt = f"QUESTION: {case['question']}\nEVIDENCE:\n{source_text}\nChoose the calculator tool and construct its arithmetic expression from evidence. Return JSON only: {{\"name\":\"calculate\",\"arguments\":{{\"expression\":\"...\"}}}}"
    return "You are a financial tool-calling agent. You select the tool and its arguments.", prompt, source_text


def execute_finqa_tool(raw: str, source_text: str) -> tuple[dict[str, Any], dict[str, Any]]:
    parsed = extract_json(raw) or {}
    arguments = parsed.get("arguments") if isinstance(parsed.get("arguments"), dict) else {}
    request = {"name": str(parsed.get("name", "PARSE_ERROR")), "arguments": arguments, "model_produced": True}
    if request["name"] != "calculate":
        return request, {"status": "error", "reason": "unknown_tool"}
    return request, safe_calculate(str(arguments.get("expression", "")), source_text)


def finqa_tool_final(case: dict[str, Any], request: dict[str, Any], result: dict[str, Any]) -> tuple[str, str]:
    prompt = f"QUESTION: {case['question']}\nMODEL_TOOL_REQUEST: {json.dumps(request, sort_keys=True)}\nAUTHORITATIVE_TOOL_RESULT: {json.dumps(result, sort_keys=True)}\nUse only the tool result. End with exactly FINAL_ANSWER: <value>. If the tool failed, write FINAL_ANSWER: INVALID."
    return "Return the final answer from the authoritative local calculator result.", prompt


def extract_program(text: str) -> str:
    parsed = extract_json(text)
    if parsed and isinstance(parsed.get("program"), str):
        return parsed["program"].strip()
    match = re.search(r"((?:add|subtract|multiply|divide|exp|greater|table[-_](?:sum|average|max|min))\([^\n]+\))", text, re.I)
    return match.group(1).strip() if match else ""


def execute_finqa_program(program: str, case: dict[str, Any]) -> dict[str, Any]:
    if not program or len(program) > 500:
        return {"status": "error", "reason": "missing_program"}
    steps = re.findall(r"(add|subtract|multiply|divide|exp|greater|table[-_](?:sum|average|max|min))\(([^()]*)\)", program, re.I)
    if not steps:
        return {"status": "error", "reason": "invalid_program"}
    all_source = "\n".join(case.get("pre_text", []) + case.get("post_text", []) + [" | ".join(map(str, row)) for row in case.get("table", [])])
    source_numbers = {token.replace(",", "") for token in re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", all_source)}
    table = {str(row[0]).strip().lower(): [str(value) for value in row[1:]] for row in case.get("table", []) if row}
    results: list[float | str] = []

    def value(token: str) -> float:
        token = token.strip()
        if token.startswith("#"):
            return float(results[int(token[1:])])
        normalized = token.replace(",", "")
        is_percent = normalized.endswith("%")
        normalized = normalized.rstrip("%")
        if normalized not in source_numbers and normalized not in {"100", "-1", "1"}:
            raise ValueError("program number absent from source")
        number = float(normalized)
        return number / 100.0 if is_percent else number

    try:
        for op, args_text in steps:
            args = [part.strip() for part in args_text.split(",")]
            op = op.lower().replace("-", "_")
            if op.startswith("table_"):
                row_name = args[0].strip("'\"").lower()
                values = []
                for raw in table[row_name]:
                    match = re.search(r"-?\d+(?:,\d{3})*(?:\.\d+)?", raw)
                    if match:
                        values.append(float(match.group().replace(",", "")))
                if not values:
                    raise ValueError("empty table row")
                result = {"table_sum": sum, "table_average": lambda x: sum(x) / len(x), "table_max": max, "table_min": min}[op](values)
            else:
                if len(args) != 2:
                    raise ValueError("binary arity")
                left, right = value(args[0]), value(args[1])
                if op == "add": result = left + right
                elif op == "subtract": result = left - right
                elif op == "multiply": result = left * right
                elif op == "divide": result = left / right
                elif op == "exp": result = left ** right
                elif op == "greater": result = "yes" if left > right else "no"
                else: raise ValueError("unknown op")
            results.append(result)
        final = results[-1]
        if isinstance(final, float):
            final = round(final, 5)
        return {"status": "success", "value": final, "program": program}
    except (ValueError, KeyError, IndexError, ZeroDivisionError, OverflowError):
        return {"status": "error", "reason": "program_validation_or_execution_failed", "program": program}


def halueval_prompt(case: dict[str, Any], pipeline: str) -> tuple[str, str, list[str]]:
    context = case["knowledge"] if pipeline != "C1_NAIVE_RAG" else case["knowledge"]
    system = "Determine whether the candidate answer contains hallucinated or non-factual information. Reply only Yes or No."
    if pipeline == "C2_RAG_EXISTENCE_CHECK":
        system += " The official knowledge record passed an existence check."
    prompt = f"KNOWLEDGE:\n{context}\n\nQUESTION:\n{case['question']}\n\nCANDIDATE_ANSWER:\n{case['candidate_answer']}\n\nDoes the candidate answer contain hallucinated information? Reply only Yes or No."
    return system, prompt, ["official_knowledge"]


def halueval_tool_request(case: dict[str, Any]) -> tuple[str, str]:
    prompt = f"QUESTION: {case['question']}\nCANDIDATE_ANSWER: {case['candidate_answer']}\nChoose the authoritative verifier. Return JSON only: {{\"name\":\"verify_candidate\",\"arguments\":{{\"question\":\"...\",\"candidate_answer\":\"...\"}}}}"
    return "You are a tool-calling hallucination judge and must choose the verifier and arguments.", prompt


def execute_halueval_tool(case: dict[str, Any], raw: str) -> tuple[dict[str, Any], dict[str, Any]]:
    parsed = extract_json(raw) or {}
    arguments = parsed.get("arguments") if isinstance(parsed.get("arguments"), dict) else {}
    request = {"name": str(parsed.get("name", "PARSE_ERROR")), "arguments": arguments, "model_produced": True}
    if request["name"] != "verify_candidate":
        return request, {"status": "error", "reason": "unknown_tool"}
    if not arguments.get("candidate_answer"):
        return request, {"status": "error", "reason": "missing_arguments"}
    return request, {"status": "success", "knowledge": case["knowledge"], "question": case["question"], "candidate_answer": case["candidate_answer"]}


def halueval_tool_final(case: dict[str, Any], request: dict[str, Any], result: dict[str, Any]) -> tuple[str, str]:
    prompt = f"AUTHORITATIVE_TOOL_RESULT:\n{json.dumps(result, ensure_ascii=False, sort_keys=True)}\n\nDoes the candidate answer contain hallucinated information? Reply only Yes or No."
    return "Judge only from the authoritative verifier result. Reply exactly Yes or No.", prompt


def halueval_uir_prompt(case: dict[str, Any]) -> tuple[str, str, list[str]]:
    prompt = f"VERIFIED_KNOWLEDGE:\n{case['knowledge']}\n\nQUESTION:\n{case['question']}\n\nCANDIDATE_ANSWER:\n{case['candidate_answer']}\n\nReturn JSON only: {{\"judgement\":\"Yes or No\",\"evidence_quote\":\"exact short quote copied from VERIFIED_KNOWLEDGE\"}}. Yes means the candidate contains hallucinated information."
    return "UIR output contract: select a judgement and bind it to an exact verified evidence quote.", prompt, ["official_knowledge"]


def apply_halueval_uir(raw: str, knowledge: str) -> tuple[str, str]:
    parsed = extract_json(raw)
    if not parsed:
        return "INVALID", ""
    judgement = parse_yes_no(str(parsed.get("judgement", "")))
    quote = str(parsed.get("evidence_quote", "")).strip()
    if judgement == "INVALID" or not quote or quote.lower() not in knowledge.lower():
        return "INVALID", quote
    return judgement, quote
