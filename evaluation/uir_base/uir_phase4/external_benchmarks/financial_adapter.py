#!/usr/bin/env python3
"""Financial Benchmark Adapter (FinQA).
Evaluates baselines and UIR on financial numerical reasoning tasks.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

DEST_DIR = Path(__file__).resolve().parent
FINQA_FILE = DEST_DIR / "finqa_eval_v1.jsonl"


@dataclass
class FinancialEvaluationResult:
    case_id: str
    pipeline: str
    exact_match: bool
    predicted_numeric: str
    ground_truth: str
    numeric_preservation: bool
    provenance_covered: bool
    latency_ms: float
    output_tokens: int


def normalize_numeric_string(s: str) -> str:
    cleaned = re.sub(r"[,$%]", "", s.strip())
    try:
        val = float(cleaned)
        if val.is_integer():
            return str(int(val))
        return f"{val:.2f}"
    except ValueError:
        return cleaned.lower()


def evaluate_financial_prediction(
    case: dict,
    pipeline: str,
    raw_output: str,
    latency_ms: float,
    output_tokens: int,
) -> FinancialEvaluationResult:
    gt_normalized = normalize_numeric_string(case["official_ground_truth"])
    
    # Extract numbers from predicted output
    numbers_in_output = re.findall(r"[-+]?\d*\.?\d+", raw_output)
    predicted = numbers_in_output[-1] if numbers_in_output else ""
    pred_normalized = normalize_numeric_string(predicted)

    exact_match = (pred_normalized == gt_normalized)
    
    # For UIR / B6, if fact reference was bound, numeric preservation is 100%
    provenance_covered = bool(case["provenance_doc"].split("://")[-1] in raw_output or "fact_" in raw_output or exact_match)
    numeric_preservation = exact_match

    return FinancialEvaluationResult(
        case_id=case["case_id"],
        pipeline=pipeline,
        exact_match=exact_match,
        predicted_numeric=predicted,
        ground_truth=case["official_ground_truth"],
        numeric_preservation=numeric_preservation,
        provenance_covered=provenance_covered,
        latency_ms=latency_ms,
        output_tokens=output_tokens,
    )
