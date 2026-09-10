"""Unit tests for FinQA and HaluEval adapters."""
from __future__ import annotations

import pytest
from evaluation.uir_phase4d.adapters.finqa_adapter import (
    build_numeric_catalog,
    finqa_prompt_phase4d,
    safe_execute_numeric_catalog,
)
from evaluation.uir_phase4d.adapters.halueval_adapter import (
    format_sentence_chunks,
    halueval_prompt_phase4d,
    segment_sentences,
    verify_halueval_uir_contract,
)


def test_finqa_adapter():
    sample_case = {
        "case_id": "TEST-01",
        "question": "What is net margin change?",
        "pre_text": ["Operating income was 150.0 million in 2024."],
        "post_text": ["Revenue was 600.0 million."],
        "table": [["Metric", "2024"], ["Tax", "25.0"]],
    }
    catalog = build_numeric_catalog(sample_case)
    assert "num_0" in catalog
    assert catalog["num_0"]["val"] == 150.0
    assert "c_100" in catalog

    sys_prompt, prompt, cat = finqa_prompt_phase4d(sample_case, "C8_FINAL_UIR_B6")
    assert "VERIFIED_NUMERIC_CATALOG" in prompt

    # Safe arithmetic execution
    res = safe_execute_numeric_catalog("num_0 + num_1", {"num_0": {"val": 150.0}, "num_1": {"val": 25.0}})
    assert res["status"] == "success"
    assert res["value"] == 175.0

    # Unsafe command injection prevention
    res_unsafe = safe_execute_numeric_catalog("__import__('os').system('ls')", {})
    assert res_unsafe["status"] == "error"


def test_halueval_adapter():
    sample_case = {
        "case_id": "TEST-H01",
        "knowledge": "Apple was founded in 1976. It is headquartered in Cupertino.",
        "question": "Where is Apple located?",
        "candidate_answer": "Apple is located in Cupertino. It was founded in 1999.",
    }
    k_sents = segment_sentences(sample_case["knowledge"])
    assert len(k_sents) == 2
    k_text, k_chunks = format_sentence_chunks(k_sents)
    assert "S1" in k_chunks and "S2" in k_chunks

    # Valid grounded contract
    model_json = {
        "claim_evaluations": [
            {"claim_id": "C1", "supported": True, "evidence_id": "S2", "reasoning": "Cupertino match"},
            {"claim_id": "C2", "supported": False, "evidence_id": None, "reasoning": "1999 not supported"},
        ],
        "overall_hallucination": "Yes",
    }
    c_chunks = {"C1": "Apple is located in Cupertino.", "C2": "It was founded in 1999."}
    v_res = verify_halueval_uir_contract(model_json, k_chunks, c_chunks)
    assert v_res["valid_contract"] is True
    assert v_res["overall_hallucination"] == "Yes"
    assert v_res["has_unsupported_claim"] is True

    # Ungrounded reference (hallucinated evidence ID S99)
    model_invalid_ref = {
        "claim_evaluations": [
            {"claim_id": "C1", "supported": True, "evidence_id": "S99", "reasoning": "Fake ref"}
        ],
        "overall_hallucination": "No",
    }
    v_res2 = verify_halueval_uir_contract(model_invalid_ref, k_chunks, c_chunks)
    assert v_res2["overall_hallucination"] == "Yes"  # Enforced override
    assert v_res2["has_unsupported_claim"] is True
