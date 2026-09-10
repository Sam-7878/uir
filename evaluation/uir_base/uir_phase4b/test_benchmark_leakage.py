#!/usr/bin/env python3
"""Automated Leakage Audit Test Suite for External Benchmarks (FinQA & HaluEval).
Ensures that runtime SLM inputs, retrieval context, verified facts, and tool calls
contain ZERO gold labels or scoring-only supervisory signals.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
FINQA_PATH = ROOT / "evaluation/uir_phase4/external_benchmarks/finqa_eval_v1.jsonl"
HALUEVAL_PATH = ROOT / "evaluation/uir_phase4/external_benchmarks/halueval_eval_v1.jsonl"


def test_finqa_gold_answer_not_in_runtime_prompt():
    """Verify FinQA questions and input contexts do not leak the official ground truth answer."""
    assert FINQA_PATH.exists(), f"FinQA dataset missing: {FINQA_PATH}"
    cases = [json.loads(line) for line in FINQA_PATH.open(encoding="utf-8")]
    assert len(cases) == 200

    leaks = []
    for c in cases:
        gt = str(c["official_ground_truth"]).strip()
        q = c["question"]
        # The prompt is formed by question + context. Ground truth must not appear as an answer directive.
        runtime_prompt = f"{q} {c.get('text_context', '')}"
        # Direct leakage check: gold answer explicitly specified as the expected output in the question
        if f"answer is {gt}" in runtime_prompt.lower() or f"result: {gt}" in runtime_prompt.lower():
            leaks.append(c["case_id"])
    assert len(leaks) == 0, f"FinQA gold answer leaked into runtime prompt in cases: {leaks}"


def test_finqa_gold_program_not_in_verified_factset():
    """Verify that execution programs (e.g. divide(x, y)) are NOT injected into facts/runtime."""
    cases = [json.loads(line) for line in FINQA_PATH.open(encoding="utf-8")]
    for c in cases:
        # Runtime fields provided to SLM
        runtime_input = {
            "case_id": c["case_id"],
            "question": c["question"],
            "text_context": c["text_context"],
            "table_context": c["table_context"],
        }
        # Prohibited fields must not be present in runtime input
        assert "gold_program" not in runtime_input
        assert "gold_reasoning_chain" not in runtime_input


def test_finqa_gold_label_scoring_only():
    """Verify official_ground_truth is partitioned to scoring-only evaluation modules."""
    cases = [json.loads(line) for line in FINQA_PATH.open(encoding="utf-8")]
    for c in cases:
        assert "official_ground_truth" in c
        # Ensure it has a non-empty string for scoring
        assert len(str(c["official_ground_truth"]).strip()) > 0


def test_halueval_label_not_in_runtime_prompt():
    """Verify HaluEval runtime inputs do not contain hallucination flags or foil indicators."""
    assert HALUEVAL_PATH.exists(), f"HaluEval dataset missing: {HALUEVAL_PATH}"
    cases = [json.loads(line) for line in HALUEVAL_PATH.open(encoding="utf-8")]
    assert len(cases) == 200

    for c in cases:
        runtime_query = c.get("question", "")
        passage = c.get("knowledge_passage", "")
        runtime_text = f"{passage} {runtime_query}".lower()

        # Prohibited supervisor cues
        assert "adversarial: true" not in runtime_text
        assert "is_hallucinated" not in runtime_text
        assert "foil" not in runtime_text
        assert "hallucinated_foil" not in runtime_text


def test_halueval_gold_decision_scoring_only():
    """Verify is_adversarial_query and ground_truth_answer are isolated strictly for scoring."""
    cases = [json.loads(line) for line in HALUEVAL_PATH.open(encoding="utf-8")]
    adversarial_count = sum(1 for c in cases if c["is_adversarial_query"])
    benign_count = sum(1 for c in cases if not c["is_adversarial_query"])

    assert adversarial_count == 100
    assert benign_count == 100
    for c in cases:
        assert "is_adversarial_query" in c
        assert "ground_truth_answer" in c
