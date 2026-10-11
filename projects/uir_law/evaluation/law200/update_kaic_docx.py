#!/usr/bin/env python3
"""Create a LAW-200-updated copy of the KAIC DOCX using native OOXML."""
from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from evaluation.uir_law.law200.common import AGGREGATE_DIR, REPO_ROOT, TABLES_DIR, read_json
from evaluation.uir_law.law200.validate_publication_results import validate

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
ET.register_namespace("w", W)

DEFAULT_SOURCE = REPO_ROOT / "docs" / "papers" / "_47_2_UIR_Law" / "2026-09-11_#0011_UIR_KAIC2026_kr.docx"


def text_of(node: ET.Element) -> str:
    return "".join(item.text or "" for item in node.findall(".//w:t", NS))


def set_text(node: ET.Element, value: str) -> None:
    texts = node.findall(".//w:t", NS)
    if not texts:
        run = ET.SubElement(node, f"{{{W}}}r")
        texts = [ET.SubElement(run, f"{{{W}}}t")]
    texts[0].text = value
    for item in texts[1:]:
        item.text = ""


def replace_paragraph(root: ET.Element, begins: str, value: str) -> None:
    for paragraph in root.findall(".//w:p", NS):
        if text_of(paragraph).strip().startswith(begins):
            set_text(paragraph, value)
            return
    raise RuntimeError(f"paragraph not found: {begins}")


def pct(value) -> str:
    return "N/A" if value is None else f"{100 * float(value):.2f}"


def update_table(root: ET.Element, metrics: dict[str, dict]) -> None:
    table = next((table for table in root.findall(".//w:tbl", NS) if "Pipeline" in text_of(table)), None)
    if table is None:
        raise RuntimeError("publication result table not found")
    rows = table.findall("./w:tr", NS)
    if len(rows) < 2:
        raise RuntimeError("result table has no template row")
    grid = table.find("./w:tblGrid", NS)
    if grid is not None:
        columns = grid.findall("./w:gridCol", NS)
        while len(columns) < 5:
            grid.append(copy.deepcopy(columns[-1]))
            columns = grid.findall("./w:gridCol", NS)
    methods = ("C0_DIRECT", "C1_NAIVE_RAG", "C2_EXISTENCE_CHECK", "C5_GUARDRAIL", "C8_UIR")
    while len(rows) < len(methods) + 1:
        table.append(copy.deepcopy(rows[-1]))
        rows = table.findall("./w:tr", NS)
    while len(rows) > len(methods) + 1:
        table.remove(rows[-1])
        rows = table.findall("./w:tr", NS)
    headers = ("Pipeline", "AULCR (%) ↓", "Invalid FAR (%) ↓", "Verified Coverage (%) ↑", "FRR (%) ↓")
    labels = {
        "C0_DIRECT": "C0 Direct SLM", "C1_NAIVE_RAG": "C1 Naive RAG",
        "C2_EXISTENCE_CHECK": "C2 + Existence Check", "C5_GUARDRAIL": "C5 Guardrail",
        "C8_UIR": "C8 UIR (Ours)",
    }
    for row, values in [(rows[0], headers)] + [
        (rows[index + 1], (
            labels[method], pct(metrics[method]["accepted_unsupported_legal_claim_rate"]),
            pct(metrics[method]["invalid_citation_far"]), pct(metrics[method]["verified_answer_coverage"]),
            pct(metrics[method]["false_rejection_rate"]),
        )) for index, method in enumerate(methods)
    ]:
        cells = row.findall("./w:tc", NS)
        while len(cells) < 5:
            row.append(copy.deepcopy(cells[-1]))
            cells = row.findall("./w:tc", NS)
        for cell, value in zip(cells[:5], values, strict=True):
            set_text(cell, value)


def append_reference(root: ET.Element, value: str) -> None:
    body = root.find(".//w:body", NS)
    if body is None:
        raise RuntimeError("document body not found")
    paragraphs = body.findall("./w:p", NS)
    template = next((p for p in reversed(paragraphs) if text_of(p).strip().startswith("[5]")), paragraphs[-1])
    reference = copy.deepcopy(template)
    set_text(reference, value)
    section = body.find("./w:sectPr", NS)
    insert_at = list(body).index(section) if section is not None else len(body)
    body.insert(insert_at, reference)


def update(source: Path = DEFAULT_SOURCE, output: Path | None = None) -> Path:
    gate = validate()
    if gate["status"] != "READY_FOR_KAIC_MANUSCRIPT":
        raise RuntimeError("publication validator did not pass; DOCX update is prohibited")
    aggregates = read_json(AGGREGATE_DIR / "test_metrics.json")["pipelines"]
    metrics = {row["pipeline"]: row for row in aggregates}
    statistics = read_json(AGGREGATE_DIR / "test_statistics.json")
    c1, c2, c8 = metrics["C1_NAIVE_RAG"], metrics["C2_EXISTENCE_CHECK"], metrics["C8_UIR"]
    c2_test = next(row for row in statistics["primary_comparisons"] if row["comparison"] == "C2_EXISTENCE_CHECK_vs_C8_UIR")
    c8_ci = c8["accepted_unsupported_wilson"]
    abstract = (
        "대규모 언어모델(LLM) 기반 법률 검색에서 자연어 프롬프트는 사용자의 의도와 사실 권위를 구조적으로 분리하지 않아, 검증되지 않은 판례 인용이 생성 단계로 전달될 수 있다. 본 논문은 다국어 요청을 강타입 의미 계약으로 정규화하고 법률 개체를 생성 전에 권위 소스와 결합하는 Universal Intermediate Representation(UIR)을 제안한다. "
        f"미국 판례 인용 200건(영어 100, 한국어 100)의 frozen LAW-200 평가에서 accepted unsupported legal claim rate는 Naive RAG {pct(c1['accepted_unsupported_legal_claim_rate'])}%, 단순 existence check {pct(c2['accepted_unsupported_legal_claim_rate'])}%, UIR {pct(c8['accepted_unsupported_legal_claim_rate'])}%로 관찰되었다. UIR의 valid-case verified coverage는 {pct(c8['verified_answer_coverage'])}%, false rejection rate는 {pct(c8['false_rejection_rate'])}%였다. 이 결과는 평가된 법률 개체 검색 범위에서 생성 전 typed binding이 비근거 주장의 허용을 줄일 수 있음을 보여준다."
    )
    evaluation = (
        "LAW-200은 CourtListener citation lookup으로 동결한 미국 판례 인용 200건을 valid, surface variation, 실제 인용에서 변이한 404 hard negative, citation–case-name mismatch의 네 범주로 균형 구성하였다. 각 범주는 영어 25건과 한국어 25건이며, 별도 dev 40건과 test 200건을 분리하였다. 모든 baseline은 동일한 Phi-3.5 모델 설정과 authoritative metadata corpus를 사용했다."
    )
    result = (
        f"표 1은 frozen LAW-200 test 결과이다. Naive RAG의 AULCR은 {pct(c1['accepted_unsupported_legal_claim_rate'])}%, existence check는 {pct(c2['accepted_unsupported_legal_claim_rate'])}%, UIR은 {pct(c8['accepted_unsupported_legal_claim_rate'])}%였다. C2–C8의 exact McNemar p={c2_test['p_value']:.4g}, Holm-adjusted p={c2_test['holm_adjusted_p']:.4g}였다. UIR의 95% Wilson 구간은 [{pct(c8_ci['low'])}%, {pct(c8_ci['high'])}%이며, valid verified coverage {pct(c8['verified_answer_coverage'])}%와 FRR {pct(c8['false_rejection_rate'])}%를 함께 관찰했다. 따라서 안전성은 단순 전면 거절만으로 해석할 수 없다."
    )
    limitation = (
        "현재 결과는 CourtListener snapshot을 권위 경계로 사용하는 미국 판례 identity-metadata 평가에 한정되며, 실체적 법률 추론이나 보편적 환각 제거를 의미하지 않는다. 향후에는 structured legal database와 legacy RDB mapping 및 agent–RDB orchestration을 연구할 예정이다."
    )
    related = (
        "LegalBench-RAG는 법률 RAG의 검색 정밀도를 독립적인 병목으로 다루며[4], 상징 제약 연구는 authoritative source 결합의 가치를 보인다[5]. LAW-200은 CourtListener citation lookup[6]을 동결한 요청 수준의 강타입 계약으로 검색·검증·모델 backend가 동일한 법률 개체를 공유하게 한다."
    )
    with ZipFile(source) as archive:
        document = archive.read("word/document.xml")
        root = ET.fromstring(document)
        replace_paragraph(root, "대규모 언어모델", abstract)
        replace_paragraph(root, "통제된 프로토타입에서는", evaluation)
        replace_paragraph(root, "표 1. 통제된 baseline 비교", "표 1. Frozen LAW-200 법률 인용 검증 결과(N=200).")
        replace_paragraph(root, "표 1은 최종 matched", result)
        replace_paragraph(root, "최근 법률 AI 연구에서도", related)
        replace_paragraph(root, "현재 결과는 controlled", limitation)
        update_table(root, metrics)
        append_reference(root, "[6] Free Law Project, “Citation Lookup and Verification API,” CourtListener REST API v4, accessed Sep. 11, 2026.")
        updated_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        output = output or source.with_name(source.stem + "_LAW200.docx")
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(suffix=".docx", dir=output.parent)
        os.close(fd)
        temp_path = Path(temp_name)
        try:
            with ZipFile(temp_path, "w", ZIP_DEFLATED) as target:
                for item in archive.infolist():
                    target.writestr(item, updated_xml if item.filename == "word/document.xml" else archive.read(item.filename))
            os.replace(temp_path, output)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    return output


if __name__ == "__main__":
    path = update()
    print(json.dumps({"status": "COMPLETE", "output": str(path)}, indent=2, ensure_ascii=False))
