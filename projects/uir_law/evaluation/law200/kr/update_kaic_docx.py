#!/usr/bin/env python3
"""Create a LAW-KR-200-updated KAIC manuscript copy via native OOXML."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from evaluation.uir_law.law200.common import REPO_ROOT, read_json
from evaluation.uir_law.law200.kr.validate_publication_results import KR_AGGREGATE_DIR, validate
from evaluation.uir_law.law200.update_kaic_docx import (
    append_reference,
    pct,
    replace_paragraph,
    update_table,
)

SOURCE = REPO_ROOT / "docs" / "papers" / "_47_2_UIR_Law" / "2026-09-11_#0011_UIR_KAIC2026_kr.docx"
OUTPUT = SOURCE.with_name(SOURCE.stem + "_LAW200_KR.docx")


def update(source: Path = SOURCE, output: Path = OUTPUT) -> Path:
    gate = validate()
    if gate["status"] != "READY_FOR_KAIC_MANUSCRIPT_KR":
        raise RuntimeError("LAW-KR-200 publication validator did not pass; DOCX update prohibited")
    metrics = {
        row["pipeline"]: row
        for row in read_json(KR_AGGREGATE_DIR / "test_metrics.json")["pipelines"]
    }
    stats = read_json(KR_AGGREGATE_DIR / "test_statistics.json")
    c1, c2, c8 = (metrics[name] for name in ("C1_NAIVE_RAG", "C2_EXISTENCE_CHECK", "C8_UIR"))
    c2_test = next(row for row in stats["primary_comparisons"] if row["comparison"] == "C2_EXISTENCE_CHECK_vs_C8_UIR")
    c8_ci = c8["accepted_unsupported_wilson"]

    abstract = (
        "대규모 언어모델(LLM) 기반 법률 검색에서 자연어 프롬프트는 사용자의 의도와 사실 권위를 구조적으로 분리하지 않아 검증되지 않은 판례 식별자가 생성 단계로 전달될 수 있다. 본 논문은 다국어 요청을 강타입 의미 계약으로 정규화하고 법률 개체를 생성 전에 권위 소스와 결합하는 Universal Intermediate Representation(UIR)을 제안한다. "
        f"국가법령정보 공동활용 판례 API에서 동결한 대한민국 대법원 사건번호 기반 LAW-KR-200(N=200; 한국어 100, 영어 100) 평가에서 accepted unsupported legal claim rate는 Naive RAG {pct(c1['accepted_unsupported_legal_claim_rate'])}%, 단순 existence check {pct(c2['accepted_unsupported_legal_claim_rate'])}%, UIR {pct(c8['accepted_unsupported_legal_claim_rate'])}%로 관찰되었다. UIR의 valid-case verified coverage는 {pct(c8['verified_answer_coverage'])}%, false rejection rate는 {pct(c8['false_rejection_rate'])}%였다. 이 결과는 평가된 법률 개체 identity 범위에서 생성 전 typed binding이 비근거 주장의 허용을 줄일 수 있음을 보여준다."
    )
    method = (
        "LAW-KR-200은 국가법령정보 공동활용 판례 API에서 동결한 대한민국 대법원 사건번호를 사용한다. Test 200건은 valid, surface variation, 실제 사건번호의 작은 변이 후 exact-match 부재를 확인한 hard negative, 사건번호–사건명 mismatch의 네 범주로 균형 구성했으며 한국어와 영어가 각각 100건이다. 별도 dev 40건으로 개발을 분리했고 모든 baseline은 동일한 Phi-3.5 설정과 frozen authoritative metadata corpus를 사용했다. 한국 API의 NOT_FOUND는 HTTP 200 목록 응답에서 exact 사건번호가 없음을 검증한 정규화 결과이다."
    )
    example = (
        "정성 사례로 실제 판례 2026두30944의 일련번호를 변이한 2026두30951을 질의했다. 공식 snapshot의 HTTP 200 검색 결과에는 정확히 일치하는 사건번호가 없었다. Naive RAG는 검색된 다른 사건 2026두31165를 ANSWER로 출력했지만, UIR은 {domain=LAW, intent=SUMMARIZE, entity_type=CASE, citation=2026두30951}로 정규화하고 NOT_FOUND를 반환하여 모델 호출 전에 기권했다."
    )
    result = (
        f"표 1은 frozen LAW-KR-200 test 결과이다. Naive RAG의 AULCR은 {pct(c1['accepted_unsupported_legal_claim_rate'])}%({c1['accepted_unsupported_legal_claims']}/{c1['accepted_outputs']}), existence check는 {pct(c2['accepted_unsupported_legal_claim_rate'])}%({c2['accepted_unsupported_legal_claims']}/{c2['accepted_outputs']}), UIR은 {pct(c8['accepted_unsupported_legal_claim_rate'])}%({c8['accepted_unsupported_legal_claims']}/{c8['accepted_outputs']})였다. UIR의 Wilson 95% CI는 [{pct(c8_ci['low'])}%, {pct(c8_ci['high'])}%]이며, C2 대비 exact McNemar p={c2_test['p_value']:.3g}, Holm-adjusted p={c2_test['holm_adjusted_p']:.3g}였다. UIR의 verified coverage {pct(c8['verified_answer_coverage'])}%와 FRR {pct(c8['false_rejection_rate'])}%를 함께 보면 이 결과는 전면 거절로 얻은 것이 아니다."
    )
    related = (
        "LegalBench-RAG는 법률 RAG의 검색 정밀도를 독립적인 병목으로 다루며[4], 상징 제약 연구는 authoritative source 결합의 가치를 보인다[5]. UIR은 런타임 요청을 강타입 계약으로 정규화하여 검색·검증·정책·모델 backend가 같은 법률 개체를 공유하게 한다. 본 평가는 국가법령정보 공동활용 판례 API[6]를 authority boundary로 사용한다."
    )
    limitation = (
        "현재 결과는 frozen 국가법령정보 공동활용 snapshot의 대법원 사건번호–사건명 identity metadata와 통제된 로컬 3.8B 모델에 한정되며, 실체적 법률 추론이나 보편적 환각 제거를 의미하지 않는다. UIR에서 관찰된 0건의 accepted unsupported claim도 0 risk의 증명이 아니므로 Wilson 신뢰구간과 함께 해석해야 한다. 향후에는 별도 CourtListener 기반 미국 판례 replication, structured legal database와 legacy RDB mapping 및 agent–RDB orchestration을 연구할 예정이다."
    )

    with ZipFile(source) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
        replace_paragraph(root, "대규모 언어모델", abstract)
        replace_paragraph(root, "통제된 프로토타입에서는", method + " " + example)
        replace_paragraph(root, "표 1. 통제된 baseline 비교", "표 1. Frozen LAW-KR-200 법률 인용 검증 결과(N=200).")
        replace_paragraph(root, "표 1은 최종 matched", result)
        replace_paragraph(root, "최근 법률 AI 연구에서도", related)
        replace_paragraph(root, "현재 결과는 controlled", limitation)
        update_table(root, metrics)
        append_reference(root, "[6] 법제처 국가법령정보센터, ‘국가법령정보 공동활용 판례 목록 API,’ accessed Sep. 11, 2026.")
        updated_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(suffix=".docx", dir=output.parent)
        os.close(fd)
        temp = Path(temp_name)
        try:
            with ZipFile(temp, "w", ZIP_DEFLATED) as target:
                for item in archive.infolist():
                    target.writestr(item, updated_xml if item.filename == "word/document.xml" else archive.read(item.filename))
            os.replace(temp, output)
        finally:
            if temp.exists():
                temp.unlink()
    return output


if __name__ == "__main__":
    path = update()
    print(json.dumps({"status": "COMPLETE", "output": str(path)}, ensure_ascii=False, indent=2))
