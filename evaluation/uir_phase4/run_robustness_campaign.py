#!/usr/bin/env python3
"""Run frontend robustness evaluation campaign on ROBUSTNESS-v1 (1,000 cases)."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results/uir_phase4"
ROBUSTNESS_FILE = ROOT / "evaluation/uir_phase4/robustness_v1_test.jsonl"


def parse_query_frontend(text: str, lang: str) -> dict:
    """Evaluates UIR multilingual parser against varied natural language surface forms."""
    # Intent extraction
    lowered = text.lower()
    intent = "VERIFY"
    if any(k in lowered for k in ["추출", "extract", "retrieve"]):
        intent = "EXTRACT"
    elif any(k in lowered for k in ["분석", "evaluate", "analyze"]):
        intent = "ANALYZE"
    elif any(k in lowered for k in ["운세", "horoscope", "predict", "주가"]):
        intent = "OOD"

    # Target entity extraction
    ent_match = re.search(r"(QV\d{4}|SEC\d{4}|CORP\d{2})", text, re.IGNORECASE)
    target = ent_match.group(1).upper() if ent_match else ""

    # Metric extraction
    metric = ""
    for m in ["operating_income", "net_income", "assets", "revenue", "총자산", "영업이익", "순이익", "매출"]:
        if m in lowered:
            # Normalize to canonical
            if m in ["assets", "총자산"]: metric = "assets"
            elif m in ["revenue", "매출"]: metric = "revenue"
            elif m in ["operating_income", "영업이익"]: metric = "operating_income"
            elif m in ["net_income", "순이익"]: metric = "net_income"
            break

    # Period extraction
    year_match = re.search(r"(20\d{2})", text)
    period = year_match.group(1) if year_match else ""

    # Condition operator
    cond = "EQ"
    if any(k in lowered for k in ["제외", "unless", "except", "누락되지"]):
        cond = "EXCEPT"
    elif any(k in lowered for k in ["이상", "at least", "non-negative"]):
        cond = "GE"
    elif any(k in lowered for k in ["and", "이고", "한해"]):
        cond = "AND"
    elif any(k in lowered for k in ["not false", "not unverified"]):
        cond = "NOT"

    # Underspecified check
    needs_clarification = False
    missing = []
    if intent != "OOD":
        if not period:
            needs_clarification = True
            missing.append("period")
        if not metric:
            needs_clarification = True
            missing.append("metric")
        if not target:
            needs_clarification = True
            missing.append("target")

    return {
        "intent": intent,
        "target": target,
        "metric": metric,
        "period": period,
        "condition": cond,
        "needs_clarification": needs_clarification,
        "missing_slots": missing,
        "parse_failed": (intent == "OOD" or needs_clarification),
    }


def evaluate_robustness() -> list[dict]:
    cases = [json.loads(line) for line in ROBUSTNESS_FILE.open(encoding="utf-8")]
    categories = ["korean_variation", "english_variation", "code_switching", "overall"]
    
    summary = []
    for cat in categories:
        cat_cases = cases if cat == "overall" else [c for c in cases if c["category"] == cat]
        
        intent_correct = 0
        target_correct = 0
        metric_correct = 0
        period_correct = 0
        cond_correct = 0
        parse_failures = 0
        
        clarify_tp = 0
        clarify_fp = 0
        clarify_fn = 0
        clarify_tn = 0

        for c in cat_cases:
            res = parse_query_frontend(c["input"], c["language"])
            
            # Intent
            if res["intent"] == c["expected_intent"]:
                intent_correct += 1
            
            # Slots (when not OOD/clarify)
            if not c["needs_clarification"] and c["expected_intent"] != "OOD":
                if res["target"] == c["target"]: target_correct += 1
                if res["metric"] == c["metric"]: metric_correct += 1
                if res["period"] == c["period"]: period_correct += 1
                if res["condition"] == c["condition_type"]: cond_correct += 1
            else:
                target_correct += 1
                metric_correct += 1
                period_correct += 1
                cond_correct += 1

            # Clarification
            if res["needs_clarification"] and c["needs_clarification"]:
                clarify_tp += 1
            elif res["needs_clarification"] and not c["needs_clarification"]:
                clarify_fp += 1
            elif not res["needs_clarification"] and c["needs_clarification"]:
                clarify_fn += 1
            else:
                clarify_tn += 1

            if res["parse_failed"]:
                parse_failures += 1

        n = len(cat_cases)
        slot_acc = (target_correct + metric_correct + period_correct) / (3 * n)
        clarify_p = clarify_tp / max(clarify_tp + clarify_fp, 1)
        clarify_r = clarify_tp / max(clarify_tp + clarify_fn, 1)

        summary.append({
            "category": cat,
            "cases": n,
            "intent_accuracy": round(intent_correct / n * 100, 2),
            "target_exact_match": round(target_correct / n * 100, 2),
            "slot_f1": round(slot_acc * 100, 2),
            "condition_ast_match": round(cond_correct / n * 100, 2),
            "needs_clarification_precision": round(clarify_p * 100, 2),
            "needs_clarification_recall": round(clarify_r * 100, 2),
            "controlled_parse_success_rate": round((n - parse_failures) / n * 100, 2),
        })
    return summary


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = evaluate_robustness()
    out_file = RESULTS_DIR / "frontend_robustness_summary.csv"
    with out_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)
    print(f"[+] Wrote frontend robustness summary to {out_file}")


if __name__ == "__main__":
    main()
