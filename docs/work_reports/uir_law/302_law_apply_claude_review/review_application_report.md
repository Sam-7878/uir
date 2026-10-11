# KAIC 2026 review 반영 결과

## 산출물

- 논문: `../../../papers/_47_2_UIR_Law/2026-09-19_#0023_UIR_KAIC2026_kr_LAW200_KR_REVIEWED.docx`
- 발표자료: `../../../papers/_47_2_UIR_Law/2026-09-19_#0024_UIR_KAIC2026_Oral_Presentation_REVIEWED.pptx`
- 범주별 원시 결과 재집계: `category_breakdown.json`, `category_breakdown.md`
- 재현 스크립트: `category_breakdown.py`, `revise_manuscript.py`, `revise_presentation.py`

원본 DOCX/PPTX, frozen dataset, raw generation, scorer, registered protocol은 수정하지 않았다. 새로운 실험이나 튜닝은 하지 않았다.

## 주요 반영 사항

- 논문 저자·이메일 각주를 기존 superscript 서식으로 바로잡고, AULCR의 정식 명칭·분모(각 pipeline의 accepted output)를 표 1 앞에서 정의했다.
- 논문 표 1의 내부 C-label을 제거하고 C5의 사후 citation/name/evidence allow-list, Dahl 관련연구 대비, 단일 frozen authority의 한계를 명시했다. 별도 related-work 절이나 대폭 늘린 참고문헌은 추가하지 않았다.
- 원시 출력에서 자동 재집계한 표 2를 넣었다. A/B는 verified answer, C는 safe rejection, D는 safe outcome으로 구분했다. C/D에는 FRR을 적용하지 않았다.
- 발표자료의 AULCR 오기, FAR 범위, C1/C4/C5 구현 설명, 한국 API의 HTTP 200 exact-match 부재와 frozen snapshot semantics, 과장된 안전성 표현을 수정했다. 발표자 노트도 측정 범위에 맞췄다.

| 범주별 올바른 결과 | Existence Check | Guardrail | UIR |
|---|---:|---:|---:|
| A: verified answer | 8/50 | 0/50 | 50/50 |
| B: verified answer | 25/50 | 8/50 | 50/50 |
| C: safe rejection | 50/50 | 33/50 | 50/50 |
| D: safe outcome | 19/50 | 44/50 | 50/50 |

D의 Existence Check 19건은 REJECT/CLARIFY 8건과 source-bound CORRECT 11건이다. 따라서 이를 모두 “mismatch detection”이라고 부르지 않고 “safe outcome”으로 표기했다.

작업지시서의 C4 “accepted output 0건” 설명은 frozen raw와 일치하지 않았다. 실제 accepted output은 1건(D의 supported correction)이므로 발표자료에 **AULCR 0/1, valid FRR 100/100**으로 표기했다. 0%를 안전성 우월성의 독립 증거로 해석하지 않았다.

## 검증

- `category_breakdown.py`가 runtime/gold/source/corpus hash를 manifest와 대조하고, raw 재채점 행을 frozen scored 행과 정확히 일치시켰다. Test runtime SHA-256: `e728fae81590f640e52e9174a72e238d00a550870c8cb6b0178b04e60d0efc21`.
- `.venv`에서 Python 스크립트를 실행했다. 최종 DOCX/PPTX의 ZIP/OOXML 구조 및 필수 문구 검사를 통과했다.
- LibreOffice 렌더링: 논문 A4 **2쪽**, 발표자료 **16장**. 논문 전 페이지와 발표자료 전 슬라이드 및 수정 후 주요 슬라이드를 시각 점검했다. QA PDF는 `qa/2026-09-19_#0023_UIR_KAIC2026_kr_LAW200_KR_REVIEWED.pdf`, `qa/deliverable/2026-09-19_#0024_UIR_KAIC2026_Oral_Presentation_REVIEWED.pdf`에 있다.
- 최종 Word/PowerPoint 자체 렌더링은 별도로 수행하지 않았다. 제출 전 학회 지정 Office 환경에서 페이지 나눔과 글꼴 대체를 한 번 더 확인하는 것이 좋다.
