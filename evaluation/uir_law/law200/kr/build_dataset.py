#!/usr/bin/env python3
"""Fetch, verify, and freeze an independent Korean LAW-KR-200 stratum."""
from __future__ import annotations

import argparse
import random
import re
from datetime import date
from pathlib import Path
from typing import Any

from evaluation.uir_law.law200.builders.generate_mismatch_cases import mismatch_pairs
from evaluation.uir_law.law200.common import FORBIDDEN_RUNTIME_KEYS, PACKAGE_ROOT, SEED, environment_manifest, sha256_file, sha256_text, utc_now, write_json, write_jsonl
from evaluation.uir_law.law200.kr.law_go_kr import KR_DATA_DIR, LawGoKrClient, exact_case_number, not_found_record, result_rows, valid_record

CASE_NO = re.compile(r"^(\d{4})([가-힣]{1,5})(\d{1,7})$")


def source_date_is_eligible(row: dict[str, Any], as_of: date) -> bool:
    value = str(row.get("선고일자") or "").replace(".", "-")
    try:
        return date.fromisoformat(value) <= as_of
    except ValueError:
        return False


def mutation_candidates(records: list[dict[str, Any]]) -> list[tuple[str, dict[str, str]]]:
    valid_numbers = {str(row["citation_canonical"]) for row in records}
    output: list[tuple[str, dict[str, str]]] = []
    seen = set(valid_numbers)
    for row in records:
        source = str(row["citation_canonical"])
        match = CASE_NO.match(source)
        if not match:
            continue
        year, code, serial_text = match.groups()
        serial = int(serial_text)
        variants = ((serial + 1, "serial_plus_1"), (serial + 7, "serial_plus_7"), (max(1, serial - 1), "serial_minus_1"), (serial + 11, "serial_small_delta"))
        for changed, kind in variants:
            candidate = f"{year}{code}{changed}"
            if candidate not in seen:
                seen.add(candidate)
                output.append((candidate, {"type": kind, "source_valid_citation": source}))
    return output


def opaque_id(split: str, category: str, index: int, language: str) -> str:
    return "lawkr-" + sha256_text(f"{SEED}|KR|{split}|{category}|{index}|{language}")[:18]


def make_query(category: str, record: dict[str, Any], language: str, variant: int, wrong_name: str | None) -> str:
    number = str(record["citation_canonical"])
    if category == "A_VALID":
        return f"Summarize the verified Korean case metadata for case number {number}." if language == "en" else f"사건번호 {number} 판례의 검증된 사건 정보를 요약해 주세요."
    if category == "B_SURFACE_VARIATION":
        if language == "en":
            return ("Please explain the authoritative case identified by {n}.", "Please summarize the verified Korean decision for case no. {n}.", "Describe the metadata for case-number {n}.")[variant % 3].format(n=number)
        return ("{n} 사건의 판례 메타데이터를 설명해 주세요.", "사건 번호 {n}에 해당하는 판결을 요약해 주세요.", "대법원 판례 {n}의 검증된 정보를 설명해 주세요.")[variant % 3].format(n=number)
    if category == "C_NONEXISTENT":
        return f"Summarize the Korean decision with case number {number}." if language == "en" else f"사건번호 {number} 판결의 핵심 정보를 요약해 주세요."
    if category == "D_ENTITY_MISMATCH":
        return f"Summarize {wrong_name} ({number})." if language == "en" else f"{wrong_name} ({number}) 판결을 요약해 주세요."
    raise ValueError(category)


def build_split(split: str, a: list[dict], b: list[dict], invalid: list[dict], d_cites: list[dict], d_names: list[dict]) -> tuple[list[dict], list[dict]]:
    groups: list[tuple[str, list[dict], list[str | None]]] = [
        ("A_VALID", a, [None] * len(a)), ("B_SURFACE_VARIATION", b, [None] * len(b)),
        ("C_NONEXISTENT", invalid, [None] * len(invalid)),
    ]
    pairs = mismatch_pairs(d_cites, d_names)
    groups.append(("D_ENTITY_MISMATCH", [p[0] for p in pairs], [str(p[1]["case_name"]) for p in pairs]))
    runtime: list[dict] = []
    gold: list[dict] = []
    for category, records, wrong_names in groups:
        for index, (record, wrong_name) in enumerate(zip(records, wrong_names, strict=True)):
            for language in ("en", "ko"):
                case_id = opaque_id(split, category, index, language)
                runtime.append({"case_id": case_id, "query": make_query(category, record, language, index, wrong_name)})
                gold.append({
                    "case_id": case_id, "pair_id": f"{split}-KR-{category}-{index:03d}", "language": language,
                    "category": category, "expected_status": {"A_VALID":"VERIFIED","B_SURFACE_VARIATION":"VERIFIED","C_NONEXISTENT":"NOT_FOUND","D_ENTITY_MISMATCH":"MISMATCH"}[category],
                    "expected_action": "ANSWER" if category in {"A_VALID", "B_SURFACE_VARIATION"} else "SAFE_REJECT_OR_CORRECT",
                    "is_valid": category in {"A_VALID", "B_SURFACE_VARIATION"}, "gold_citation": record["citation_canonical"],
                    "gold_case_name": record.get("case_name", ""), "claimed_case_name": wrong_name,
                    "source_id": record["source_id"], "mutation_type": (record.get("mutation") or {}).get("type"),
                    "source_valid_citation": (record.get("mutation") or {}).get("source_valid_citation"),
                })
    order = list(range(len(runtime)))
    random.Random(SEED + 200 + (0 if split == "test" else 1)).shuffle(order)
    return [runtime[i] for i in order], [gold[i] for i in order]


def build(force: bool = False, bug_note: str | None = None) -> dict[str, Any]:
    outputs = [KR_DATA_DIR / name for name in ("law200_test_runtime.jsonl", "law200_test_gold.jsonl", "law200_dev_runtime.jsonl", "law200_dev_gold.jsonl")]
    if any(path.exists() for path in outputs) and not force:
        raise RuntimeError("LAW-KR-200 is already frozen")
    if force and not bug_note:
        raise RuntimeError("--force requires --bug-note")
    client = LawGoKrClient()
    snapshot = client.search("valid_page_001", display=100, page=1, org=400201, sort="ddes")
    valid = []
    seen = set()
    as_of = date.fromisoformat(snapshot.retrieved_at[:10])
    for row in result_rows(snapshot):
        record = valid_record(row, snapshot)
        number = record["citation_canonical"]
        if (
            CASE_NO.match(number)
            and record["case_name"]
            and record["court"] == "대법원"
            and source_date_is_eligible(row, as_of)
            and number not in seen
        ):
            seen.add(number); valid.append(record)
    if len(valid) < 60:
        raise RuntimeError(f"only {len(valid)} usable Korean Supreme Court case records; need 60")
    valid = valid[:60]
    pending = mutation_candidates(valid)
    invalid: list[dict] = []
    for batch_index in range(0, len(pending), 80):
        chunk = pending[batch_index : batch_index + 80]
        search = client.search(f"invalid_batch_{batch_index // 80:03d}", display=100, page=1, nb=",".join(number for number, _ in chunk))
        observed = [exact_case_number(row) for row in result_rows(search)]
        observed_set = set(observed)
        for number, mutation in chunk:
            if number not in observed_set:
                invalid.append(not_found_record(number, mutation, search, observed))
        if len(invalid) >= 30:
            break
    if len(invalid) < 30:
        raise RuntimeError(f"only {len(invalid)} exact-case-number NOT_FOUND mutations; need 30")
    invalid = invalid[:30]
    registry = valid + invalid
    write_jsonl(KR_DATA_DIR / "source_registry.jsonl", registry)
    corpus_dir = KR_DATA_DIR / "corpus"; corpus_dir.mkdir(parents=True, exist_ok=True)
    corpus = [{
        "source_id": row["source_id"], "citation_canonical": row["citation_canonical"], "case_name": row["case_name"],
        "court": row["court"], "date_filed": row["date_filed"], "law_go_kr_prec_id": row["law_go_kr_prec_id"],
        "provenance_pointer": row["source_uri"],
        "verified_summary": f"국가법령정보센터는 사건번호 {row['citation_canonical']}를 {row['case_name']} 사건으로 수록하며 선고일은 {row['date_filed']}이다.",
    } for row in valid]
    write_jsonl(corpus_dir / "legal_cases.jsonl", corpus)
    test_runtime, test_gold = build_split("test", valid[:25], valid[25:50], invalid[:25], valid[:25], valid[25:50])
    dev_runtime, dev_gold = build_split("dev", valid[50:55], valid[55:60], invalid[25:30], valid[50:55], valid[55:60])
    for path, rows in zip(outputs, (test_runtime, test_gold, dev_runtime, dev_gold), strict=True): write_jsonl(path, rows)
    if any(set(row) & FORBIDDEN_RUNTIME_KEYS for row in test_runtime + dev_runtime): raise AssertionError("oracle leakage into Korean runtime")
    manifest = {
        "benchmark": "LAW-KR-200", "version": "1.0.0", "frozen_at": utc_now(), "construction_seed": SEED,
        "authoritative_source": "국가법령정보 공동활용 판례 목록 API", "not_found_semantics": "HTTP 200 with no exact 사건번호 match",
        "source_filters": {"court": "대법원", "decision_date_lte_retrieved_date": True},
        "test_cases": 200, "dev_cases": 40, "hashes": {p.name: sha256_file(p) for p in outputs},
        "source_registry_sha256": sha256_file(KR_DATA_DIR / "source_registry.jsonl"),
        "corpus_sha256": sha256_file(corpus_dir / "legal_cases.jsonl"), "environment": environment_manifest(),
        "rebuild_bug_note": bug_note,
    }
    write_json(KR_DATA_DIR / "benchmark_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--force", action="store_true"); parser.add_argument("--bug-note")
    args = parser.parse_args(); result = build(args.force, args.bug_note)
    print(f"LAW-KR-200 frozen: {result['hashes']['law200_test_runtime.jsonl']}")
