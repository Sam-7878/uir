"""Typed Numeric-Catalog Arithmetic UIR Adapter for FinQA (P4).

Implements Option A:
- Extracts numbered numeric catalog from text/table context.
- Model produces typed expression over catalog keys: e.g. {"expression": "num_1 - num_0", "evidence_refs": ["num_1", "num_0"]}
- Deterministic arithmetic engine evaluates the expression safely.
- No hallucinations of external numbers permitted without source evidence refs.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from evaluation.uir_phase4d.common import extract_json


def _extract_numbers_from_text(text: str) -> list[str]:
    # Match numbers, percentages, currency
    return re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?%?", text)


def build_numeric_catalog(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    idx = 0

    # Add standard constants
    catalog["c_100"] = {"val": 100.0, "raw": "100", "source": "constant:percentage_base"}
    catalog["c_1"] = {"val": 1.0, "raw": "1", "source": "constant:unity"}

    # Extract from pre_text
    for p_idx, para in enumerate(case.get("pre_text", [])):
        for num_str in _extract_numbers_from_text(para):
            val_clean = num_str.replace(",", "").rstrip("%")
            try:
                v = float(val_clean)
                if num_str.endswith("%"):
                    v = v / 100.0
                catalog[f"num_{idx}"] = {"val": v, "raw": num_str, "source": f"pre_text[{p_idx}]"}
                idx += 1
            except ValueError:
                pass

    # Extract from table
    for r_idx, row in enumerate(case.get("table", [])):
        for c_idx, cell in enumerate(row):
            for num_str in _extract_numbers_from_text(str(cell)):
                val_clean = num_str.replace(",", "").rstrip("%")
                try:
                    v = float(val_clean)
                    if num_str.endswith("%"):
                        v = v / 100.0
                    catalog[f"num_{idx}"] = {"val": v, "raw": num_str, "source": f"table[{r_idx}][{c_idx}]"}
                    idx += 1
                except ValueError:
                    pass

    # Extract from post_text
    for p_idx, para in enumerate(case.get("post_text", [])):
        for num_str in _extract_numbers_from_text(para):
            val_clean = num_str.replace(",", "").rstrip("%")
            try:
                v = float(val_clean)
                if num_str.endswith("%"):
                    v = v / 100.0
                catalog[f"num_{idx}"] = {"val": v, "raw": num_str, "source": f"post_text[{p_idx}]"}
                idx += 1
            except ValueError:
                pass

    return catalog


def finqa_format_context(case: dict[str, Any]) -> str:
    lines = []
    if case.get("pre_text"):
        lines.append("CONTEXT_TEXT:")
        lines.extend(case["pre_text"])
    if case.get("table"):
        lines.append("FINANCIAL_TABLE:")
        for row in case["table"]:
            lines.append(" | ".join(map(str, row)))
    if case.get("post_text"):
        lines.append("ADDITIONAL_TEXT:")
        lines.extend(case["post_text"])
    return "\n".join(lines)


def finqa_prompt_phase4d(case: dict[str, Any], pipeline: str) -> tuple[str, str, dict[str, Any]]:
    context_str = finqa_format_context(case)
    catalog = build_numeric_catalog(case)
    catalog_display = {k: v["val"] for k, v in catalog.items() if not k.startswith("c_")}

    if pipeline in {"C1_NAIVE_RAG", "C2_RAG_EXISTENCE_CHECK"}:
        system = "Solve the financial calculation question directly from the provided financial context."
        prompt = (
            f"FINANCIAL_DATA:\n{context_str}\n\n"
            f"QUESTION: {case['question']}\n\n"
            "Calculate the numerical answer. End your response with exactly: FINAL_ANSWER: <value>"
        )
        return system, prompt, catalog

    if pipeline == "C4_TOOL_CALLING_AGENT":
        system = "You are a financial agent. Choose the calculator tool and specify the arithmetic expression."
        prompt = (
            f"FINANCIAL_DATA:\n{context_str}\n\n"
            f"QUESTION: {case['question']}\n\n"
            'Choose tool. Return JSON only: {"name":"calculate","arguments":{"expression":"..."}}'
        )
        return system, prompt, catalog

    if pipeline == "C8_FINAL_UIR_B6":
        system = (
            "You are a typed financial UIR compiler. Solve the question by referencing the catalog of verified numbers.\n"
            "Produce an arithmetic expression referencing only valid catalog keys (e.g. num_0, num_1, c_100, c_1)."
        )
        prompt = (
            f"FINANCIAL_DATA:\n{context_str}\n\n"
            f"VERIFIED_NUMERIC_CATALOG:\n{json.dumps(catalog_display, indent=2)}\n\n"
            f"QUESTION: {case['question']}\n\n"
            "Return JSON only:\n"
            '{"expression": "num_1 - num_0", "evidence_refs": ["num_1", "num_0"], "explanation": "..."}'
        )
        return system, prompt, catalog

    raise ValueError(f"Unsupported pipeline for FinQA: {pipeline}")


def safe_execute_numeric_catalog(expression: str, catalog: dict[str, dict[str, Any]]) -> dict[str, Any]:
    # Replace catalog keys with actual values
    # Sort keys by length descending to avoid partial prefix collisions
    expr_eval = expression.strip()
    keys_sorted = sorted(catalog.keys(), key=lambda k: len(k), reverse=True)
    used_keys = []
    for k in keys_sorted:
        if re.search(r"\b" + re.escape(k) + r"\b", expr_eval):
            expr_eval = re.sub(r"\b" + re.escape(k) + r"\b", str(catalog[k]["val"]), expr_eval)
            used_keys.append(k)

    # Validate characters in arithmetic expression
    if not re.fullmatch(r"[-+*/().\d\s]+", expr_eval):
        return {"status": "error", "reason": f"unsafe_expression_characters: {expr_eval}", "value": None}

    try:
        val = eval(expr_eval, {"__builtins__": None}, {})  # safe arithmetic eval
        return {"status": "success", "value": float(val), "evaluated_expression": expr_eval, "used_keys": used_keys}
    except Exception as e:
        return {"status": "error", "reason": str(e), "value": None}
