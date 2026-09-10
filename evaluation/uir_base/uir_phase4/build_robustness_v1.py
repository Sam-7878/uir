#!/usr/bin/env python3
"""ROBUSTNESS-v1 Stress Suite Builder (1,000 cases).
Languages: Korean (>=400), English (>=400), Code-mixed (>=200).
Covers: Paraphrases, particle variations, spacing, honorifics, prepositions,
negation, double negation, unless/except, nested conditions, coordination,
ellipsis, multi-entity, code-switching, and OOD requests.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

DEST_DIR = Path(__file__).resolve().parent
ROBUSTNESS_FILE = DEST_DIR / "robustness_v1_test.jsonl"


def build_robustness_suite() -> list[dict]:
    random.seed(2026)
    cases = []
    case_idx = 0

    entities = ["QV0001", "QV0002", "QV0003", "SEC1001", "SEC1002", "CORP88"]
    metrics = ["assets", "revenue", "operating_income", "net_income"]
    years = [2021, 2022, 2023, 2024]

    # 1. Korean Variations (400 cases)
    # Includes particle shifts, honorifics, spacing, unless/except, nested conditions
    for i in range(400):
        ent = entities[i % len(entities)]
        met = metrics[i % len(metrics)]
        yr = years[i % len(years)]
        style = i % 8

        if style == 0:  # Standard particle
            text = f"{ent}의 {yr}년 {met} 수치를 검증해 주세요"
            intent, cond_type = "VERIFY", "EQ"
            is_valid, is_clarify = True, False
        elif style == 1:  # Topic particle + formal honorific
            text = f"{ent} 기업에 대해서는 {yr}년도 {met}을 확인하십시오"
            intent, cond_type = "VERIFY", "EQ"
            is_valid, is_clarify = True, False
        elif style == 2:  # Spacing error / contraction
            text = f"{ent}기업{yr}년{met}검증요청"
            intent, cond_type = "VERIFY", "EQ"
            is_valid, is_clarify = True, False
        elif style == 3:  # Imperative / abrupt ending
            text = f"{ent} {yr} {met} 대조 바람"
            intent, cond_type = "VERIFY", "EQ"
            is_valid, is_clarify = True, False
        elif style == 4:  # Unless / Except
            text = f"출처가 없는 경우는 제외하고 {ent}의 {yr}년 {met} 값을 알려줘"
            intent, cond_type = "VERIFY", "EXCEPT"
            is_valid, is_clarify = True, False
        elif style == 5:  # Nested condition / double constraint
            text = f"{yr}년 이상이고 검증된 경우에 한해 {ent}의 {met} 추출"
            intent, cond_type = "EXTRACT", "AND"
            is_valid, is_clarify = True, False
        elif style == 6:  # Ellipsis / Underspecified (NeedsClarification)
            text = f"{ent}의 {met} 수치 확인"  # missing year
            intent, cond_type = "UNKNOWN", "NONE"
            is_valid, is_clarify = False, True
        else:  # OOD unsupported request
            text = f"{ent} 대표이사의 오늘의 운세를 점쳐줘"
            intent, cond_type = "OOD", "NONE"
            is_valid, is_clarify = False, False

        cases.append({
            "case_id": f"ROB-KO-{case_idx:04d}",
            "language": "ko",
            "category": "korean_variation",
            "style_id": style,
            "input": text,
            "target": ent if not is_clarify and style != 7 else "",
            "metric": met if not is_clarify and style != 7 else "",
            "period": str(yr) if not is_clarify and style != 7 else "",
            "expected_intent": intent,
            "condition_type": cond_type,
            "is_valid": is_valid,
            "needs_clarification": is_clarify,
        })
        case_idx += 1

    # 2. English Variations (400 cases)
    # Includes preposition variants, negation, double negation, unless/except, nested, OOD
    for i in range(400):
        ent = entities[i % len(entities)]
        met = metrics[i % len(metrics)]
        yr = years[i % len(years)]
        style = i % 8

        if style == 0:  # Standard
            text = f"Please verify company {ent} metric {met} in {yr}"
            intent, cond_type = "VERIFY", "EQ"
            is_valid, is_clarify = True, False
        elif style == 1:  # Preposition variation
            text = f"Substantiate the {met} figure reported by {ent} for the fiscal period {yr}"
            intent, cond_type = "VERIFY", "EQ"
            is_valid, is_clarify = True, False
        elif style == 2:  # Negation / Non-zero
            text = f"Audit {ent} in {yr} to confirm that {met} was non-negative"
            intent, cond_type = "VERIFY", "GE"
            is_valid, is_clarify = True, False
        elif style == 3:  # Unless / Except
            text = f"Unless provenance is unverified, retrieve {ent} {met} for {yr}"
            intent, cond_type = "EXTRACT", "EXCEPT"
            is_valid, is_clarify = True, False
        elif style == 4:  # Nested condition
            text = f"If period is at least {yr} and entity is authenticated, evaluate {ent} {met}"
            intent, cond_type = "ANALYZE", "AND"
            is_valid, is_clarify = True, False
        elif style == 5:  # Double negation
            text = f"Ensure it is not false that {ent} reported {met} in {yr}"
            intent, cond_type = "VERIFY", "NOT"
            is_valid, is_clarify = True, False
        elif style == 6:  # Ellipsis (missing period)
            text = f"Verify {met} associated with {ent}"
            intent, cond_type = "UNKNOWN", "NONE"
            is_valid, is_clarify = False, True
        else:  # OOD
            text = f"Predict the stock price trajectory of {ent} next month"
            intent, cond_type = "OOD", "NONE"
            is_valid, is_clarify = False, False

        cases.append({
            "case_id": f"ROB-EN-{case_idx:04d}",
            "language": "en",
            "category": "english_variation",
            "style_id": style,
            "input": text,
            "target": ent if not is_clarify and style != 7 else "",
            "metric": met if not is_clarify and style != 7 else "",
            "period": str(yr) if not is_clarify and style != 7 else "",
            "expected_intent": intent,
            "condition_type": cond_type,
            "is_valid": is_valid,
            "needs_clarification": is_clarify,
        })
        case_idx += 1

    # 3. Code-Mixed / Code-Switching (200 cases)
    # Combines English terms in Korean syntax and Korean entities in English frames
    for i in range(200):
        ent = entities[i % len(entities)]
        met = metrics[i % len(metrics)]
        yr = years[i % len(years)]
        style = i % 4

        if style == 0:
            text = f"{ent}의 {yr}년 {met} figure를 verify해 줘"
            intent, cond_type = "VERIFY", "EQ"
            is_valid, is_clarify = True, False
        elif style == 1:
            text = f"For company {ent}, {yr}년도 {met} 수치 audit 요청합니다"
            intent, cond_type = "VERIFY", "EQ"
            is_valid, is_clarify = True, False
        elif style == 2:  # Ellipsis in code-switch
            text = f"{ent} {met} please check"
            intent, cond_type = "UNKNOWN", "NONE"
            is_valid, is_clarify = False, True
        else:  # Nested code-switch
            text = f"Unless provenance가 누락된 경우, {ent} {yr} {met} extract"
            intent, cond_type = "EXTRACT", "EXCEPT"
            is_valid, is_clarify = True, False

        cases.append({
            "case_id": f"ROB-MIX-{case_idx:04d}",
            "language": "code_mixed",
            "category": "code_switching",
            "style_id": style,
            "input": text,
            "target": ent if not is_clarify else "",
            "metric": met if not is_clarify else "",
            "period": str(yr) if not is_clarify else "",
            "expected_intent": intent,
            "condition_type": cond_type,
            "is_valid": is_valid,
            "needs_clarification": is_clarify,
        })
        case_idx += 1

    return cases


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    suite = build_robustness_suite()
    with ROBUSTNESS_FILE.open("w", encoding="utf-8") as f:
        for c in suite:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    h = hashlib.sha256(ROBUSTNESS_FILE.read_bytes()).hexdigest()
    print(f"[+] Built ROBUSTNESS-v1: {len(suite)} cases (SHA-256: {h})")


if __name__ == "__main__":
    main()
