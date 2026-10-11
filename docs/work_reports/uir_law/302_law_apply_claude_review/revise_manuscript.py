"""Apply the bounded KAIC review edits to a copy of the template DOCX.

The source file, frozen benchmark artifacts, and Word style definitions are not edited.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree

HERE = Path(__file__).resolve().parent
PAPERS = HERE.parents[2] / "papers/_47_2_UIR_Law"
SOURCE = PAPERS / "2026-09-11_#0013_UIR_KAIC2026_kr_LAW200_KR_FINAL.docx"
OUTPUT = PAPERS / "2026-09-19_#0023_UIR_KAIC2026_kr_LAW200_KR_REVIEWED.docx"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
Q = lambda local: f"{{{W}}}{local}"


def paragraph_text(node) -> str:
    return "".join(node.xpath(".//w:t/text()", namespaces=NS))


def set_text(node, value: str) -> None:
    spans = node.xpath(".//w:t", namespaces=NS)
    if not spans:
        raise ValueError("No existing text run to preserve")
    spans[0].text = value
    spans[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    for span in spans[1:]:
        span.text = ""


def replace_para(body, prefix: str, value: str):
    matches = [p for p in body if p.tag == Q("p") and paragraph_text(p).startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one paragraph beginning {prefix!r}, found {len(matches)}")
    set_text(matches[0], value)
    return matches[0]


def replace_superscript_runs(body, prefix: str, values: list[str]) -> None:
    para = next(p for p in body if p.tag == Q("p") and paragraph_text(p).startswith(prefix))
    superscript = [
        r for r in para.findall("./w:r", NS)
        if r.find("./w:rPr/w:vertAlign", NS) is not None
        and r.find("./w:rPr/w:vertAlign", NS).get(Q("val")) == "superscript"
    ]
    if len(superscript) != len(values):
        raise ValueError((prefix, len(superscript), values))
    for run, value in zip(superscript, values, strict=True):
        spans = run.findall(".//w:t", NS)
        if len(spans) != 1:
            raise ValueError("Unexpected author-run topology")
        spans[0].text = value


def category_table(source_table, breakdown: dict):
    table = copy.deepcopy(source_table)
    grid = table.find("./w:tblGrid", NS)
    for column in list(grid)[3:]:
        grid.remove(column)
    for column, width in zip(grid, (1430, 1490, 1490), strict=True):
        column.set(Q("w"), str(width))
    rows = table.findall("./w:tr", NS)
    for row in rows[5:]:
        table.remove(row)
    rows = table.findall("./w:tr", NS)
    labels = ["Category", "Exist. Check", "UIR"]
    names = ["A Valid", "B Surface", "C Hard Neg.", "D Mismatch"]
    categories = ("A_VALID", "B_SURFACE_VARIATION", "C_NONEXISTENT", "D_ENTITY_MISMATCH")
    for index, row in enumerate(rows):
        cells = row.findall("./w:tc", NS)
        for cell in cells[3:]:
            row.remove(cell)
        cells = row.findall("./w:tc", NS)
        if index == 0:
            values = labels
        else:
            category = categories[index - 1]
            values = [names[index - 1]]
            for pipeline in ("C2_EXISTENCE_CHECK", "C8_UIR"):
                counts = breakdown["pipelines"][pipeline][category]
                values.append(f"{counts['safe_outcome']}/50 ({2 * counts['safe_outcome']:.0f}%)")
        for cell, value, width in zip(cells, values, (1430, 1490, 1490), strict=True):
            set_text(cell, value)
            tc_width = cell.find("./w:tcPr/w:tcW", NS)
            if tc_width is not None:
                tc_width.set(Q("w"), str(width))
    return table


def build() -> Path:
    breakdown = json.loads((HERE / "category_breakdown.json").read_text(encoding="utf-8"))
    assert breakdown["pipelines"]["C2_EXISTENCE_CHECK"]["D_ENTITY_MISMATCH"]["safe_outcome"] == 19
    assert breakdown["pipelines"]["C8_UIR"]["D_ENTITY_MISMATCH"]["safe_outcome"] == 50
    with ZipFile(SOURCE) as source:
        root = etree.fromstring(source.read("word/document.xml"))
        body = root.find(".//w:body", NS)

        # Preserve the template's superscript run formatting; correct only its text.
        replace_superscript_runs(body, "박성수", ["1", "1,*"])
        replace_superscript_runs(body, "SeongSu Park", ["1", "1,*"])
        for prefix in ("parky@ajou.ac.kr",):
            email_paras = [p for p in body if p.tag == Q("p") and paragraph_text(p).startswith(prefix)]
            assert len(email_paras) == 2
            for para in email_paras:
                super_runs = [r for r in para.findall("./w:r", NS) if r.find("./w:rPr/w:vertAlign", NS) is not None]
                assert len(super_runs) == 2
                super_runs[0].find(".//w:t", NS).text = ""
                super_runs[1].find(".//w:t", NS).text = "*"
                ordinary = [r for r in para.findall("./w:r", NS) if r.find("./w:rPr/w:vertAlign", NS) is None]
                for run in ordinary:
                    spans = run.findall(".//w:t", NS)
                    if len(spans) == 1 and spans[0].text in (" ", "  "):
                        spans[0].text = ""
                runs = para.findall("./w:r", NS)
                comma = next(i for i, run in enumerate(runs) if "".join(run.xpath(".//w:t/text()", namespaces=NS)) == ",")
                runs[comma + 1].find(".//w:t", NS).text = " "

        replace_para(body, "대규모 언어모델(LLM)",
            "법률 검색에서 자연어 프롬프트는 요청 의도와 사실 권위를 분리하지 않아 잘못된 판례 식별자를 생성에 전달할 수 있다. 본 논문은 한국어·영어 요청을 강타입 UIR로 정규화하고 사건번호–사건명 identity를 생성 전에 동결된 공식 정보원과 결합한다. LAW-KR-200(200질의; 한·영 각 100)에서 근거 없는 법률 주장 수용은 Naive RAG 80/83, existence check 98/142, UIR 0/100이었다. UIR의 AULCR은 0.00%(Wilson 95% CI [0.00%, 3.70%]), valid-query source-bound coverage는 100%, FRR은 0%였다. 이는 평가된 판례 identity 범위의 관찰이며 실체적 법률 추론 정확도를 뜻하지 않는다.")
        replace_para(body, "LLM은 법률 연구의", 
            "LLM 법률 검색은 존재하지 않는 판례 식별자나 근거 없는 주장을 생성할 수 있다[3]. RAG가 외부 근거를 결합해도[2], 검색 대상의 identity가 틀리면 잘못된 개체를 답할 수 있다[4], [5]. ‘2026두30951을 요약하라’에는 정상적 요약 의도와 미검증 사건번호가 함께 있다. 프롬프트만으로 그 번호에 사실 권위를 부여해서는 안 된다.")
        replace_para(body, "본 논문은 자연어 상호작용과", 
            "본 논문은 컴파일러 IR에서 착안한[1] 강타입 UIR을 제안한다. 기여는 (1) 한·영 질의의 의미 정규화, (2) 생성 전 사건번호–사건명 결합 검증, (3) 검증 실패의 명시적 기권 처리이다.")
        replace_para(body, "UIR의 핵심 원칙은", 
            "UIR의 원칙은 Prompt ≠ Authority이다. 프롬프트는 의도를 전하지만 사건의 존재나 identity를 확정하지 않는다. 일반 UIR은 <Domain, Intent, Entity, Parameters, Constraints, Output>이며, 법률 projection은 {source_lang, jurisdiction=KR, intent, entity_type=CASE, case_id, claimed_name, constraints}를 쓴다. 언어가 달라도 동일한 법률 개체로 정규화된다.")
        replace_para(body, "UIR은 schema/type", 
            "Schema·type 검증과 식별자 정규화 후 동결된 국가법령정보 공동활용 snapshot에서 사건번호와 사건명을 생성 전에 대조한다. VERIFIED만 exact retrieval과 모델 생성으로 진행하며 NOT_FOUND/MISMATCH는 모델 호출 없이 기권한다. 출력 계약은 citation·case name·source ID의 결합을 확인한다.")
        replace_para(body, "LegalBench-RAG는", 
            "Dahl 등은 법률 환각을 측정·분석한다[3]. LegalBench-RAG는 검색 정밀도를 평가하고[4], symbolic constraint 연구는 선례 검색과 제약을 결합한다[5]. 반면 UIR은 생성 전 typed entity binding을 수행하는 runtime 표현 계층이다. 본 평가는 국가법령정보 공동활용 판례 API[6]를 권위 경계로 삼는다.")
        replace_para(body, "LAW-KR-200은", 
            "LAW-KR-200은 동결된 대법원 사건번호–사건명 metadata로 valid(A), surface variation(B), hard negative(C), mismatch(D) 각 50질의를 구성했다. 한·영 100쌍은 동일 underlying entity를 공유하며 canonical UIR 동등성은 100/100이었다. Dev 40건과 test 200건을 분리하고 Direct LLM을 포함한 6개 pipeline을 동일 Phi-3.5-mini-instruct와 frozen corpus에서 비교했다(표 1은 주요 5개). 한국 API의 NOT_FOUND는 HTTP 200 응답 내 exact 사건번호 부재를 정규화한 것이다. Accepted Unsupported Legal Claim Rate(AULCR)는 ANSWER/CORRECT로 수용한 출력 중 frozen authoritative identity metadata로 지지되지 않는 법률 주장을 포함한 출력의 비율이다. 분모는 전체 200질의가 아니라 pipeline별 accepted output 수다.")
        replace_para(body, "표 1. LAW-KR-200", "표 1. LAW-KR-200 주요 pipeline 결과(N=200 질의).")
        replace_para(body, "AULCR은 accepted output", 
            "표 1에서 AULCR은 Naive RAG 80/83(96.39%), Existence Check 98/142(69.01%), UIR 0/100(0.00%; Wilson 95% CI [0.00%, 3.70%])이었다. Tool Agent는 0/1이나 valid 100건 모두 거절(FRR 100%)했다. 사후 citation·name·evidence allow-list인 Guardrail은 AULCR 75.61%, FRR 84%로 identity 오류와 utility 손실을 함께 해결하지 못했다. UIR의 valid source-bound coverage는 100%, FRR은 0%였다. 공통 200질의의 case-level accepted-unsupported endpoint에서 Existence Check 98건 대 UIR 0건이었다(exact McNemar p=6.31e-30; Holm-adjusted p=1.89e-29). 표 2는 범주별 올바른 결과를 보인다.")
        replace_para(body, "UIR은 법률 LLM 통합을", 
            "UIR은 의도와 사실 권위를 분리하는 강타입 runtime 경계다. Existence Check는 번호만 확인하지만, UIR은 의미 정규화·생성 전 identity binding·exact retrieval·출력 계약을 결합해 평가 범위에서 근거 없는 법률 주장 수용을 낮추면서 valid identity coverage를 유지했다.")
        replace_para(body, "결과는 2026-09-11에", 
            "결과는 2026-09-11 동결 대법원 identity metadata, 한·영 100쌍 및 로컬 3.8B 모델에 한정되며 법리 추론이나 보편적 환각 제거를 의미하지 않는다. 단일 국가법령정보 공동활용 snapshot을 권위 경계로 사용해 다중 정보원 불일치·source outage는 평가하지 않았다. 0건의 accepted unsupported claim은 0 risk의 증명이 아니다. 향후 source unavailability와 multi-authority conflict의 fail-closed 동작, 미국 판례 replication 및 legacy RDB 연계를 평가한다.")

        tables = [x for x in body if x.tag == Q("tbl")]
        assert len(tables) == 2
        main = tables[1]
        for row, label in zip(main.findall("./w:tr", NS)[1:],
                              ("Naive RAG", "Existence Check", "Tool Agent", "Guardrail", "UIR (Ours)"), strict=True):
            set_text(row.find("./w:tc", NS), label)

        category = category_table(main, breakdown)
        caption = copy.deepcopy(next(p for p in body if p.tag == Q("p") and paragraph_text(p).startswith("표 1.")))
        set_text(caption, "표 2. 범주별 올바른 결과(A/B: verified, C: safe reject, D: safe outcome).")
        after_main = list(body).index(main) + 1
        body.insert(after_main, caption)
        body.insert(after_main + 1, category)

        for prefix in ("Ⅰ.", "Ⅱ.", "Ⅲ.", "Ⅳ."):
            heading = next(p for p in body if p.tag == Q("p") and paragraph_text(p).startswith(prefix))
            properties = heading.find("./w:pPr", NS)
            if properties is None:
                properties = etree.Element(Q("pPr"))
                heading.insert(0, properties)
            if properties.find("./w:keepNext", NS) is None:
                properties.append(etree.Element(Q("keepNext")))

        text = "".join(root.xpath(".//w:t/text()", namespaces=NS))
        for invalid in ("박성수o1", "김기형21", "parky@ajou.ac.kro", "근거없는 요청 수용", "accepted-unsupported event", "\ufffe", "\ufffd"):
            assert invalid not in text, invalid
        assert "Accepted Unsupported Legal Claim Rate(AULCR)" in text
        assert "단일 국가법령정보 공동활용 snapshot" in text
        updated = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as target:
            for item in source.infolist():
                target.writestr(item, updated if item.filename == "word/document.xml" else source.read(item.filename))
    return OUTPUT


if __name__ == "__main__":
    print(build())
