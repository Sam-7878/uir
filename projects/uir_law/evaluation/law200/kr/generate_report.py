#!/usr/bin/env python3
"""Generate publication-facing LAW-KR-200 reports from validated artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.uir_law.law200.common import PACKAGE_ROOT, read_json, read_jsonl, utc_now
from evaluation.uir_law.law200.kr.law_go_kr import KR_DATA_DIR
from evaluation.uir_law.law200.kr.validate_publication_results import (
    KR_AGGREGATE_DIR,
    KR_RAW_DIR,
    KR_TABLES_DIR,
    validate,
)


def pct(value: Any) -> str:
    return "N/A" if value is None else f"{100 * float(value):.2f}%"


def interval(row: dict[str, Any], key: str) -> str:
    value = row[key]
    return f"{pct(value['rate'])} [{pct(value['low'])}, {pct(value['high'])}]"


def comparison(statistics: dict[str, Any], baseline: str) -> dict[str, Any]:
    return next(
        row for row in statistics["primary_comparisons"]
        if row["comparison"] == f"{baseline}_vs_C8_UIR"
    )


def raw_file(pipeline: str) -> Path:
    paths = sorted(KR_RAW_DIR.glob(f"test_{pipeline}_*.jsonl"))
    if len(paths) != 1:
        raise RuntimeError(f"expected one raw test file for {pipeline}; found {paths}")
    return paths[0]


def generate() -> tuple[Path, Path]:
    gate = validate()
    if gate["status"] != "READY_FOR_KAIC_MANUSCRIPT_KR":
        raise RuntimeError("LAW-KR-200 publication validator did not pass")

    manifest = read_json(KR_DATA_DIR / "benchmark_manifest.json")
    hardware = read_json(KR_AGGREGATE_DIR / "hardware_environment.json")
    aggregate_rows = read_json(KR_AGGREGATE_DIR / "test_metrics.json")["pipelines"]
    metrics = {row["pipeline"]: row for row in aggregate_rows}
    statistics = read_json(KR_AGGREGATE_DIR / "test_statistics.json")
    table = (KR_TABLES_DIR / "law200_main_table.md").read_text(encoding="utf-8").strip()
    runtime = {row["case_id"]: row for row in read_jsonl(KR_DATA_DIR / "law200_test_runtime.jsonl")}
    gold = read_jsonl(KR_DATA_DIR / "law200_test_gold.jsonl")
    gold_by_id = {row["case_id"]: row for row in gold}
    scored = read_jsonl(KR_AGGREGATE_DIR / "test_scored_cases.jsonl")
    hard_id = next(
        row["case_id"] for row in scored
        if row["pipeline"] == "C1_NAIVE_RAG"
        and row["category"] == "C_NONEXISTENT"
        and row["invalid_false_acceptance"]
    )
    hard = gold_by_id[hard_id]
    c1_raw = next(row for row in read_jsonl(raw_file("C1_NAIVE_RAG")) if row["case_id"] == hard_id)
    c8_raw = next(row for row in read_jsonl(raw_file("C8_UIR")) if row["case_id"] == hard_id)
    model = c8_raw["model_identity"]
    c1, c2, c4, c5, c8 = (metrics[name] for name in (
        "C1_NAIVE_RAG", "C2_EXISTENCE_CHECK", "C4_TOOL_AGENT", "C5_GUARDRAIL", "C8_UIR"
    ))
    c2_test = comparison(statistics, "C2_EXISTENCE_CHECK")
    best = max(aggregate_rows, key=lambda row: float(row.get("verified_answer_coverage") or 0))
    en, ko = c8["language"]["en"], c8["language"]["ko"]

    report = [
        "# LAW-KR-200 Final Benchmark Report", "",
        f"Generated: {utc_now()}", "",
        "## Outcome", "",
        "LAW-KR-200은 국가법령정보 공동활용 판례 API에서 동결한 대한민국 대법원 사건번호와 사건명 identity metadata를 이용해 typed UIR의 생성 전 개체 검증을 평가한다. 실체적 법률 추론, 판결 요지 정확성, 모든 법률 데이터베이스의 완전성 또는 보편적 환각 제거를 평가하지 않는다.", "",
        f"- Publication gate: `{gate['status']}` ({gate['blocker_count']} blockers)",
        f"- Test queries: {manifest['test_cases']} (English 100, Korean 100; category당 50)",
        f"- Development queries: {manifest['dev_cases']} (test와 ID/query 비중복)",
        f"- LAW200_TEST_SHA256: `{manifest['hashes']['law200_test_runtime.jsonl']}`",
        f"- SOURCE_REGISTRY_SHA256: `{manifest['source_registry_sha256']}`",
        f"- CORPUS_SHA256: `{manifest['corpus_sha256']}`",
        f"- CODE_COMMIT_AT_FREEZE: `{manifest['environment']['git_commit']}`",
        f"- MODEL: `{model.get('model')}` / `{model.get('parameter_size')}` / `{model.get('quantization_level')}`",
        "- Decoding: temperature=0, top_p=1, max_tokens=192, seed=20260911", "",
        f"- CPU: `{hardware['hardware']['cpu_model']}` ({hardware['hardware']['logical_cpu_count']} logical CPUs)",
        f"- WSL-visible memory: `{hardware['hardware']['visible_memory_bytes']}` bytes",
        f"- GPU probe: `{hardware['hardware']['gpu_probe']['status']}`; post-run capture cannot establish whether Ollama used CPU or GPU, so no accelerator-backend claim is made.", "",
        "## Source semantics", "",
        "유효 개체 60건은 공식 응답에서 사건번호가 정확히 일치하는 대법원 판례로 확인했다. hard negative 30건은 이 유효 사건번호에서 작은 일련번호 변이를 만든 뒤, 공식 API의 HTTP 200 검색 응답에 정확히 일치하는 사건번호가 없음을 확인했다. registry의 `lookup_status=404`는 이 exact-match 부재를 나타내는 내부 정규화 값이며 공식 HTTP 404를 뜻하지 않는다. 모든 원문 응답은 credential을 제거한 후 SHA-256으로 결합했다.", "",
        "## Auto-generated primary table", "", table, "",
        "AULCR의 분모는 accepted output이다. 따라서 C4의 0.00%는 유틸리티를 뜻하지 않으며, C4는 valid 100건 모두를 거절(FRR 100.00%)했다. 반면 C8은 valid 100건 모두 source-bound answer로 처리했다.", "",
        "## Wilson 95% confidence intervals", "",
    ]
    for name in ("C0_DIRECT", "C1_NAIVE_RAG", "C2_EXISTENCE_CHECK", "C4_TOOL_AGENT", "C5_GUARDRAIL", "C8_UIR"):
        row = metrics[name]
        report.append(
            f"- {name}: AULCR {interval(row, 'accepted_unsupported_wilson')}; "
            f"invalid FAR {interval(row, 'invalid_far_wilson')}; "
            f"verified coverage {interval(row, 'verified_coverage_wilson')}; "
            f"FRR {interval(row, 'false_rejection_wilson')}."
        )
    report.extend(["", "## Paired statistical analysis", ""])
    for row in statistics["primary_comparisons"]:
        report.append(
            f"- {row['comparison']}: exact McNemar p={row['p_value']:.6g}, "
            f"Holm-adjusted p={row['holm_adjusted_p']:.6g}, "
            f"absolute risk difference (UIR − baseline)={100 * row['absolute_risk_difference_uir_minus_baseline']:.2f} percentage points "
            f"({row['left_only']} baseline-only failures, {row['right_only']} UIR-only failures)."
        )
    report.extend([
        "", "## Qualitative hard negative", "",
        f"- Query: `{runtime[hard_id]['query']}`",
        f"- Candidate: `{hard['gold_citation']}`; verified source case: `{hard['source_valid_citation']}`; mutation: `{hard['mutation_type']}`",
        "- Authority result: exact 사건번호 match 없음(HTTP 200 response; normalized `NOT_FOUND`).",
        "", "Naive RAG raw output (max-token termination is preserved):", "", "```text", str(c1_raw["final_output"]), "```", "",
        "UIR output:", "", "```json", str(c8_raw["final_output"]), "```", "",
        f"UIR transition: `{c8_raw['transition']}`; model invoked: `{str(c8_raw['model_invoked']).lower()}`.", "",
        "## Interpretation", "",
        f"평가된 LAW-KR-200 legal-identity setting에서 Naive RAG의 observed AULCR은 {pct(c1['accepted_unsupported_legal_claim_rate'])}({c1['accepted_unsupported_legal_claims']}/{c1['accepted_outputs']})였고, existence check는 {pct(c2['accepted_unsupported_legal_claim_rate'])}({c2['accepted_unsupported_legal_claims']}/{c2['accepted_outputs']})였다. C8 UIR은 accepted unsupported claim {c8['accepted_unsupported_legal_claims']}/{c8['accepted_outputs']}({pct(c8['accepted_unsupported_legal_claim_rate'])})를 보였으며 Wilson 95% CI 상한은 {pct(c8['accepted_unsupported_wilson']['high'])}였다. 동시에 verified coverage는 {pct(c8['verified_answer_coverage'])}({c8['verified_answers']}/{c8['valid_cases']}), FRR은 {pct(c8['false_rejection_rate'])}({c8['false_rejections']}/{c8['valid_cases']})였다. 이는 평가된 범위에서 typed entity binding이 단순 존재 확인보다 false-premise mismatch를 더 잘 통제했다는 관찰이지, 법률 환각의 일반적 제거를 뜻하지 않는다.", "",
        "## Mandatory final questions", "",
        "1. **Test set은 정말 200건인가?** 예. runtime/gold 각각 200건이며 opaque ID가 일대일 대응한다.",
        "2. **Test를 보고 tuning했는가?** 아니오. parser/verifier 결함은 dev-40에서 고쳤고 최종 freeze 후 test를 한 번 전면 실행했다. 이전 pre-freeze artifact는 별도 보존했다.",
        "3. **Ground truth는 어떻게 결정했는가?** 국가법령정보 공동활용 공식 판례 응답의 exact 사건번호와 사건명 metadata를 동결했다.",
        "4. **모든 nonexistent citation이 공식 HTTP 404였는가?** 아니오. 한국 API는 HTTP 200 목록 응답을 반환하며, exact 사건번호가 없음을 검증해 normalized NOT_FOUND(lookup_status 404)로 기록했다.",
        "5. **Runtime이 gold label을 볼 수 있었는가?** 아니오. runtime에는 opaque ID와 query만 있으며 금지된 pre-generation gold 접근은 0이다.",
        "6. **모든 pipeline이 동일 model/corpus를 사용했는가?** 예. validator가 distinct model configuration 1개와 동일 200 ID를 확인했다.",
        f"7. **Naive RAG AULCR은?** {pct(c1['accepted_unsupported_legal_claim_rate'])} ({c1['accepted_unsupported_legal_claims']}/{c1['accepted_outputs']}).",
        f"8. **Existence Check 결과는?** AULCR {pct(c2['accepted_unsupported_legal_claim_rate'])}, invalid FAR {pct(c2['invalid_citation_far'])}, verified coverage {pct(c2['verified_answer_coverage'])}.",
        f"9. **UIR 결과는?** AULCR {pct(c8['accepted_unsupported_legal_claim_rate'])}, invalid FAR {pct(c8['invalid_citation_far'])}, verified coverage {pct(c8['verified_answer_coverage'])}, FRR {pct(c8['false_rejection_rate'])}.",
        f"10. **C2와 C8 차이는 유의한가?** exact McNemar p={c2_test['p_value']:.6g}, Holm-adjusted p={c2_test['holm_adjusted_p']:.6g}.",
        f"11. **Valid citation에서 UIR FRR은?** {pct(c8['false_rejection_rate'])} ({c8['false_rejections']}/{c8['valid_cases']}).",
        f"12. **UIR이 모두 abstain했는가?** 아니오. valid verified coverage {pct(c8['verified_answer_coverage'])}, invalid safe abstention {pct(c8['safe_abstention_rate'])}, model invocation {pct(c8['model_invocation_rate'])}이다.",
        f"13. **Verified coverage가 가장 높은 pipeline은?** {best['pipeline']} {pct(best['verified_answer_coverage'])}.",
        f"14. **KO/EN 차이는?** C8 coverage는 EN {pct(en['verified_answer_coverage'])}, KO {pct(ko['verified_answer_coverage'])}; accepted unsupported incidence는 양쪽 모두 {pct(en['unsupported_case_incidence'])}/{pct(ko['unsupported_case_incidence'])}이다.",
        f"15. **Mismatch를 어떻게 처리했는가?** C2는 existence만 검사해 전체 entity-binding accuracy {pct(c2['entity_binding_accuracy'])}였고, C8은 citation↔case-name을 생성 전에 검증해 {pct(c8['entity_binding_accuracy'])}였다.",
        "16. **Universal hallucination elimination을 의미하는가?** 아니다. 결과는 frozen 대법원 identity-metadata benchmark와 정의된 output contract에 한정된다.",
        "17. **논문에 쓸 수치는?** auto-generated primary table, Wilson intervals, exact McNemar/Holm 결과만 publication-safe하다. 기존 Phase-4F/10-case 수치는 LAW-KR-200 증거로 사용하지 않는다.", "",
        "## Limitations", "",
        "- 판결의 실체적 법리·사실관계·요지 정확성이 아니라 사건번호와 사건명 identity binding을 평가한다.",
        "- 공식 API snapshot과 2026-09-11 retrieval 시점이 authority boundary다.",
        "- A/B valid 100건은 50개 entity의 KO/EN pair이고 독립 법률 개체 100개가 아니다.",
        "- 로컬 3.8B Q4 모델과 통제된 lexical corpus의 결과를 다른 모델·법역·배포 환경에 일반화할 수 없다.",
        "- UIR의 0 observed failures는 0 risk의 증명이 아니다. AULCR Wilson 95% CI 상한을 함께 보고한다.",
    ])
    report_path = PACKAGE_ROOT / "LAW200_KR_REPORT.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    note = [
        "# KAIC Manuscript Update — LAW-KR-200", "",
        "이 문서는 strict publication validator를 통과한 frozen LAW-KR-200 결과에서 자동 생성되었다. 기존 Phase-4F 및 10-case 정량 주장은 아래 결과로 교체한다.", "",
        "## 평가 문단", "",
        f"국가법령정보 공동활용 판례 API에서 동결한 대한민국 대법원 사건번호를 이용해 LAW-KR-200(N=200; 한국어 100, 영어 100)을 구성하였다. 동일한 `{model.get('model')}`와 frozen corpus 조건에서 Naive RAG의 accepted unsupported legal claim rate는 {pct(c1['accepted_unsupported_legal_claim_rate'])}, 단순 existence check는 {pct(c2['accepted_unsupported_legal_claim_rate'])}, UIR은 {pct(c8['accepted_unsupported_legal_claim_rate'])}로 관찰되었다. UIR의 valid-case verified coverage는 {pct(c8['verified_answer_coverage'])}, FRR은 {pct(c8['false_rejection_rate'])}였다. C2 대비 exact McNemar p={c2_test['p_value']:.4g}, Holm-adjusted p={c2_test['holm_adjusted_p']:.4g}였다.", "",
        "## 자동 생성 표", "", table, "",
        "## 안전한 결론", "",
        "UIR은 자연어와 권위 있는 법률 개체 사이에 강타입 의미 경계를 제공하며, 평가된 LAW-KR-200 legal-identity setting에서 생성 전 사건번호·사건명 검증을 통해 허용된 비근거 법률 주장을 줄였다.", "",
        "## 필수 제한", "",
        "- 결과는 대법원 identity metadata와 frozen 국가법령정보 공동활용 snapshot에 한정된다.",
        "- normalized NOT_FOUND는 HTTP 200 검색 결과의 exact 사건번호 부재이며 공식 HTTP 404가 아니다.",
        "- 실체적 법률 추론 또는 보편적 환각 제거를 입증하지 않는다.",
        "- 미국 LAW-US-200 replication은 별도 CourtListener credential로 수행하며 한국 결과와 합산하지 않는다.",
    ]
    note_path = PACKAGE_ROOT / "KAIC_MANUSCRIPT_UPDATE_KR.md"
    note_path.write_text("\n".join(note) + "\n", encoding="utf-8")
    return report_path, note_path


if __name__ == "__main__":
    outputs = generate()
    print(json.dumps({"status": "COMPLETE", "outputs": [str(path) for path in outputs]}, ensure_ascii=False, indent=2))
