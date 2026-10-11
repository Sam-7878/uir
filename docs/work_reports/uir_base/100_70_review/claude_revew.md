# SCI급 저널 투고 관점 심사 리뷰 — "HETE: Multi-Lingual Neuro-Symbolic Compiler Framework using UIR"

아래는 IEEE Access / Expert Systems with Applications / Information Fusion / IEEE TNNLS 급 저널의 리뷰어 관점에서 작성한 심사 의견입니다.

---

## 1. 종합 판정

**현 상태로 투고 시 예상 결과: Reject 또는 Major Revision (거절 확률 우세)**

| 항목 | 평가 | 비고 |
|---|---|---|
| 참신성(Novelty) | 中 | UIR+정책엔진 조합은 신선하나, 개별 요소(DSL 파싱, GAT, 가드레일)는 기존 기술 |
| 기술적 엄밀성 | **下** | 최대 약점. 검증 불가능한 수치, 실험 설계 결함 |
| 실험 설계 | **下** | 합성 데이터 자체 제작, 베이스라인 부실, 통계 검정 없음 |
| 재현성 | **下** | 코드/데이터 미공개, 하이퍼파라미터 부재, GATv2 학습 절차 미기술 |
| 문헌 조사 | **下** | 참고문헌 ~15편. SCI 저널 기준 최소 40~60편 필요 |
| 형식 | 中 | IEEEtran conference 템플릿(8p) — 저널 포맷 아님 |

핵심 진단: **"이 논문은 좋은 시스템 논문이지만, 아직 과학 논문이 아닙니다."** 즉 엔지니어링 구현은 설득력 있으나, 주장(claim)을 뒷받침하는 검증 체계가 리뷰어를 통과할 수준이 아닙니다.

---

## 2. 치명적 문제 (Reject 사유가 되는 것들)

### ① "0.0% Hallucination / 100.0% Fact-Consistency" — 가장 위험한 주장
리뷰어는 이 숫자를 보는 순간 **회의적 모드**로 전환합니다.

- **동어반복(tautology) 문제**: 존재하지 않는 ID를 API 조회 → 404 → 차단. 이건 "환각 제거"가 아니라 **정의상 당연한 결과**입니다. 즉 HR=0%는 시스템의 성취가 아니라 평가 지표 설계의 산물입니다. 리뷰어는 반드시 이렇게 지적합니다: *"The 0% hallucination rate is trivially guaranteed by the evaluation protocol, not by the method."*
- **FC 지표가 너무 관대**: "ground-truth 키워드 50% 이상 포함"은 사실성 측정이 아니라 키워드 재현율입니다. 이 기준으로 100%가 나온 것은 지표가 헐거움을 뜻합니다.
- **차단된 쿼리 이후의 유용성 미측정**: 시스템이 모든 쿼리를 거부해도 HR=0%입니다. → **False Rejection Rate(과차단율)**가 반드시 필요합니다.

**수정 방향**
- 주장을 "0.0% hallucination"에서 **"0.0% hallucination on out-of-KB entity queries, at the cost of X% false-rejection rate"**로 정직하게 재프레이밍
- 지표 재설계: HR, FC와 함께 **False Rejection Rate, Coverage(응답 가능 비율), Utility-under-constraint** 추가
- FC는 키워드 기반 대신 **FactScore, FActScore/AlignScore, RAGAS(faithfulness/answer relevancy), 또는 human evaluation (2명 이상, Cohen's κ 보고)** 로 교체

### ② 벤치마크 데이터셋의 자체 합성
"1,000 synthesized prompt-response pairs"는 SCI 저널에서 거의 자동 감점입니다. 저자가 만든 데이터에서 저자의 시스템이 100%를 얻는 것은 증거력이 없습니다.

**수정 방향**
- **공개 벤치마크 최소 2개 추가 필수**: TruthfulQA, HaluEval, FELM, RAGTruth, FinQA/TAT-QA(금융), LegalBench/CaseHOLD(법률), KorQuAD/KMMLU(한국어)
- 자체 데이터셋은 **부록 + 공개(Zenodo/HuggingFace DOI)** 로 전환하고, 구축 절차(annotator 수, 지침, 일치도)를 명시

### ③ 베이스라인이 너무 약함
Vanilla SLM과 Naive RAG만으로는 2026년 기준 비교가 성립하지 않습니다. Vanilla가 HR 100%, FC 0%라는 수치 자체가 비현실적으로 보여 신뢰도를 떨어뜨립니다.

**추가해야 할 베이스라인**
- Self-RAG, CRAG (Corrective RAG), FLARE
- GraphRAG / KG-RAG (그래프 기반 — 본 논문의 직접 경쟁자)
- Guardrails 계열: NeMo Guardrails, Guidance/Outlines(제약 디코딩), JSON-schema constrained decoding
- LLM 기반 function calling / tool-use 에이전트 (가장 중요한 대조군 — "GPT-4o에 function calling 시키면 되지 않나?"에 답해야 함)
- SelfCheckGPT (사후 검증 방식)

### ④ GATv2 부분의 과학적 공백 — 가장 심각한 기술적 결함
현재 원고에는 GATv2에 대한 **학습 절차가 전혀 없습니다**.
- 학습 데이터, 손실 함수, 라벨(무엇을 root cause로 지도학습했는가?), epoch, lr, hidden dim, head 수, 학습/검증 분할 — 모두 부재
- **핵심 반박**: XBRL 계산 링크베이스는 이미 결정론적 가감산 구조입니다. 그렇다면 **단순 기여도 분해(Δ 기여율 계산)로 충분**한데 왜 학습된 GNN이 필요한가? 리뷰어는 반드시 묻습니다.
- α = 0.7894를 "78.94%의 부정적 기여"로 해석한 것은 **어텐션 가중치를 인과 기여도로 오독**한 것입니다. Attention ≠ Explanation은 유명한 논쟁(Jain & Wallace 2019, Wiegreffe & Pinter 2019)이며, 이 지적만으로 논문이 거절될 수 있습니다.

**수정 방향 (택1 이상, 반드시 해결)**
1. **어블레이션으로 정당화**: GATv2 vs. 단순 산술 기여도 분해 vs. Shapley value / Integrated Gradients 비교. GATv2가 더 낫다는 증거를 제시
2. **정직한 축소**: "α는 인과성이 아닌 상대적 기여 랭킹의 근사"라고 명시하고, Attention-as-explanation 논쟁을 Related Work에서 인용·논의
3. 가능하면 **Shapley 기반 기여도로 교체**하고 GATv2는 후보 노드 프루닝 용도로 축소

### ⑤ 통계적 유의성 검정 전무
단일 실행 결과만 보고되어 있습니다. **최소 5회 반복, 평균±표준편차, 신뢰구간, 유의성 검정(paired t-test 또는 Wilcoxon), 효과크기** 필요. 지연시간 5,383ms도 분산 없이 제시되어 있습니다.

### ⑥ 수치 불일치 (즉시 수정)
- Abstract/Conclusion: Naive RAG 대비 **"a factor of three"**, Contributions: **"69.7% reduction"**, 본문: **"66.1% reduction"** — 세 곳이 서로 다릅니다. 실제 계산은 (15892−5383)/15892 = **66.1%**. Vanilla 대비는 74.0%가 맞습니다.
- Related Work: "Absence of Hard **Hard-Locking** Mechanisms" — 오타
- 본문 다수의 `"..."` 곧은 따옴표(66.1%, 2.5 GB, 5.38 s 등)가 LaTeX에서 잘못 렌더링됨 → ``...''로 교체
- Figure 아키텍처 TikZ: `injector` 노드의 중괄호 불일치 (`{[XAI\_FACT]}` 닫힘 누락)

---

## 3. 구조·논증 측면의 문제

### 국방/C4ISR 절은 삭제 또는 대폭 축소 권장
Discussion의 "Mission-Critical Applicability: Defense" 절은 **실험적 근거가 전혀 없는 사변(speculation)**입니다. SCI 리뷰어는 "unsupported claims"로 표시하며, 심사자에 따라서는 논문 전체의 신뢰도를 깎습니다. 한 문단으로 줄여 Future Work에 넣으세요.

### 이론적 기여의 부재
"UIR = T_KO(Q_KO) ≡ T_EN(Q_EN)" 이라는 식(1)은 **주장일 뿐 증명이 없습니다**. SCI급에서는 이 부분이 이론적 핵심이 되어야 합니다.

**보강 방향**
- UIR 스키마의 **형식적 정의**(BNF 문법 또는 타입 시스템)
- **의미 보존(semantic preservation) 정리**: 두 프론트엔드의 등가성을 명제화하고, 최소한 커버리지 실험(N개 병렬 KO/EN 쿼리쌍에서 UIR 일치율 %)으로 실증
- 정책 엔진의 **건전성(soundness)/완전성(completeness)** 논의: "L0–L3 위반은 반드시 차단된다(soundness)"를 형식적으로 진술

### 컴파일러 프론트엔드의 취약성 미평가
정규식+형태소 분석 기반 파서는 **자연어 변이에 매우 취약**합니다. 리뷰어의 핵심 질문: *"실제 사용자가 템플릿을 벗어난 문장을 쓰면 어떻게 되는가?"*
→ **파싱 실패율(parse failure rate)**, 문장 변형(paraphrase) 실험(예: 각 쿼리당 5개 패러프레이즈), OOD 쿼리에 대한 동작을 반드시 보고해야 합니다. 이것이 없으면 "잘 짜인 입력에서만 동작하는 시스템"으로 평가됩니다.

### 다국어 주장의 근거 부족
"multi-lingual"을 제목에 넣었으나 KO/EN 2개 언어뿐이고, 언어별 분리 결과(KO vs EN 성능 차이)가 보고되지 않았습니다. 최소한 **언어별 breakdown 표**를 넣고, 가능하면 제3언어(일본어 — 교착어, 중국어 — 고립어)를 추가해 일반화를 보이세요. 불가하면 제목을 "Bilingual" 또는 "Cross-Lingual (Korean–English)"로 정직하게 조정하는 편이 안전합니다.

---

## 4. 문헌·형식 문제

### 참고문헌 (심각)
현재 약 15편. **SCI급 저널은 40~60편 이상**을 기대합니다. 게다가 최신(2024–2026) 핵심 문헌이 거의 없습니다.

**반드시 추가할 영역**
- 환각 서베이: Huang et al. 2025 (ACM TOIS), Zhang et al. "Siren's Song"
- 고급 RAG: Self-RAG (Asai 2024), CRAG (Yan 2024), GraphRAG (Edge 2024), HippoRAG, LightRAG
- 제약 생성: Outlines/Guidance, Grammar-constrained decoding (Geng 2023), NeMo Guardrails (Rebedea 2023)
- 뉴로심볼릭 최신: LINC, Logic-LM (Pan 2023), SatLM, Faithful CoT (Lyu 2023)
- 어텐션 해석 논쟁: Jain & Wallace 2019, Wiegreffe & Pinter 2019, Serrano & Smith 2019
- GNN 설명가능성: GNNExplainer, PGExplainer
- 금융/법률 LLM: FinGPT, BloombergGPT, SaulLM, LegalBench
- 한국어 LLM/형태소: KLUE, KoBERT/KoGPT, Kiwi 논문

### 파일·포맷 문제
- **`references.tex` 파일명 오류**: 내용은 BibTeX 항목인데 확장자가 `.tex`입니다. `\bibliography{references}`는 `references.bib`를 찾으므로 **컴파일 시 참고문헌이 나오지 않습니다.** → `references.bib`로 즉시 개명하세요.
- `\IEEEPARstart`는 `\documentclass[conference]`에서 지원되지 않습니다(journal 클래스 전용). 저널 투고 시 `\documentclass[journal]{IEEEtran}`으로 변경 필요.
- `\usepackage{kotex}` — 한글 주석/문자가 최종본에 남아 있으면 안 됩니다. 영어 본문에서 "대법원 9999다9999" 같은 한글 예시는 로마자 병기 필요.
- `\usepackage{cite}`와 `hyperref` 로드 순서 충돌 가능 — hyperref는 마지막에.
- 8페이지 conference 분량 → 저널은 보통 12~20페이지. **분량이 부족**하며, 위 보강을 하면 자연히 채워집니다.

---

## 5. 저널 선택 전략

| 저널 | IF 대략 | 적합도 | 코멘트 |
|---|---|---|---|
| **IEEE Access** | ~3.4 | ★★★★★ | 현실적 1순위. 시스템 논문에 관대, 리뷰 빠름. 위 ①~⑥만 고쳐도 통과 가능 |
| **Expert Systems with Applications** | ~7.5 | ★★★★ | 응용+실무 지향. 공개 벤치마크와 강한 베이스라인 필수 |
| **Applied Sciences / Electronics (MDPI)** | ~2.5 | ★★★★ | 빠른 게재. 안전한 대안 |
| **Information Fusion** | ~14 | ★★ | 뉴로심볼릭 융합 각도로는 맞으나 현 수준으로는 desk reject 위험 |
| **Knowledge-Based Systems** | ~7.2 | ★★★ | 지식그래프+추론 각도로 적합. 이론적 보강 필수 |
| **IEEE TNNLS / TKDE** | ~10 | ★ | 권장하지 않음. 이론적 신규성 부족 |

**권장 경로**: 먼저 아래 수정 로드맵을 수행 → **IEEE Access** 또는 **Expert Systems with Applications** 투고.

---

## 6. 실행 로드맵 (우선순위순)

### Phase 1 — 반드시 (없으면 거절)
1. `references.tex` → `references.bib` 개명, 문헌 40편 이상으로 확충
2. 수치 불일치(66.1% / 69.7% / 3배) 전면 정정, 오타·따옴표·TikZ 중괄호 수정
3. **공개 벤치마크 2개 이상 추가 실험** (예: HaluEval + FinQA 또는 RAGTruth + LegalBench)
4. **베이스라인 확충**: Self-RAG, GraphRAG, function-calling agent 최소 3개
5. **False Rejection Rate / Coverage 지표 추가** 및 "0% 환각"의 조건부 재프레이밍
6. **5회 반복 실행 + 평균±표준편차 + 유의성 검정**
7. GATv2 **학습 절차 전체 기술** + 단순 산술 기여도 분해와의 어블레이션
8. Attention≠Explanation 논쟁 인용 및 α 해석의 한계 명시

### Phase 2 — 강력 권장 (억셉 확률 크게 상승)
9. 프론트엔드 **강건성 실험**: 패러프레이즈 5종, 파싱 실패율, OOD 쿼리
10. **KO/EN 언어별 결과 분리 보고** + UIR 등가성 실증(일치율 %)
11. UIR 스키마의 **형식 문법(BNF) 정의** 및 정책 엔진 soundness 진술
12. 코드·데이터 **공개 저장소(GitHub + Zenodo DOI)** 개설 후 논문에 명시
13. 국방/C4ISR 절 대폭 축소 → Future Work 한 문단
14. IEEEtran journal 클래스로 전환, 분량 12~16p로 확장

### Phase 3 — 완성도
15. 실패 사례 분석(error analysis) 절 신설 — 리뷰어가 매우 좋아합니다
16. 비용 분석(TCO): 클라우드 LLM API 대비 온프레미스 경제성 정량화
17. 사용자 스터디 또는 도메인 전문가 평가(소규모라도)
18. 영어 professional proofreading

---

## 7. 리뷰어가 던질 가장 아픈 질문 3가지 (미리 답을 준비하세요)

1. **"GPT-4o에 JSON schema + function calling을 쓰면 동일한 보장을 얻을 수 있지 않습니까? 왜 별도 컴파일러가 필요한가요?"**
   → 답: 온프레미스 제약, 결정론적 감사 추적(audit trail), 정책의 코드화·버전관리 가능성. **이를 정량 실험으로 보여야 함.**

2. **"환각 0%는 시스템이 모르는 것을 전부 거부해서 얻은 결과 아닙니까? 유용성은 얼마나 희생되었나요?"**
   → 답: False Rejection Rate와 Coverage 지표로 정면 대응.

3. **"XBRL 링크베이스가 결정론적 산술 구조인데, 학습된 GNN의 어텐션이 산술 기여도보다 나은 이유는 무엇입니까?"**
   → 답: 어블레이션 실험 결과로만 답변 가능.

---

**요약 한 줄**: 아이디어와 시스템은 SCI급 게재 가치가 충분합니다. 문제는 **"0%/100%"라는 과잉 주장, 자체 합성 데이터, 약한 베이스라인, GATv2의 학습·정당화 공백** 네 가지이며, 이 넷을 정직하고 엄밀하게 재작업하면 IEEE Access급은 충분히 통과 가능하다고 봅니다.

필요하시면 ① 수정된 Abstract/Introduction 초안, ② 확충된 `references.bib` 파일, ③ 추가 실험 설계 프로토콜, ④ 컴파일 오류 수정본 `.tex` 중 원하시는 것을 바로 작성해 드리겠습니다.