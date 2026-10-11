논문 초안을 SCI 심사 기준으로 검토하려면 본문과 참고문헌을 먼저 전부 읽겠습니다.
본문 후반(수식·실험·결론)을 이어서 읽겠습니다.
실험 주장과 최신 관련 연구를 교차 확인한 뒤, SCI 심사 관점으로 정리하겠습니다.
# SCI 심사 기준 리뷰: HETE / UIR 논문 초안

**총평:** 시스템 아이디어(다국어 frontend → UIR → 정책 엔진 → 사실 주입)는 **엔터프라이즈 온프레미스 SLM**이라는 실용 문제에 잘 맞습니다. 그러나 **현재 형태로는 Q1 SCI 저널에 투고하면 desk-reject 또는 Major Revision 후 사실상 거절 확률이 매우 높습니다.** 이유는 아이디어 부재가 아니라, (1) 주장이 실험이 지탱할 수 있는 범위를 크게 넘고, (2) 2024–2026 관련 연구와 SOTA 베이스라인이 비어 있으며, (3) 0.0% hallucination / 100% fact-consistency가 정의상 거의 자동으로 나오는 측정 설계이기 때문입니다.

현재 원고는 **IEEE 학회 8페이지 포맷(`IEEEtran` conference)** 입니다. SCI 저널은 보통 12–18페이지 분량, 저널 클래스, 재현 자료, 통계적 엄밀성을 요구합니다. 포맷만 바꿔 투고하는 것으로는 통과하지 않습니다.

아래는 **실제 Associate Editor / Reviewer 3인 관점**으로 쓴 심사 리포트와, **통과를 위한 수정 로드맵**입니다.

---

## 1. 심사 점수 (가상 SCI 리뷰어)

| 심사 항목 | 점수 (10) | 한줄 판정 |
|---|---|---|
| 문제 정의 / 동기 | 7 | 온프레미스 SLM + 컴플라이언스는 타당 |
| 참신성 (novelty) | 4 | 컴파일러 은유는 있으나 구성 요소가 기존 기술의 조합 |
| 기술 깊이 / 형식화 | 3 | UIR 의미론·GAT 학습·보장 정리가 없음 |
| 실험 설계 | 3 | strawman 베이스라인, 약한 메트릭, 순환 정의 |
| 관련 연구 | 3 | 2023 이후 핵심 문헌 대거 누락 |
| 주장–증거 정합성 | 2 | “eliminate / 0.0% / SOTA / guarantee” 과잉 |
| 재현성 | 2 | 코드·데이터·하이퍼파라미터·주석 가이드 없음 |
| 글쓰기 / 일관성 | 5 | 영어는 읽히나 수치·인용·범위가 흔들림 |
| **종합 (SCI Q1)** | **3.5 / 10** | **Reject 또는 Very Major Revision** |

통과 가능 저널을 지금 상태로 고르면 **IEEE Access / MDPI 계열** 정도입니다. 목표를 SCI Q1–Q2로 두면 **재실험 + 주장 축소 + 형식화**가 필수입니다.

---

## 2. 심사자가 가장 먼저 칠 치명적 문제 (Fatal)

### F1. “0.0% hallucination”은 발견이 아니라 정의의 산물입니다

Hallucination Rate 정의:

\[
HR = \frac{N_{\text{hallucinated}}}{N_{\text{invalid}}} \times 100\%
\]

즉 **존재하지 않는 ID 300건에서 거절하지 않고 서사를 만든 비율**입니다. HETE는 API가 404이면 LLM을 호출하지 않고 `NO_FACT_FOUND`를 반환합니다. 그러면 HR=0%는 **파이프라인이 그렇게 짜여 있어서** 나옵니다.

심사자 예상 코멘트:

> A 10-line existence check (`if not api.exists(id): return "No Fact Found"`) would also yield HR = 0%. This does not demonstrate that the SLM does not hallucinate.

더 심각한 점:

- Vanilla / Naive RAG가 **invalid 300건에서 100% hallucination**인 것도 부자연스럽습니다. 거절 프롬프트만 넣어도 떨어집니다.
- Abstract는 **1,000건 전체에서 0.0%**처럼 읽히지만, 정의상 HR은 invalid 300건에만 적용됩니다.
- Valid 500건에서 SLM이 `[XAI_FACT]`를 의역·누락·숫자 왜곡할 가능성은 **측정되지 않았습니다.**
- Gaslighting 200건은 정량 표가 없고 예시 1건뿐입니다.

**SCI에서 “hallucination eliminated / guarantee 0%”는 거의 자동 desk-reject 트리거입니다.** 생성 모델에 대한 전칭 보장은 이 실험으로 증명되지 않습니다.

### F2. Fact-Consistency 100%도 메트릭이 과잉 포장입니다

정의: 공식 API 키워드의 **≥ 50%가 출력에 포함**되면 정답.

- 50% 키워드 오버랩은 fact-consistency가 아닙니다.
- 숫자 단위, 부호, 연도, 조문 번호의 정확성을 보지 않습니다.
- 인간 평가, NLI entailment, FActScore, exact numeric match가 없습니다.
- 이 기준으로 100%를 “perfectly accurate summaries”라고 쓴 것은 심사자가 **지적 정직성**을 의심하게 만듭니다.

### F3. Ablation이 ablation이 아닙니다

비교 대상이 Vanilla Phi-3.5와 Naive RAG뿐입니다. 2026년 SCI에서 이것은 strawman입니다.

없는 것:

| 빠져 있는 비교 | 왜 치명적인가 |
|---|---|
| Tool-calling / function calling + JSON schema | 엔티티 검증만으로 HR=0을 재현 가능 |
| Constrained decoding (Outlines, Guidance, LMQL) | UIR의 가장 가까운 경쟁 기술 |
| NeMo Guardrails / semantic rails | 정책 엔진의 직접 경쟁 |
| Self-RAG, CRAG, GraphRAG | “RAG는 probabilistic이라 실패” 주장을 반박하는 SOTA |
| Text-to-SQL / SPARQL / KG-RAG | 구조화 IR의 표준 대안 |
| 더 큰 모델 + tools (GPT-4o, Claude) | 온프레미스 이점이 품질 희생인지 보여야 함 |
| HETE 내부 ablation (UIR only / Policy only / GAT only) | contribution이 어디서 나오는지 모름 |

지금 표는 “존재 확인을 안 한 RAG는 가짜 ID에 속는다”만 보여 줍니다. 그건 이미 알려진 사실입니다.

### F4. GATv2 attention을 “mathematical causality”로 부르는 것은 학계에서 바로 거절됩니다

XBRL calculation linkbase는 이미

\[
\text{Parent} = \sum_j w_j \cdot \text{Child}_j,\quad w_j \in \{+1,-1\}
\]

인 **회계 항등식**입니다. 영업이익 YoY 변동의 주원인은

\[
j^* = \arg\max_j \lvert w_j \cdot \Delta v_j \rvert
\]

같은 **기여도 분해**로  deterministically 나옵니다. GAT가 왜 필요한지 설명이 없습니다.

추가로:

- Attention ≠ causality (Jain & Wallace 2019 이후 표준 비판).
- GAT를 **학습했는지, 손실은 무엇인지, 분할·에폭·시드가 무엇인지** 전혀 없습니다.
- 학습하지 않은 GAT의 \(\alpha=0.7894\)는 의미가 없습니다.
- 예시 1개의 소수점 4자리 숫자는 cherry-pick으로 읽힙니다.
- Legal DAG에 대한 수식·실험이 사실상 없습니다. 금융 예시만 있습니다.

심사자는 “GAT는 불필요한 복잡성(complexity theater)”이라고 쓸 가능성이 큽니다.

### F5. Related Work가 2020년 이전에 머물러 있습니다

현재 인용은 RAG(Lewis 2020), hallucination survey, GAT, LLVM, QA-GNN 수준입니다. **이 논문이 차별화해야 할 바로 그 문헌이 없습니다.**

반드시 넣고 차이를 명시해야 하는 것:

- **Hallucination 평가:** SelfCheckGPT, FActScore, TruthfulQA, HaluEval, semantic entropy
- **구조화/제약 생성:** LMQL, Guidance, Outlines, JSON schema / tool use
- **가드레일:** NeMo Guardrails, constitutional classifiers
- **에이전트:** ReAct, Toolformer, Program-of-Thoughts, PAL, DSPy
- **그래프 RAG:** GraphRAG, KG-RAG, QA-GNN 이후 후속
- **뉴로심볼릭 LLM 2024–2025:** systematic review (예: Colelough & Regli 2025), logic-constrained decoding
- **의미 파싱:** Text-to-SQL, semantic parsing (Dong & Lapata는 2016 ACL인데 bib가 2019/잘못된 저널)
- **다국어/한국어:** 형태소 분석 기반 NLU, cross-lingual semantic parsing
- **XBRL/재무:** FinQA, ConvFinQA, TAT-QA, 최근 FinReflectKG-HalluBench류

Related Work가 약하면 심사자는 “저자들이 필드를 모른다”고 결론 내립니다.

---

## 3. 방법론·형식화 문제 (Major)

### M1. UIR이 “Universal Compiler IR”로 성립하지 않습니다

식 (1)

\[
UIR = \mathcal{T}_{KO}(Q_{KO}) \equiv \mathcal{T}_{EN}(Q_{EN})
\]

은 수학이 아닙니다. 동치 관계의 정의역·치역·불변량이 없습니다.

부족한 것:

- UIR의 **형식 문법 (BNF)과 조작적 의미론**
- 파서 **커버리지**: 문법 밖 문장 비율, parse exact-match, slot F1
- 한국어 조사/어미 렉서가 실제로 처리하는 구문 범위 (관계절, 이중 부정, 경어, 생략)
- 영어 frontend가 `EXECUTE  ON {ID} FROM [DOMAIN] GIVEN (NL)` 패턴이면, 이는 DSL이지 자연어가 아님
- `condition_tree`는 본문에 나오나 스키마 표에 없음
- KO/EN + LAW/FINANCE만 있으면 Universal이 아님 → 이름을 축소해야 함

LLVM 비유는 직관적이지만, regex + kiwipiepy + Pydantic은 컴파일러 이론 기여로 인정받기 어렵습니다. **시스템 아키텍처 기여**로 재포장하는 것이 정직합니다.

### M2. Zero-trust / prompt-injection “보장”이 실험으로 뒷받침되지 않습니다

- L0가 injection을 어떻게 탐지하는지 알고리즘이 없습니다 (키워드? 휴리스틱?).
- AdvBench, GCG, jailbreak 벤치마크가 없습니다.
- 정책 엔진이 UIR 위에서 돈다면, **파서를 우회하는 자연어**가 핵심 공격면인데 이 평가가 없습니다.
- NIST Zero Trust를 차용한 용어는 보안 심사자에게 오히려 마이너스입니다. 실측 없이 쓰면 overclaim입니다.

### M3. 데이터셋이 재현 불가능합니다

- “synthesized 1,000 pairs” vs Abstract의 “real-world” — 모순입니다.
- 생성 프로토콜, 템플릿, 중복 제거, 인간 검증, IAA(κ)가 없습니다.
- 실제 판례/XBRL ID 목록, 라이선스, 공개 여부가 없습니다.
- 동일 백본, 단일 시드, 분산·신뢰구간이 없습니다.
- 카테고리 불균형(valid 500 / invalid 300 / gaslight 200)이 평균 latency를 HETE에 유리하게 만듭니다. Invalid는 50ms에 거절되므로 **평균 5.38s는 구성 효과**입니다.

### M4. Latency 비교가 불공정하고 수치도 내부 불일치입니다

| 위치 | Naive RAG 대비 감소 |
|---|---|
| Abstract / Contributions | **69.7%** |
| Evaluation 본문 | **66.1%** |

계산: \(1 - 5383/15892 \approx 66.1\%\). Abstract가 틀렸습니다.

또한 Vanilla(20.7s)가 RAG(15.9s)보다 느린 이유를 길이가 다른 출력으로 통제하지 않았습니다. **쿼리 유형별 latency, TTFT, 생성 토큰 수 정규화**가 필요합니다.

### M5. 국방/C4ISR 섹션은 근거 없는 scope creep입니다

실험은 법률 인용 + XBRL입니다. 전술 좌표·ROE·보급 DAG는 한 줄도 없습니다. SCI 심사자는 “grant language / 과장비”로 읽습니다. **Discussion에서 한 문단 전망으로 축소**하거나, 실제 프록시 실험을 넣으십시오.

### M6. 재현성·연구윤리

- 코드/데이터/모델 카드 없음
- Figure에 `language_router.py` 같은 구현 파일명이 들어가 저널 톤이 아님
- Phi-3.5를 Phi-3 기술보고서로 인용
- Vaswani 2017을 hallucination 근거로 인용 (해당 논문은 hallucination을 다루지 않음)
- bib 오류: Dong & Lapata 연도/저널, Yasunaga 페이지, Dettmers2023의 year=2022, `et al.` 남용
- 한글 주석, `kotex`, 중복 `\usepackage{tikz,url}` — 투고본 완성도가 낮음

---

## 4. 잘된 점 (유지할 자산)

심사에 남을 **실제 기여 후보**는 다음 네 가지입니다. 주장을 여기에 맞추십시오.

1. **언어 비대칭을 IR로 분리** — 교착어(한국어 조사/어미) vs 분석어 프롬프트를 같은 실행 스키마로 내리는 시스템 설계.
2. **LLM 호출 전 hard gate** — 환각을 “생성 후 탐지”하지 않고 **컴파일/검증 단계에서 차단**하는 아키텍처 (아이디어는 유효, 실험이 약함).
3. **온프레미스 8GB 제약** — 실용 설정은 저널보다 응용 저널에서 강점.
4. **XBRL 계산 그래프를 설명 가능한 근거로 주입** — GAT가 아니라 **구조화 재무 그래프 grounding**으로 재정의하면 설득력이 생깁니다.

이 네 가지를 “환각 0% 제거 이론”이 아니라 **constrained neuro-symbolic execution for bilingual enterprise agents**로 쓰는 것이 SCI 전략입니다.

---

## 5. SCI를 통과하려면: 수정 로드맵

우선순위를 P0(필수) → P2(있으면 가산)로 나눕니다. P0를 안 고치면 Q2 이상 통과는 비현실적입니다.

### P0 — 주장·측정·실험 재설계 (가장 중요)

**1) 제목·Abstract·기여 문장에서 절대 표현 삭제**

권장 재포장:

- 삭제: `Hallucination-Eliminated`, `guarantees`, `0.0%`, `SOTA`, `zero-trust execution 보장`
- 대체 예:  
  *“HETE: A Bilingual Neuro-Symbolic Compiler that Grounds On-Premise SLM Agents on a Typed Intermediate Representation and Verifiable Domain Graphs”*

Abstract는 다음만 주장하십시오.

- invalid entity에 대해 **거절 재현율 / false-accept**
- valid entity에 대해 **수치·인용 exact match, 인간 Likert, FActScore**
- 파서 커버리지와 정책 위반 탐지율
- latency는 **유형별**로

**2) 메트릭을 학계 표준으로 교체**

| 현상 | 쓸 메트릭 |
|---|---|
| 가짜 ID | Refusal rate, false-accept, false-reject (valid를 거절하는 비용) |
| 사실성 | FActScore 또는 atomic fact precision, **숫자 exact match**, citation exact match |
| 환각(생성 단계) | SelfCheckGPT / NLI contradiction vs source |
| Gaslighting | 잘못된 전제를 **정정/거절/수용**한 3-way 분류 정확도 (200건 전부) |
| 파서 | Intent/slot EM, 언어별, OOD 문장 |
| 정책 | precision/recall per L0–L3, 우회 공격 성공률 |
| 효율 | 유형별 latency, tokens/s, VRAM peak, 통계(평균±표준편차, 최소 3 시드) |

**3) 진짜 ablation (최소 이 표가 있어야 함)**

같은 Phi-3.5 백본으로:

1. Vanilla  
2. Naive RAG  
3. RAG + “ID must exist” 툴  
4. Structured output / JSON schema only  
5. UIR parser only  
6. UIR + Policy (no GAT)  
7. UIR + 결정적 기여도 분해 (no GAT)  
8. UIR + GATv2  
9. Full HETE  

여기서 **(3)과 (6)이 Full과 HR이 같으면**, 핵심 기여는 GAT/UIR이 아니라 existence check입니다. 그 결과를 숨기지 말고 논문의 중심으로 쓰십시오. 정직한 논문이 더 잘 붙습니다.

**4) 베이스라인 4개 이상 추가**

최소: GraphRAG 또는 KG-RAG, tool-calling agent, NeMo Guardrails(또는 동등 rails), constrained decoding. 가능하면 GPT-4o-mini tool agent를 “클라우드 상한선”으로.

### P0 — GATv2를 살리거나 버리십시오 (중간은 불가)

선택지 A (추천): GAT를 **본 기여에서 내리고**, XBRL 계산식을 따른 **결정적 기여도/반사실 분해**를 XAI로 사용. Attention 인과 주장은 삭제. 훨씬 방어하기 쉽습니다.

선택지 B: GAT를 유지하려면

- 학습 목표 (예: 인간 주석 원인 vs attention alignment, 또는 다음 기 예측)
- 데이터 분할, 베이스라인 (GCN, GraphSAGE, 단순 |\Deltav|)
- attention faithfulness 테스트 (edge perturbation, ROAR류)
- 법률 그래프는 별도 실험이 없으면 문장에서 빼기

**Attention weight = root-cause probability** 문장은 어떤 선택지에서도 쓰면 안 됩니다.

### P0 — UIR을 형식화

저널이 기대하는 최소 형식:

- JSON 스키마가 아니라 **문법 + 타입 시스템**
- \(\mathcal{T}_L\)의 불변량: 같은 의도 쌍 \((Q_{KO}, Q_{EN})\)에 대해 UIR equality를 **측정** (bilingual parallel 200쌍)
- 실패 모드: underspecified query, nested conditions, 다중 엔티티
- 한국어 형태소 분석 오류가 downstream에 미치는 영향

“Universal”은 `Bilingual Domain IR (BDIR)` 등으로 낮추는 것이 안전합니다.

### P1 — Related Work 전면 재작성 + 포지셔닝 한 문단

표 하나:

| 시스템 | 다국어 IR | 실행 전 hard gate | 도메인 그래프 근거 | 온프레미스 SLM |
|---|---|---|---|---|
| Naive RAG | × | × | × | △ |
| GraphRAG | × | × | ○ | △ |
| Guardrails | × | △ (생성 후/중) | × | ○ |
| Tool agent | × | ○ (툴) | △ | △ |
| **HETE** | ○ | ○ (compile-time) | ○ | ○ |

이 표가 있어야 “조합이지만 빈칸을 채운다”는 novelty 서사가 됩니다.

### P1 — 데이터·코드 공개

SCI Q1은 사실상 필수에 가깝습니다.

- 프롬프트 템플릿, 라벨 가이드, 합성 스크립트
- 공개 가능한 판례 ID / 미국 인용은 CourtListener, 국내는 개인정보 없는 사건번호 체계만
- XBRL는 DART/SEC 공개 보고서
- 파서·정책 엔진 코드 (모델 가중치는 HuggingFace 링크)

비공개면 최소한 **anonymous supplementary with 100-example sample**이라도 넣으십시오.

### P1 — 통계·공정 비교

- 쿼리 유형별 표 (지금은 평균이 HETE에 유리)
- 3 seed 이상, Wilcoxon 또는 bootstrap CI
- 출력 길이 정규화 latency
- 인간 평가: 도메인 주석자 ≥2, Cohen’s κ
- Error analysis 1절: 파서 실패, API 허위 양성, SLM이 fact를 왜곡한 사례

### P2 — 저널 포맷·글쓰기

- `\documentclass{IEEEtran}` conference → 목표 저널 클래스
- 한글 주석·kotex 제거 (영문 저널이면)
- 국방 절 삭제 또는 2–3문장 future work
- 수치 일치 (66.1 vs 69.7)
- Algorithm의 깨진 `If ... then` 정리
- 아키텍처 그림에서 `.py` 파일명 제거
- 인용 전수 점검 (저자 전체, 정확한 venue)
- Contribution을 4개가 아니라 **2개로 줄이기** (bilingual IR + compile-time grounding). GAT와 8GB는 supporting result.

---

## 6. 목표 저널 추천 (정직하게)

지금 상태 그대로:

- Q1 TNNLS / TKDE / TPAMI / NeurIPS 저널급 → **거의 불가능**
- Knowledge-Based Systems, ESWA, Information Sciences → **Major 후 거절 가능**
- IEEE Access, Applied Sciences → 통과 가능하나 SCI 임팩트 기대와 다를 수 있음

P0를 수행한 뒤의 현실적 타깃:

| 타깃 | 조건 | 적합성 |
|---|---|---|
| **Knowledge-Based Systems** (Q1) | 형식화된 IR, 강한 응용 실험, 공개 데이터 | 가장 잘 맞음 |
| **Expert Systems with Applications** | 엔터프라이즈 케이스, 인간 평가, 실무 한계 명시 | 잘 맞음 |
| **IEEE Trans. on Artificial Intelligence** | 가드레일·에이전트 포지션, SOTA 베이스라인 | 가능 |
| **Information Fusion** | 뉴럴+심볼릭+그래프 fusion을 전면에 | 가능 |
| **ACM TIST** | 시스템+평가가 두꺼울 때 | 가능 |
| IEEE TNNLS | GAT를 진짜 학습 기여로 키우지 않으면 비추천 | 낮음 |
| ACL/EMNLP 저널 트랙 | 파서·다국어 평가가 핵심일 때만 | 중간 |

**한 줄 전략:** *환각 이론 논문이 아니라, 이중언어 엔터프라이즈 에이전트를 위한 typed IR + 실행 전 검증 시스템 논문*으로 투고하십시오.

---

## 7. 권장 논문 골격 (저널 버전)

대략 14–16페이지:

1. Introduction — 과잉 주장 없이, 실패 사례 1개(가짜 판례번호)로 동기
2. Related Work — 위 표 중심
3. Problem formulation — 입력 공간, 허용 출력, safety property (예: unverifiable entity ⇒ refuse)
4. UIR specification — 문법, 타입, 언어별 frontend, 병렬 동치 실험
5. Policy engine — L0–L3를 규칙의 시맨틱으로, 공격면 분석
6. Grounding module — **결정적 그래프 기여도** (± GAT는 ablation)
7. SLM as renderer — 제약의 한계(렌더링 환각)를 정직히
8. Experiments — 데이터, 메트릭, 베이스라인, ablation, 인간평가, 오류분석, 효율
9. Limitations — 구조화 지식 의존, 파서 커버리지, 생성 단계 환각 잔존
10. Conclusion — “eliminate” 없이

Safety property 예시는 이런 수준이면 저널이 좋아합니다.

> **Unverifiable-entity refusal:** If `target_id` is not validated by the authoritative API, the system returns a typed error and never invokes the SLM.  
> 이것은 guarantee로 쓸 수 있습니다. “모든 hallucination = 0”은 쓸 수 없습니다.

---

## 8. 최종 판정

| 질문 | 답 |
|---|---|
| 아이디어가 쓸모없는가? | 아닙니다. 온프레미스 SLM + 한국어 비대칭 + 실행 전 게이트는 쓸 만한 시스템 기여입니다. |
| 지금 원고가 SCI Q1을 통과하는가? | **아니요.** 과잉 주장, 순환 메트릭, strawman 베이스라인, GAT 인과 오해, 관련연구 공백이 동시에 있습니다. |
| 무엇이 통과를 가르는가? | **주장을 10%로 줄이고 실험을 3배로 늘리는 것.** 특히 existence-check 베이스라인과 생성 단계 사실성 평가. |
| 최소 추가 실험량 | 병렬 KO–EN 200쌍 파서 평가, 내부 ablation 8조건, SOTA 베이스라인 3–4개, 인간평가 200건, gaslighting 200건 전수 정량화, 유형별 latency. |

원하시면 다음 턴에서 바로 **(a) 저널용 제목·Abstract·Contribution 재작성**, **(b) 실험 프로토콜/메트릭 섹션 초안**, **(c) Related Work 삽입용 문헌 리스트** 중 하나를 원고 문장 수준으로 만들어 드리겠습니다.