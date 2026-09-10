#!/usr/bin/env python3
"""Post-generation scorers for frozen official FinQA and HaluEval-QA rows."""
from __future__ import annotations

import csv
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

from evaluation.uir_phase4c.common import EXTERNAL_PIPELINES, FROZEN_DIR, RESULTS_DIR, SOURCE_DIR, read_jsonl, row_hash, write_jsonl


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def _load_official_finqa_evaluator():
    path = SOURCE_DIR / "FinQA/evaluate.py"
    spec = importlib.util.spec_from_file_location("phase4c_official_finqa_evaluate", path)
    if spec is None or spec.loader is None: raise ImportError(path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def _numeric_value(text: str) -> float | str | None:
    lowered = str(text).strip().lower()
    if lowered in {"yes", "no"}: return lowered
    matches = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?\s*%?", lowered)
    if not matches: return None
    token = matches[-1].replace(",", "").replace(" ", "")
    percent = token.endswith("%"); token = token.rstrip("%")
    try:
        value = float(token); return round(value / 100.0 if percent else value, 5)
    except ValueError: return None


def score_finqa() -> None:
    source = json.loads((SOURCE_DIR / "FinQA/test.json").read_text(encoding="utf-8"))
    runtime = {row["case_id"]: row for row in read_jsonl(FROZEN_DIR / "finqa_runtime_200.jsonl")}
    evaluator = _load_official_finqa_evaluator(); summary = []
    for pipeline in EXTERNAL_PIPELINES:
        short = pipeline.split("_")[0]; path = RESULTS_DIR / f"finqa_predictions_actual_{short}.jsonl"; records = read_jsonl(path)
        execution_correct = 0; program_correct = 0; mapping_correct = 0
        for record in records:
            run = runtime[record["case_id"]]; official = source[run["source_index"]]
            mapping_ok = official["id"] == record["source_original_id"] and row_hash(official) == record["source_row_hash"]
            mapping_correct += int(mapping_ok)
            predicted = _numeric_value(record["prediction"]); gold = official["qa"]["exe_ans"]
            gold_value = gold.lower() if isinstance(gold, str) else round(float(gold), 5)
            execution_match = predicted == gold_value
            execution_correct += int(execution_match)
            program_match = False
            if record.get("predicted_program"):
                try:
                    pred_tokens = evaluator.program_tokenization(record["predicted_program"])
                    gold_tokens = evaluator.program_tokenization(official["qa"]["program"])
                    program_match = bool(evaluator.equal_program(gold_tokens, pred_tokens))
                except (AssertionError, KeyError, IndexError, TypeError, ValueError):
                    program_match = False
            program_correct += int(program_match)
            record["score"] = {"official_execution_match": execution_match, "official_program_match": program_match, "source_mapping_match": mapping_ok}
        write_jsonl(path, records)
        n = len(records)
        summary.append({"pipeline": pipeline, "official_test_cases": n, "execution_accuracy": execution_correct / n, "uir_numeric_answer_accuracy": execution_correct / n, "program_accuracy": program_correct / n, "source_mapping_rate": mapping_correct / n, "latency_p50_ms": float(np.quantile([row["timing"]["end_to_end_ms"] for row in records], 0.5)), "latency_p95_ms": float(np.quantile([row["timing"]["end_to_end_ms"] for row in records], 0.95))})
    _write_csv(RESULTS_DIR / "finqa_results_actual.csv", summary)


def score_halueval() -> None:
    source = [json.loads(line) for line in (SOURCE_DIR / "HaluEval/qa_data.json").read_text(encoding="utf-8").splitlines() if line.strip()]
    runtime = {row["case_id"]: row for row in read_jsonl(FROZEN_DIR / "halueval_qa_runtime_200.jsonl")}; summary = []
    for pipeline in EXTERNAL_PIPELINES:
        short = pipeline.split("_")[0]; path = RESULTS_DIR / f"halueval_predictions_actual_{short}.jsonl"; records = read_jsonl(path)
        correct = mapping_correct = tp = tn = fp = fn = invalid = 0
        for record in records:
            run = runtime[record["case_id"]]; official = source[run["source_index"]]
            mapping_ok = row_hash(official) == record["source_row_hash"] and record["source_original_id"] == f"qa_data.json:{run['source_index']}"; mapping_correct += int(mapping_ok)
            candidate = run["candidate_answer"]
            if candidate == official["right_answer"]: label = "No"
            elif candidate == official["hallucinated_answer"]: label = "Yes"
            else: raise ValueError(f"candidate does not map to official row: {record['case_id']}")
            prediction = record["prediction"]
            match = prediction == label; correct += int(match); invalid += int(prediction not in {"Yes", "No"})
            if prediction == "Yes" and label == "Yes": tp += 1
            elif prediction == "No" and label == "No": tn += 1
            elif prediction == "Yes" and label == "No": fp += 1
            elif prediction == "No" and label == "Yes": fn += 1
            record["score"] = {"label": label, "correct": match, "source_mapping_match": mapping_ok}
        write_jsonl(path, records); n = len(records)
        summary.append({"pipeline": pipeline, "official_qa_cases": n, "accuracy": correct / n, "true_positive": tp, "true_negative": tn, "false_positive": fp, "false_negative": fn, "invalid_output_rate": invalid / n, "source_mapping_rate": mapping_correct / n, "latency_p50_ms": float(np.quantile([row["timing"]["end_to_end_ms"] for row in records], 0.5)), "latency_p95_ms": float(np.quantile([row["timing"]["end_to_end_ms"] for row in records], 0.95))})
    _write_csv(RESULTS_DIR / "halueval_results_actual.csv", summary)


def main() -> None:
    score_finqa(); score_halueval(); print(json.dumps({"status": "OFFICIAL_SCORING_COMPLETE", "finqa": 200, "halueval": 200}, sort_keys=True))


if __name__ == "__main__": main()
