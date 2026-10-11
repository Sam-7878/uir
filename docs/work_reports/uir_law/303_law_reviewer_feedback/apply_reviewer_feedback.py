"""Apply the KAIC reviewer feedback to a copy of the #0025 manuscript.

The source manuscript and frozen LAW-KR-200 evidence remain unchanged.
"""
from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree

HERE = Path(__file__).resolve().parent
PAPERS = HERE.parents[2] / "papers/_47_2_UIR_Law"
SOURCE = PAPERS / "2026-09-19_#0025_UIR_KAIC2026_kr_LAW200_updated.docx"
OUTPUT = PAPERS / "2026-09-19_#0026_UIR_KAIC2026_kr_LAW200_REVIEWER_REVISED.docx"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
Q = lambda local: f"{{{W}}}{local}"


def paragraph_text(node) -> str:
    return "".join(node.xpath(".//w:t/text()", namespaces=NS))


def set_text(node, value: str) -> None:
    spans = node.xpath(".//w:t", namespaces=NS)
    if not spans:
        raise ValueError("No text run available for style-preserving replacement")
    spans[0].text = value
    spans[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    for span in spans[1:]:
        span.text = ""


def replace_para(body, prefix: str, value: str) -> None:
    matches = [
        node for node in body
        if node.tag == Q("p") and paragraph_text(node).startswith(prefix)
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one paragraph beginning {prefix!r}, found {len(matches)}")
    set_text(matches[0], value)


def build() -> Path:
    with ZipFile(SOURCE) as source:
        root = etree.fromstring(source.read("word/document.xml"))
        body = root.find(".//w:body", NS)

        replace_para(
            body,
            "대규모 언어모델(LLM)",
            "대규모 언어모델(LLM) 기반 법률 검색은 사용자의 의도와 검증된 사실 권위를 분리하지 않아 잘못된 판례 identity를 생성에 전달할 수 있다. 본 논문은 한·영 질의를 강타입 의미 계약으로 정규화하고 사건번호–사건명 identity를 생성 전에 동결된 공식 정보원과 결합하는 Universal Intermediate Representation(UIR)을 제안한다. LAW-KR-200(N=200; 한·영 각 100)에서 KO–EN canonical equivalence는 100/100이었고, UIR은 유효 A/B 100건을 모두 verified path로, C/D 100건을 모두 safe outcome으로 routing하면서 FRR 0/100을 유지했다. Accepted unsupported legal claim은 0/100(0.00%; Wilson 95% CI [0.00%, 3.70%])이었다. 핵심 실증은 생성 차단 자체보다 자연어 질의를 올바른 verification branch로 정규화·결합하면서 valid identity coverage를 보존했는지에 있다.",
        )

        replace_para(
            body,
            "우리가 사용한 Dataset인 LAW-KR-200은",
            "LAW-KR-200은 국가법령정보 공동활용 오픈API에서 동결한 대법원 사건번호–사건명 metadata로 valid(A), surface variation(B), hard negative(C), mismatch(D) 각 50질의를 구성했다. 한·영 100쌍은 동일 underlying entity를 공유했고 canonical UIR 동등성은 100/100이었다. Dev 40건과 test 200건을 분리해 Direct LLM을 포함한 6개 pipeline을 동일 Phi-3.5-mini-instruct와 frozen corpus에서 비교했다(표 1은 주요 5개). NOT_FOUND는 HTTP 200 응답 내 exact 사건번호 부재를 정규화한 것이다. Accepted Unsupported Legal Claim Rate(AULCR)는 ANSWER/CORRECT로 수용한 출력 중 frozen authoritative identity metadata로 지지되지 않는 법률 주장을 포함한 출력의 비율이며, 분모는 전체 200질의가 아니라 pipeline별 accepted output 수다.",
        )

        replace_para(
            body,
            "표 2. 범주별 올바른 결과",
            "표 2. Semantic canonicalization 및 identity binding의 범주별 결과(A/B: verified, C: safe reject, D: safe outcome).",
        )

        replace_para(
            body,
            "표 1에서 AULCR은",
            "표 1의 AULCR은 Naive RAG 80/83(96.39%), Existence Check 98/142(69.01%), UIR 0/100(0.00%; Wilson 95% CI [0.00%, 3.70%])이었다. Tool Agent의 0/1은 valid 100건 전부를 거절한 결과이며, 사후 citation·name·evidence allow-list인 Guardrail도 AULCR 75.61%, FRR 84%였다. 더 중요한 표 2에서 UIR은 A/B 100건을 모두 verified path로 처리하고 C/D 100건을 모두 safe outcome으로 처리했다. 반면 Existence Check의 올바른 결과는 surface variation에서 25/50, mismatch에서 19/50이었다. 이는 본 benchmark에서 UIR의 이점이 단순 존재 확인이 아니라 semantic canonicalization과 identity binding에 있음을 보여준다. NOT_FOUND/MISMATCH 경로는 설계상 모델을 호출하지 않으므로 그 경로의 생성 차단은 구조적 특성이다. 따라서 평가는 0% 자체보다 질의를 올바른 UIR 상태와 verification branch로 routing하면서 valid coverage와 FRR을 유지하는지를 검증한다.",
        )

        replace_para(
            body,
            "UIR은 의도와 사실 권위를 분리하는",
            "UIR은 의도와 사실 권위를 분리하는 강타입 runtime 경계다. 본 결과는 생성 차단 자체의 효과보다, 자연어 질의를 typed UIR로 canonicalize하고 올바른 verification branch에 routing하면서 valid identity coverage를 유지할 수 있음을 보여준다.",
        )

        replace_para(
            body,
            "결과는 2026-09-11 동결",
            "결과는 2026-09-11 동결 대법원 identity metadata, 한·영 100쌍 및 단일 3.8B 모델에 한정되며 법리 추론이나 보편적 환각 제거를 의미하지 않는다. 단일 frozen snapshot을 권위 경계로 사용해 다중 정보원 불일치와 source outage도 평가하지 않았다. 향후 Qwen3 등 다양한 공개 LLM에서 모델 독립성을 검증하고, UIR semantic representation과 모델 내부 표현의 결합이 sample·parameter efficiency에 미치는 영향을 평가할 예정이다. 또한 미국 판례, code generation 및 biomedical entity grounding으로 domain을 확장하고 multi-authority·legacy RDB 연계를 연구한다.",
        )

        text = "".join(root.xpath(".//w:t/text()", namespaces=NS))
        required = (
            "올바른 verification branch",
            "surface variation에서 25/50",
            "mismatch에서 19/50",
            "설계상 모델을 호출하지 않으므로",
            "Qwen3 등 다양한 공개 LLM",
            "code generation 및 biomedical entity grounding",
        )
        for phrase in required:
            assert phrase in text, phrase
        forbidden = (
            "exact McNemar",
            "Holm-adjusted",
            "accepted-unsupported event",
            "근거없는 요청 수용",
            "소스 중단장애",
            "우리가 사용한 Dataset",
        )
        for phrase in forbidden:
            assert phrase not in text, phrase

        updated = etree.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True
        )
        with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as target:
            for item in source.infolist():
                data = updated if item.filename == "word/document.xml" else source.read(item.filename)
                target.writestr(item, data)
    return OUTPUT


if __name__ == "__main__":
    print(build())
