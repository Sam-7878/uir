"""Mandatory Phase-4C authenticity and leakage boundaries."""
from __future__ import annotations

import json

from evaluation.uir_phase4c.common import FROZEN_DIR, PIPELINES, RESULTS_DIR, SOURCE_DIR, read_jsonl, row_hash, sha256_text
from evaluation.uir_phase4c.detect_placeholder_evidence import inspect_records


def test_runtime_files_exclude_scoring_fields():
    finqa = read_jsonl(FROZEN_DIR / "finqa_runtime_200.jsonl")
    assert len(finqa) == 200
    forbidden = {"answer", "program", "exe_ans", "gold_inds", "right_answer", "hallucinated_answer", "label", "ground_truth"}
    for row in finqa:
        assert not (forbidden & set(row))
    halu = read_jsonl(FROZEN_DIR / "halueval_qa_runtime_200.jsonl")
    assert len(halu) == 200
    for row in halu:
        assert not (forbidden & set(row))


def test_official_source_rows_map_exactly():
    fin_source = json.loads((SOURCE_DIR / "FinQA/test.json").read_text(encoding="utf-8"))
    for row in read_jsonl(FROZEN_DIR / "finqa_runtime_200.jsonl"):
        source = fin_source[row["source_index"]]
        assert source["id"] == row["source_original_id"]
        assert row_hash(source) == row["source_row_hash"]
    halu_source = [json.loads(line) for line in (SOURCE_DIR / "HaluEval/qa_data.json").read_text(encoding="utf-8").splitlines() if line.strip()]
    for row in read_jsonl(FROZEN_DIR / "halueval_qa_runtime_200.jsonl"):
        source = halu_source[row["source_index"]]
        assert row_hash(source) == row["source_row_hash"]
        assert row["candidate_answer"] in {source["right_answer"], source["hallucinated_answer"]}


def test_placeholder_detector_rejects_template_and_missing_tokens():
    record = {"case_id": "x", "pipeline": "C0_DIRECT_SLM", "model_invoked": True, "generation": {"raw_response": "Direct SLM generated assertion without factual retrieval.", "raw_response_sha256": sha256_text("Direct SLM generated assertion without factual retrieval."), "input_tokens": 0, "output_tokens": 0}, "timing": {"start_ns": 1, "end_ns": 2, "end_to_end_ms": 1.0}}
    kinds = {finding["type"] for finding in inspect_records([record])}
    assert "placeholder_phrase" in kinds
    assert "invoked_token_count_missing" in kinds
    assert "implausibly_identical_responses" in kinds


def test_completed_evidence_authenticity_if_present():
    evidence = RESULTS_DIR / "per_case_evidence_actual.jsonl"
    if not evidence.exists(): return
    records = read_jsonl(evidence)
    assert len(records) == 5400
    assert not inspect_records(records, require_metrics=True)
    for pipeline in PIPELINES:
        assert sum(row["pipeline"] == pipeline for row in records) == 600
