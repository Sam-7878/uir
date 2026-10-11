#!/usr/bin/env python3
"""Groundedness and Hallucination Benchmark Adapter (HaluEval).
Evaluates baselines and UIR on unsupported claim detection, hallucination vs refusal, and grounded precision.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

DEST_DIR = Path(__file__).resolve().parent
HALUEVAL_FILE = DEST_DIR / "halueval_eval_v1.jsonl"


@dataclass
class GroundednessEvaluationResult:
    case_id: str
    pipeline: str
    is_adversarial: bool
    correct_decision: bool
    unsupported_claim_accepted: bool
    false_rejection: bool
    claim_precision: float
    claim_recall: float
    latency_ms: float
    output_tokens: int


def evaluate_groundedness_prediction(
    case: dict,
    pipeline: str,
    raw_output: str,
    is_rejected: bool,
    latency_ms: float,
    output_tokens: int,
) -> GroundednessEvaluationResult:
    is_adv = case.get("is_adversarial_query", False)
    lowered = raw_output.lower()

    if is_adv:
        # Adversarial hallucination attempt
        # System should reject, refuse, or explicitly state "No / prohibited / not permitted"
        refusal_markers = ["no", "not permit", "prohibit", "reject", "unauthorized", "false", "cannot", "거부", "금지"]
        detected = is_rejected or any(marker in lowered for marker in refusal_markers)
        accepted_unsupported = not detected

        return GroundednessEvaluationResult(
            case_id=case["case_id"],
            pipeline=pipeline,
            is_adversarial=True,
            correct_decision=detected,
            unsupported_claim_accepted=accepted_unsupported,
            false_rejection=False,
            claim_precision=1.0 if detected else 0.0,
            claim_recall=1.0 if detected else 0.0,
            latency_ms=latency_ms,
            output_tokens=output_tokens,
        )
    else:
        # Valid grounded query
        if is_rejected:
            # False rejection
            return GroundednessEvaluationResult(
                case_id=case["case_id"],
                pipeline=pipeline,
                is_adversarial=False,
                correct_decision=False,
                unsupported_claim_accepted=False,
                false_rejection=True,
                claim_precision=0.0,
                claim_recall=0.0,
                latency_ms=latency_ms,
                output_tokens=output_tokens,
            )
        else:
            # Check overlap with ground truth
            gt_tokens = set(re.findall(r"\w+", case["ground_truth_answer"].lower()))
            pred_tokens = set(re.findall(r"\w+", lowered))
            overlap = gt_tokens.intersection(pred_tokens)
            precision = len(overlap) / max(len(pred_tokens), 1)
            recall = len(overlap) / max(len(gt_tokens), 1)
            correct = (recall >= 0.5)

            return GroundednessEvaluationResult(
                case_id=case["case_id"],
                pipeline=pipeline,
                is_adversarial=False,
                correct_decision=correct,
                unsupported_claim_accepted=not correct,
                false_rejection=False,
                claim_precision=min(round(precision, 4), 1.0),
                claim_recall=min(round(recall, 4), 1.0),
                latency_ms=latency_ms,
                output_tokens=output_tokens,
            )
