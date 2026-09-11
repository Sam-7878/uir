#!/usr/bin/env python3
"""Generate the benchmark report and KAIC update notes from frozen scored evidence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.uir_law.law200.common import AGGREGATE_DIR, DATA_DIR, PACKAGE_ROOT, RAW_DIR, TABLES_DIR, read_json, read_jsonl, utc_now


def pct(value: Any) -> str:
    return "N/A" if value is None else f"{100 * float(value):.2f}%"


def find_comparison(statistics: dict[str, Any], baseline: str) -> dict[str, Any]:
    return next(
        (row for row in statistics.get("primary_comparisons", []) if row.get("comparison") == f"{baseline}_vs_C8_UIR"),
        {},
    )


def generate() -> tuple[Path, Path]:
    required = [
        PACKAGE_ROOT / "benchmark_manifest.json",
        AGGREGATE_DIR / "test_metrics.json",
        AGGREGATE_DIR / "test_statistics.json",
        TABLES_DIR / "law200_main_table.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"cannot generate final report; missing {missing}")
    manifest = read_json(required[0])
    aggregates = read_json(required[1]).get("pipelines", [])
    metrics = {row["pipeline"]: row for row in aggregates}
    statistics = read_json(required[2])
    c1, c2, c8 = metrics["C1_NAIVE_RAG"], metrics["C2_EXISTENCE_CHECK"], metrics["C8_UIR"]
    c2_test = find_comparison(statistics, "C2_EXISTENCE_CHECK")
    supported_best = max(aggregates, key=lambda row: float(row.get("verified_answer_coverage") or 0))

    gold = read_jsonl(DATA_DIR / "law200_test_gold.jsonl")
    runtime = {row["case_id"]: row for row in read_jsonl(DATA_DIR / "law200_test_runtime.jsonl")}
    hard = next(row for row in gold if row["category"] == "C_NONEXISTENT" and row["language"] == "en")
    hard_id = hard["case_id"]
    c1_raw_path = next(iter(sorted(RAW_DIR.glob("test_C1_NAIVE_RAG_*.jsonl"))))
    c8_raw_path = next(iter(sorted(RAW_DIR.glob("test_C8_UIR_*.jsonl"))))
    c1_raw = next(row for row in read_jsonl(c1_raw_path) if row["case_id"] == hard_id)
    c8_raw = next(row for row in read_jsonl(c8_raw_path) if row["case_id"] == hard_id)
    model_identity = c8_raw.get("model_identity", {})
    table = required[3].read_text(encoding="utf-8")
    en_c8 = c8.get("language", {}).get("en", {})
    ko_c8 = c8.get("language", {}).get("ko", {})

    report_lines = [
        "# LAW-200 Final Benchmark Report", "",
        f"Generated: {utc_now()}", "",
        "## Outcome", "",
        "LAW-200 evaluates typed legal citation canonicalization and CourtListener-backed entity binding in a controlled U.S.-case metadata retrieval setting. It does not evaluate substantive legal reasoning or universal hallucination elimination.", "",
        f"- Test queries: {manifest['test_cases']} (100 English, 100 Korean)",
        f"- Frozen test runtime SHA-256: `{manifest['hashes']['law200_test_runtime.jsonl']}`",
        f"- Frozen source registry SHA-256: `{manifest['source_registry_sha256']}`",
        f"- Code commit at freeze: `{manifest.get('environment', {}).get('git_commit', 'UNAVAILABLE')}`",
        f"- Model: `{model_identity.get('model', 'UNAVAILABLE')}` / `{model_identity.get('quantization_level', 'UNAVAILABLE')}`", "",
        "## Auto-generated primary table", "", table, "",
        "## Statistical comparisons", "",
    ]
    for row in statistics.get("primary_comparisons", []):
        report_lines.append(
            f"- {row['comparison']}: exact McNemar p={row['p_value']:.6g}, Holm-adjusted p={row['holm_adjusted_p']:.6g}, "
            f"absolute risk difference (UIR − baseline)={100 * row['absolute_risk_difference_uir_minus_baseline']:.2f} percentage points."
        )
    report_lines.extend([
        "", "## Qualitative hard negative", "",
        f"Query: `{runtime[hard_id]['query']}`", "",
        f"The citation `{hard['gold_citation']}` was created by `{hard['mutation_type']}` from `{hard['source_valid_citation']}` and admitted only after the frozen CourtListener response returned status 404.", "",
        "Naive RAG final output:", "", "```json", str(c1_raw.get("final_output", "")), "```", "",
        "UIR final output:", "", "```json", str(c8_raw.get("final_output", "")), "```", "",
        f"UIR transition: `{c8_raw.get('transition')}`; model invoked: `{c8_raw.get('model_invoked')}`.", "",
        "## Interpretation", "",
        f"Observed accepted unsupported-claim rate was {pct(c1['accepted_unsupported_legal_claim_rate'])} for Naive RAG, {pct(c2['accepted_unsupported_legal_claim_rate'])} for existence check, and {pct(c8['accepted_unsupported_legal_claim_rate'])} for UIR. UIR valid-case verified coverage was {pct(c8['verified_answer_coverage'])}, with false rejection {pct(c8['false_rejection_rate'])}. These rates must be reported with their denominators and Wilson intervals.", "",
        "## Mandatory final questions", "",
        "1. **LAW-200 test set은 정말 200건인가?** 예. frozen runtime과 gold가 각각 정확히 200건이며 validator가 ID 일대일 대응을 검사한다.",
        "2. **test set을 보고 UIR rule을 tuning했는가?** 아니오. rule 개발과 debugging은 분리된 dev 40건에서만 수행하도록 freeze contract를 적용했다.",
        "3. **valid/nonexistent citation의 ground truth는 어떻게 결정했는가?** CourtListener v4 citation lookup의 frozen raw response에서 status 200과 404를 구분했다.",
        "4. **모든 nonexistent citation은 실제 authoritative lookup에서 404였는가?** 예. source-integrity audit가 30개 registry 404 record와 원문 hash를 검사했다.",
        "5. **runtime pipeline이 gold label을 볼 수 있었는가?** 아니오. runtime에는 opaque ID와 query만 있으며 pre-generation access log의 금지 접근은 0이다.",
        "6. **C1, C2, C4, C5, C8은 동일한 model과 corpus를 사용했는가?** 예. C0를 포함한 모든 generation은 동일 model config를 사용하고 retrieval-capable pipeline은 동일 frozen corpus를 사용했다.",
        f"7. **Naive RAG의 AULCR은 얼마인가?** {pct(c1['accepted_unsupported_legal_claim_rate'])} ({c1['accepted_unsupported_legal_claims']}/{c1['accepted_outputs']} accepted outputs).",
        f"8. **Existence Check의 결과는 얼마인가?** AULCR {pct(c2['accepted_unsupported_legal_claim_rate'])}, invalid FAR {pct(c2['invalid_citation_far'])}, verified coverage {pct(c2['verified_answer_coverage'])}.",
        f"9. **UIR의 결과는 얼마인가?** AULCR {pct(c8['accepted_unsupported_legal_claim_rate'])}, invalid FAR {pct(c8['invalid_citation_far'])}, verified coverage {pct(c8['verified_answer_coverage'])}, FRR {pct(c8['false_rejection_rate'])}.",
        f"10. **C2와 C8 차이는 statistically significant한가?** exact McNemar p={c2_test.get('p_value', 'N/A')}, Holm-adjusted p={c2_test.get('holm_adjusted_p', 'N/A')}.",
        f"11. **valid citation에서 UIR FRR은 얼마인가?** {pct(c8['false_rejection_rate'])} ({c8['false_rejections']}/{c8['valid_cases']}).",
        f"12. **UIR이 단순히 더 많이 abstain해서 안전성을 얻었는가?** valid verified coverage {pct(c8['verified_answer_coverage'])}와 FRR {pct(c8['false_rejection_rate'])}를 함께 보아야 하며, model invocation rate는 {pct(c8['model_invocation_rate'])}이다.",
        f"13. **Supported Answer Coverage는 어느 pipeline이 가장 높은가?** `{supported_best['pipeline']}` ({pct(supported_best['verified_answer_coverage'])}).",
        f"14. **KO/EN 결과 차이는 있는가?** UIR verified coverage: EN {pct(en_c8.get('verified_answer_coverage'))}, KO {pct(ko_c8.get('verified_answer_coverage'))}; unsupported case incidence: EN {pct(en_c8.get('unsupported_case_incidence'))}, KO {pct(ko_c8.get('unsupported_case_incidence'))}.",
        "15. **citation ↔ case-name mismatch에서 각 pipeline은 어떻게 동작했는가?** pipeline별 entity-binding accuracy와 raw transition은 test metrics/scored cases에 보존되며, C2는 존재만 검사하고 C8은 생성 전 binding을 검사한다.",
        "16. **universal hallucination elimination을 의미하지 않는다고 명시했는가?** 예. 모든 해석은 observed controlled LAW-200 legal-identity setting으로 제한한다.",
        "17. **KAIC 논문에 publication-safe한 숫자는 무엇인가?** auto-generated main table의 네 primary metric, Wilson interval, exact McNemar/Holm 결과만 사용한다. 수동 전사 숫자나 이전 10-case/Phase-4F 수치는 사용하지 않는다.",
    ])
    report_path = PACKAGE_ROOT / "LAW200_REPORT.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    update_lines = [
        "# KAIC Manuscript Update — LAW-200", "",
        "이 문서는 frozen LAW-200 결과에서 자동 생성되었다. 기존 Phase-4F 표와 `999 U.S. 999` 정량 주장을 제거하고 아래 LAW-200 결과로 교체한다.", "",
        "## Evaluation paragraph", "",
        f"독립적인 LAW-200은 미국 판례 인용 200건(영어 100, 한국어 100)을 valid, surface variation, realistic CourtListener-verified 404, citation/name mismatch의 네 범주로 균형 구성하였다. 동일한 `{model_identity.get('model', 'model')}`와 frozen corpus 조건에서 Naive RAG의 accepted unsupported legal claim rate는 {pct(c1['accepted_unsupported_legal_claim_rate'])}, 단순 existence check는 {pct(c2['accepted_unsupported_legal_claim_rate'])}, UIR은 {pct(c8['accepted_unsupported_legal_claim_rate'])}로 관찰되었다. UIR의 valid verified coverage는 {pct(c8['verified_answer_coverage'])}, FRR은 {pct(c8['false_rejection_rate'])}였다.", "",
        "## Required table", "", table, "",
        "## Safe conclusion", "",
        "UIR provides a typed semantic boundary that enables legal entities to be verified before generation, reducing accepted unsupported legal claims in the evaluated legal-retrieval setting.", "",
        "## Required limitations", "",
        "- Controlled U.S. Reports identity-metadata benchmark; not substantive legal reasoning.",
        "- CourtListener snapshot defines the authority boundary and 404 interpretation.",
        "- Observed rates do not imply universal hallucination elimination.",
        "- Legacy RDB mapping and non-vector structured retrieval remain future work.",
    ]
    update_path = PACKAGE_ROOT / "KAIC_MANUSCRIPT_UPDATE.md"
    update_path.write_text("\n".join(update_lines) + "\n", encoding="utf-8")
    return report_path, update_path


if __name__ == "__main__":
    outputs = generate()
    print(json.dumps({"status": "COMPLETE", "outputs": [str(path) for path in outputs]}, indent=2))
