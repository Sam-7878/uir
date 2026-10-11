# UIR 논문 — MDPI SCIE 저널 투고를 위한 수정 작업지시서

- 작성·외부 공고 확인 기준일: **2026-10-11 (Asia/Seoul)**
- 대상 원고: `_47_UIR.tex`
- 참고문헌: `references.bib`
- 목표 논문 유형: **Original Research Article**. 이 문서는 심사·수정 지시서이며, 원고를 문헌고찰 논문(Review)으로 바꾸라는 지시가 아니다.
- 우선 투고 경로: **Electronics / Generative AI, Large Language Models and Their Applications**.
- 대안 경로: **Applied Sciences / Agentic AI and Large Language Models for Applied Intelligent Systems**.
- 현 단계 판단: **투고 전 Major Revision 필요**. 수치 정합성 문제를 해결하지 않은 상태의 제출은 권장하지 않는다.
- 상태 표시: 이 문서에 제시한 신규 실험·인간 검토·코드 산출물은 **수행 지시 사항이지, 이미 수행한 작업이나 확인된 결과가 아니다**.

## 0. 검토 범위와 변경 금지 원칙

### 0.1 실제 확인한 것

LaTeX와 BibTeX 원본을 읽고, 원고 내 정의·표·주장의 일관성 및 인용·교차참조를 정적 점검했다. MDPI 공식 공고의 검색 색인과 저널 공식 imprint를 확인했다. 일부 MDPI 페이지의 실시간 직접 열기는 429/cache 오류로 제한되었으므로, 마감일·참여 저널·APC는 제출 직전 다시 확인한다. Clarivate Master Journal List를 독립적으로 조회·검증한 것은 아니다.

실험 소스코드, 데이터셋, 모델 응답, 로그, manifest, annotation packet, 학습·추론 환경, Phase-4F 재현 패키지는 이번 업로드에 없다. 따라서 “실험이 재현되었다”, “원시 데이터가 진짜임을 검증했다”, “보고 수치가 정확하다”는 판단을 내려서는 안 된다.

### 0.2 원본 고정

| 파일 | SHA-256 |
|---|---|
| `_47_UIR.tex` | `5ac024d585f57e72f38013c907b96efe8ca647e5cbd65b6438f62499e969b006` |
| `references.bib` | `1faf8a3d4aacbeebce5607019a10e67abc9818a0b54215b512f6e4029eb7e0c7` |

아래 줄 번호는 위 해시의 **원본 파일 물리적 줄 번호**를 기준으로 한 탐색용 위치다. 수정 후에는 줄 번호보다 함께 적은 section/label을 우선한다.

### 0.3 모든 작업자에게 적용할 규칙

1. 원본을 덮어쓰지 않는다. 수정 브랜치와 변경 로그를 만든다.
2. 수치·p-value·신뢰구간·모델 실행 결과·사람 평가·DOI·저장소 주소를 만들어 넣지 않는다.
3. 자료가 없으면 `BLOCKED: 필요한 원시 자료와 담당자`를 기록한다. 추정값으로 빈칸을 채우지 않는다.
4. 표와 맞추려고 지표 정의를 사후 변경하지 않는다. 정의가 잘못되었다면 변경 이유, 기존/신규 정의, 전체 조건 재계산 결과를 함께 기록한다.
5. 초록·본문·표·결론은 동일한 최종 evidence manifest에서 생성한다. 유리한 실험 단계의 수치를 조합하지 않는다.
6. UIR, C5, D1에 동일한 평가 규칙을 적용한다. 비-UIR 시스템에만 불리한 파싱·채점 규칙을 적용하지 않는다.
7. 불리한 외부 결과, 동일 안전성을 보이는 C5 결과, annotation 불일치, 신뢰 가정을 삭제하지 않는다.
8. 모델 세션의 레거시 라벨과 실제 모델 selector가 다르면 원본 기록을 보존하고 정정 매핑을 별도로 제공한다.
9. 예시용 합성 데이터를 실측 자료처럼 기술하지 않는다. 익명화·공개 허가가 필요한 자료는 허가 범위에서만 공개한다.
10. 이 문서의 통계 정합성 검사는 **원고가 현재 정의한 동일 표본·동일 사건**이라는 조건하에 적용된다. 다른 사건·표본이면 정의와 전이 과정을 먼저 명시한다.

## 1. 투고 경로와 논문 포지셔닝

### 1.1 추천 경로

| 우선순위 | 저널 / 형식 | 공고명 | 원고 마감 | 적용 방향 |
|---|---|---|---|---|
| 1 | Electronics / Special Issue | Generative AI, Large Language Models and Their Applications | 2027-03-31 | typed knowledge representation, neuro-symbolic control, evidence-bound output |
| 2 | Applied Sciences / Special Issue | Agentic AI and Large Language Models for Applied Intelligent Systems | 2027-05-10 | 실제 에이전트 구조, 신뢰성, 도구 실행 및 응용 평가 |
| 3 | Electronics / Special Issue | Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems | 2027-02-15 | 소프트웨어 아키텍처, 재현성, 실행 검증, 배포 비용 |
| 4 | Applied Sciences를 선택 / Topic | Challenges and Solutions in Large Language Models | 2027-06-30; 초록 2027-04-30 | 정책 우회·주입 방어·신뢰성의 구체적 위협 모델과 실험 |
| 5 | Applied Sciences / Special Issue | Advanced Applications of Large Language Models | 2027-02-20 | 도메인 지식·외부 도구 결합과 재현 가능한 응용 사례 |

근거: [S1]–[S7]. 순위는 주제 적합성에 관한 검토자의 판단이며 게재 가능성이나 편집부의 사전 승인 의미가 아니다.

Electronics(ISSN 2079-9292), Applied Sciences(ISSN 2076-3417)는 공식 imprint에 SCIE 등재가 표시되어 있다. Topic 자체가 SCIE 저널인 것은 아니다. 4번 경로에서는 참여 저널 가운데 **Applied Sciences**를 선택한다. 해당 Topic의 현재 참여 목록에 Electronics는 없다. 두 저널의 확인한 공고에는 APC CHF 2400이 표시되지만, 실제 청구액·세금·기관 할인은 제출 시 재확인한다.

### 1.2 핵심 주장 정리

권장 중심 주장:

> UIR은 지원되는 한국어·영어 제어언어 요청을 typed contract로 컴파일하고, 정책·근거 검증과 결정적 재구성을 통해 모델 생성과 시스템이 승인한 출력을 분리한다. 보장은 명시된 신뢰 가정과 지원 도메인 안에서 성립한다.

피해야 할 주장:

- 모든 언어·모든 도메인에 적용되는 보편적 자연어 이해.
- UIR이 일반적으로 추론 능력이나 정확도를 높인다는 주장.
- 0건 관측을 실패 확률 0이나 모든 prompt injection 해결로 표현.
- 신뢰 저장소에 근거가 있다는 사실을 객관적 사실성·의사결정 안전성 전체와 동일시.
- guardrail, CRAG, GraphRAG의 모든 구현에 대한 일반적 우위.
- p=0.50을 통계적 동등성 또는 비열등성의 증명으로 해석.

권장 제목 예시:

**UIR: A Typed Policy-and-Evidence Contract for Korean–English Small Language Model Agents**

UIR 명칭을 유지하면서 “Universal”의 의미를 지원 frontend 간 공유되는 표현으로 제한한다. 제목 예시는 제안이지 확정 제목이 아니다.

## 2. 작업 순서와 제출 차단 조건

| 단계 | 작업 | 제출 차단 여부 | 담당 역할 |
|---|---|---|---|
| G0 | W00 자료·버전 고정 | 차단 | 연구 책임자 / 실험 담당 |
| G1 | W01–W04 수치·채점·gold 분리 | 차단 | 평가 구현자 / 독립 검산자 |
| G2 | W05–W09 신규성·비교실험·명세·외부 검증 | 핵심 과학적 차단 | 저자 / 시스템 개발자 / 평가자 |
| G3 | W10–W12 위협 모델·통계·재현 패키지 | 차단 | 시스템·통계·데이터 담당 |
| G4 | W13–W15 서술·MDPI 변환·최종 게이트 | 차단 | 교신저자 / 편집 담당 |

G1이 완료되기 전 초록의 최종 성능 문장을 확정하지 않는다. W00–W15의 미완료 항목은 사유와 영향 범위를 기록한다. 단순히 “향후 연구”로 이동해서 현재의 강한 주장을 유지하지 않는다.

---

## W00. 원시 증거와 실험 버전 확정

**우선순위:** P0  
**위치:** `subsec:lim_artifacts`, 구현/재현성 부분(약 1522–1553, 1868–1889, 2481줄 이후)  
**문제:** 원고는 frozen evidence와 자동 생성 표를 주장하지만 제공 파일만으로 검증할 수 없다.

**작업**

- Phase-4F의 정확한 commit, manifest, 데이터 해시, 평가 코드 버전, prompt 버전, 모델 revision을 확보한다.
- 이전 단계와 최종 단계의 결과 파일을 분리한다. 각 표·그림·초록 수치가 어떤 파일과 집계식에서 나왔는지 연결한다.
- 600 internal, 50 adversarial, 418 commit-eligible의 집합 관계를 명시한다. 50과 418을 별도 독립 실험처럼 600에 더하지 않는다.
- 1200 semantic benchmark, 1000 robustness, 300 condition diagnostic, 500 mutation, 각 외부 200 사례의 중복·파생 관계도 기록한다.
- “authentic”이 실제 사용자 로그, 전문가 작성 사례, 합성 사례, 실제 추론 실행 중 무엇을 뜻하는지 분리한다.
- 데이터 생성·개발·검증·테스트·freeze 시점을 기록하고 테스트 사례로 prompt/validator를 반복 조정했는지 공개한다.

**산출물:** `evidence_manifest.json`, `claim_evidence_map.csv`, `cohort_manifest.csv`, `CHANGELOG.md`  
**완료 기준:** 모든 주요 수치를 `case_id → raw output → judgment → aggregate → manuscript location`으로 추적할 수 있고, 원본 로그가 없는 수치는 검증 완료로 표시하지 않는다.

## W01. HaluEval 교집합 지표의 불가능한 조합 해결

**우선순위:** P0 / 즉시 제출 차단  
**위치:** `subsec:eval_metrics`(약 1725–1827), `subsec:results_halueval`, `tab:external_results`(약 2120–2180)

**확인된 문제**

원고의 Phi-3.5 C8 HaluEval 행은 N=200, raw semantic accuracy=72%, contract validity=36.5%, accepted E2E accuracy=6%다. 같은 표본에서 E2E를 `correct AND contract-valid`로 정의했다면:

- correct: 144건
- contract-valid: 73건
- 교집합 최소: `144 + 73 - 200 = 17건 = 8.5%`
- 보고된 E2E: `12건 = 6%`

따라서 **현재 정의·동일 표본이라는 조건에서 양립할 수 없다**. 6%를 임의로 8.5%로 고치는 것은 금지한다. 8.5%는 가능한 하한일 뿐 실제 정답 값이 아니다.

**작업**

- 각 사례에 raw semantic label, raw correctness, contract-valid, projected answer, final correctness, accepted/rejected, error reason을 연결한다.
- raw correct와 contract-valid의 2×2 분할표 및 raw→final 정답성 전이표를 출력한다.
- E2E가 실제로 세 번째 게이트나 투영 후 정답성을 포함한다면 수식·명칭·표 주석을 수정한다. raw semantic correctness와 final correctness를 같은 변수로 표기하지 않는다.
- 서로 다른 버전/표본의 결과가 혼합되었는지 확인한다.
- 정정된 정의로 두 모델·두 baseline 전체를 재계산한다.

**산출물:** `halueval_case_audit.csv`, `halueval_transition_tables.csv`, `metric_correction_note.md`  
**완료 기준:** 같은 사건 C,V라면 `max(0,nC+nV-N) <= n(C∩V) <= min(nC,nV)`가 성립한다. 다른 사건을 사용하면 별도 정의와 사례 단위 근거가 제공된다.

## W02. 완전정답률·macro recall·coverage의 일관된 채점 체계 재구축

**우선순위:** P0 / 즉시 제출 차단  
**위치:** `eq:metric_cca`, `eq:metric_coverage`, `eq:metric_partial`, `tab:internal_utility`(약 1725–1827, 1980–2020)

**확인된 문제**

같은 418개 사례의 비어 있지 않은 required set R_i에 대해 CCA=`mean[ A_i=R_i ]`, macro recall=`mean[ |A_i∩R_i|/|R_i| ]`이라면 macro recall은 CCA 이상이어야 한다. 완전정답 사례는 각각 recall=1이기 때문이다. C8의 53.59%와 23.78%는 그 정의와 양립하지 않는다. 다른 baseline에도 유사 문제가 있다.

**작업**

- `raw emitted claims`, `accepted emitted claims`, `supported claims`, `relevant claims`, `required gold claims`를 별도 변수로 정의한다.
- 전체 원시 승인 출력에 대한 factual/policy 평가를 먼저 하고, 관련 claim 부분집합을 평가자가 추출하는 행위를 시스템의 실제 안전 투영과 혼동하지 않는다.
- macro/micro, cases/claims, 418/all600/answered-only의 분모를 전부 명시한다.
- recall이 전체 fact catalog 등 다른 분모를 쓴 값이면 conventional recall로 계속 부르지 않는다. 목적과 계산식을 설명하고 표준 recall도 함께 산출한다.
- C0/C3/C7의 `no answer=100%`가 실제 무응답인지 “검증된 답이 없음”인지 구별한다. 이 시스템들은 안전성 표에서 unsupported accepted output도 보고하므로 명칭이 중요하다.
- D1의 `safe partial`은 실제 승인된 전체 답변이 안전할 때만 사용한다. 지원되는 claim 몇 개가 있다고 unsafe mixed output을 safe partial로 분류하지 않는다.
- C5와 C1에도 동일한 사후 채점 규칙을 적용한다. 별도 partial mode가 없다는 이유만으로 내용상의 부분 정답을 무조건 0으로 만들지 않는다.
- N_accepted, N_nonempty, N_model_invoked, N_safe_answered를 별도로 공개한다.
- 원고의 C8 224/418 complete, 272/418 covered, 48/418 partial, 146/418 none은 보고 백분율에서 일치하는 **추론 값**일 뿐이다. 원시 자료로 검증하기 전 실측 건수로 확정하지 않는다.

**산출물:** `metrics_spec.md`, `metrics_case_level.csv`, `internal_utility_recomputed.csv`  
**완료 기준:** 같은 정의를 쓰는 행에 대해 `macro_recall >= CCA`가 성립한다. FULL/PARTIAL/NONE이 전수 분할이라면 세 건수 합이 N이며, unsafe/no-output 상태를 별도 축으로 명시한다. 정의 변경은 모든 baseline에 적용된다.

## W03. D1 schema validity와 전역 숫자 동기화

**우선순위:** P0  
**위치:** 초록/서론(약 83–142), `subsec:results_grammar`, `tab:grammar_comparison`, limitations

**확인된 문제:** 초록·서론의 D1 schema validity는 99.33%인데 결과·표·한계에서는 100%다.

**작업**

- 분모가 all600, model-invoked 또는 accepted subset인지 확인한다.
- 모두 N=600이라면 596/600과 600/600의 차이인 사례를 식별한다. 어느 쪽이 맞는지 원고만으로 추정하지 않는다.
- schema-valid의 기준을 raw token output, parsed JSON, contract-valid final output으로 나누고 혼용하지 않는다.
- 모든 성능 수치를 생성된 LaTeX macro/table에서 읽도록 바꾼다.
- “20.83% of accepted outputs”와 “20.83% of all evaluated cases”를 혼용하지 않는다. 현재 AUCR 수식의 분모는 all600이다.
- 최종값과 역사적 값의 차이를 변경 로그에 남긴다.

**산출물:** `generated_metrics.tex`, `generated_tables/*.tex`, `numeric_consistency_report.md`  
**완료 기준:** 초록·본문·표·결론의 동일 지표가 동일 분자·분모·버전을 참조한다.

## W04. 실행 시 계약과 평가용 gold의 분리

**우선순위:** P0  
**위치:** `alg:projection`, `subsec:projection_semantics`(약 1145–1216), 외부 평가/누출 통제 부분

**문제:** 투영 알고리즘의 required claim set R과 정확도 계산의 gold R_i가 같은 표기로 보인다. 이것만으로 데이터 누출을 단정할 수 없지만, 리뷰어는 런타임이 정답을 미리 아는지 질문할 수 있다.

**작업**

- `R_contract(U)`와 `R_gold(case)`를 서로 다른 이름·자료형·저장 위치로 정의한다.
- 런타임은 request, 허용된 facts, policy만 사용하도록 한다.
- 정답 라벨·expected answer·정답 program·adjudication 결과가 prompt, fact selection, acceptance guard에 들어가지 않음을 데이터 흐름으로 보여준다.
- fact registry에 값이 존재한다는 것과 해당 요청의 정답 claim을 oracle이 골라준다는 것은 다르므로 생성 과정을 공개한다.
- gold 파일을 접근 불가하게 둔 실행 테스트를 추가한다.

**산출물:** `runtime_evaluator_boundary.md`, `gold_access_test.log`  
**완료 기준:** gold 없이 추론·acceptance가 실행되고, 평가기에서만 gold가 사용됨을 재현할 수 있다. 의도적인 oracle-assisted 조건은 일반 성능과 별도 표로 보고한다.

## W05. 신규성 및 최신 직접 비교 문헌 보완

**우선순위:** P1 / 핵심 과학적 보완  
**위치:** Related Work, Introduction contributions(약 96–265)

**작업**

- CaMeL [S10]: trusted query에서 control/data flow를 분리하고 capability 기반 정책을 집행하는 접근과 비교한다.
- AgentSpec [S11]: 명시적 rule/DSL 및 runtime enforcement와 비교한다. ICSE 2026 공식 기록과 원 논문의 정확한 서지를 확인한다.
- 기존 RAG/guardrail/grammar 논문만으로 “결정적 안전 경계를 처음 도입”했다고 쓰지 않는다.
- 표현 계층, 정책의 위치, fact provenance, 다국어 canonicalization, safe partial semantics, 신뢰 가정, 구현 가능성을 축으로 비교표를 만든다.
- OPA/XACML 계열 정책 엔진, 기존 typed IR·CNL은 원고에 이미 인용된 범위를 점검하고 UIR의 고유 부분을 명시한다.
- 논문에서 사용한 Phi-3.5-mini, Qwen2.5-7B의 정확한 checkpoint/model card를 확인한다. Phi-3 일반 보고서가 실제 모델 revision을 대신하지 않도록 한다.
- 29개 BibTeX entry와 29개 사용 키는 정적으로 연결되어 있으나 이는 DOI·연도·저자·최신 출판본의 정확성 검증이 아니다. 서지를 별도로 검증한다.

**산출물:** `related_work_matrix.md`, 갱신된 `references.bib`  
**완료 기준:** “기존에도 가능했던 것 / 이번 논문이 추가한 것 / 실험으로 입증한 것 / 설계 목표에 머무는 것”이 분리되어 있다.

## W06. 검증기 효과와 UIR 자체 효과를 분리하는 비교실험

**우선순위:** P1 / 매우 중요  
**위치:** Baselines, Internal Results, Discussion(약 1634–1684, 1944–2065)

현재 C5도 accepted unsupported=0%, adversarial ASR=0%다. UIR의 안전성이 유일하다는 주장은 성립하지 않는다. UIR의 coverage 개선이 IR 구조 때문인지, UIR에만 붙은 partial projection 때문인지 분리해야 한다.

### 최소 권장 실험 조건

| 조건 | 고정할 요소 | 검증 질문 |
|---|---|---|
| 비-LLM 결정적 시스템 | 동일 CNL 입력, DB/facts, policy, template renderer | SLM을 빼면 정확도·coverage·지연·표현력이 어떻게 바뀌는가? |
| C5 + 동일 verified projection | 동일 사실 집합·검증기·partial 규칙 | 안전한 부분 답의 이득이 UIR 없이도 재현되는가? |
| D1 + fact-ID allowlist + 동일 rebinding | 같은 evidence/policy/출력 인터페이스 | UIR의 이득이 단순 의미 검증 결합 이상인가? |
| UIR without partial recovery | UIR 나머지 구성 동일 | partial semantics의 순증분은 무엇인가? |
| UIR의 표현/정책 구성요소 ablation | 실험 sandbox에서만 한 요소 변경 | canonicalization·policy AST·provenance의 각 기여는 무엇인가? |

**공정성 제약**

- 동일 사례, evidence 접근 수준, entity catalog, 정책, 도구 권한, 모델 revision, 생성 한도, prompt 개발 예산을 사용한다.
- 비교 조건의 model/context/token 차이가 불가피하면 수치와 이유를 표로 제공한다.
- 동일 baseline에 동일 scorer를 사용한다.
- C5–C7이 제3자 프레임워크의 정식 재현이 아니라면 모든 표에서 `guardrail-style`, `corrective-retrieval-style`, `graph-structured RAG`로 명확하게 표기한다.
- 성능 향상이 없더라도 숨기지 않는다. 그 경우 기여를 composability, 감사 가능성, 언어별 frontend 재사용 등 실제로 입증한 영역으로 조정한다.
- 실제 정책을 우회하도록 배포 시스템을 변경하지 않는다. 정책 ablation은 격리된 평가 환경에서만 수행한다.

**산출물:** `matched_baseline_protocol.md`, `ablation_case_results.csv`, 비교 표/그림  
**완료 기준:** 최소한 C5+projection, D1+fact binding, 비-LLM 대조군을 통해 “왜 UIR인가/왜 SLM인가”에 대한 증거가 있다. 수행 불가 조건은 주장을 축소하고 사유를 밝힌다.

## W07. 형식명세의 누락과 구현 대응 보완

**우선순위:** P1  
**위치:** formal specification(약 934–1404), contribution의 EBNF 주장(약 140), `alg:projection`

**작업**

1. 실제 지원 CNL/DSL의 EBNF와 UIR 직렬화 규격을 부록 또는 보충자료로 제공한다. 현재 소스에는 EBNF 제공을 기여로 선언하지만 문법 자체가 포함되어 있지 않다.
2. 한국어·영어의 동등 요청을 동일 typed UIR로 변환한 완전한 worked example을 넣는다. 실제 parser로 통과한 결과를 사용한다.
3. 허용, 거부, 승인 대기, read-only, clarification, quarantine, no-verified-answer의 상태·전이·실패 우선순위를 완전한 결정표로 정의한다.
4. main algorithm의 policy-aware `ProjectClaims(Y,U,F)`와 projection algorithm의 `ResolveVerifiedFact(c,F)` 사이 차이를 해소한다. fact match만으로 relevance·권한까지 자동 보장한다고 가정하지 않는다.
5. 직접 fact와 파생 fact를 구분한다. FinQA 계산 결과는 여러 operand의 허용 연산에서 나올 수 있으므로 단일 f와 값이 같은 경우만으로 정의하지 않는다.
6. 파생 fact에는 operand IDs, 연산 DAG/허용 연산, 단위, precision, rounding, overflow, division by zero, provenance, temporal validity를 정의한다.
7. canonical hash에 포함/제외되는 metadata, key ordering, Unicode/숫자 normalization, versioning을 명시한다.
8. “동등 AST라면 같은 canonical digest”와 “frontend가 의미를 보존한다”는 서로 다른 주장이다. 전자는 조건부 속성으로 표기하고 후자는 별도 증명·테스트를 제공한다.
9. A1–A5는 검증 대상 밖의 신뢰 전제로 명시한다. 전제를 다시 서술한 증명 스케치를 기계검증된 시스템 보안 증명으로 표현하지 않는다.
10. parser/type checker/policy evaluator/projector가 명세와 일치하는 conformance tests를 추가한다.

**산출물:** `grammar.ebnf`, `uir.schema.json` 또는 동등 명세, `operational_semantics.md`, `examples/`, `conformance_tests/`  
**완료 기준:** 외부 구현자가 예시와 명세만으로 동일 accept/reject/partial 결과를 재현할 수 있다. 지원하지 않는 언어·구문·연산은 명시적으로 거부된다.

## W08. annotation과 다국어 평가의 독립성 확보

**우선순위:** P1  
**위치:** benchmark methodology, multilingual results, `subsec:lim_annotation`(약 2465–2471)

**확인된 문제**

최종 검토는 사람 전문가가 아니라 같은 Gemini 계열의 세 AI 세션이다. 원고의 conditions_valid raw agreement=0.415, Fleiss κ=0.1995는 높은 의미 검증 신뢰도를 뒷받침하지 않는다. 같은 계열의 여러 세션은 인간 gold나 독립 모델 계열의 검증과 동일하지 않다.

**작업**

- 이러한 평가자 구성과 불일치를 Methods에 먼저 명시한다. limitations에만 두지 않는다.
- 대표 조건·정책 사례는 한국어/영어 및 도메인 이해가 있는 인간 평가자 2인 이상이 서로의 판정을 보지 않고 독립 평가하도록 설계한다.
- disagreement adjudication, 원판정 보존, annotator 지침, 시간/전문성, 모호함 처리 규칙을 문서화한다.
- 전수 검토가 불가하면 사전 정의된 층화 표본을 사용하고 human-audited subset과 AI-audited 전체를 별도로 보고한다. 전수 human ground truth라고 쓰지 않는다.
- 코드 혼합, 생략, 부정, 숫자·단위, AND/OR 괄호, 조건 범위, 권한 표현을 포함한다.
- 200/200 digest equivalence의 분모가 compile-successful pairs임을 표시하고 전체 입력쌍에 대한 end-to-end compiler correctness를 따로 계산한다.
- KO/EN/mixed별 N, parse success, intent, slot, AST, clarification의 confusion/count를 공개한다.
- 같은 template의 언어 변형을 독립 무작위 사례로 취급하는지 점검한다.
- 사람 평가를 새로 도입하면 기관 정책에 따른 윤리 검토·동의·보상 필요성을 확인한다. 자동으로 IRB “Not applicable”을 채우지 않는다.

**산출물:** `annotation_protocol.md`, `human_labels.csv`, `adjudication.csv`, `language_breakdown.csv`  
**완료 기준:** AI review와 인간 평가가 분리되어 있고, 조건 의미 판단에 대한 독립 근거 및 잔존 모호성이 공개된다.

## W09. 외부 평가의 계약 적합성과 실패 원인 분석

**우선순위:** P1  
**위치:** `subsec:results_finqa`, `subsec:results_halueval`, `tab:external_results`, external limitations

**작업**

- Qwen HaluEval의 contract validity=0%, accepted E2E=0%는 실용적 성공 사례로 제시하지 않는다. reject-all과의 utility 차이를 명시한다.
- Phi HaluEval의 metric 정합성은 W01 완료 결과를 먼저 반영한다.
- Qwen FinQA C1의 task accuracy=0% 및 raw unsupported=0%를 사례별로 분석한다. 빈 출력, 파싱 실패, chat template, truncated response, 모델 로딩/양자화, 프로그램 표현 차이를 점검한다.
- contract error를 schema, missing field, invalid fact ID, unsupported operation, policy deny, no evidence, wrong semantic answer 등으로 분류한다.
- FinQA의 “official execution accuracy”가 공식 evaluator와 동일한지 검증한다. 제한된 custom adapter이면 명칭을 수정하고 공식 evaluator와의 parity 검사를 제시한다.
- gold program의 허용 연산/형태가 UIR 계약으로 표현 가능한 비율을 측정한다. 지원할 수 없는 과제를 모델 추론 실패만으로 계산하지 않는다.
- 200개 subset ID, split, sampling rule, seed, selection date, 중복 여부를 공개한다.
- 모델 간 tokenizer/backend/quantization 차이를 명시하고 모델 규모 효과로 단정하지 않는다.
- 계약을 개선할 때 dev set에서만 조정하고 새로운 holdout에서 평가한다. 기존 부정적 결과는 별도 버전 결과로 보존한다.
- 가능하면 공개·재현 가능한 정책/근거 제약 agent task를 추가한다. 단순 hallucination recognition 분류만으로 다국어 실행 계약의 일반화를 주장하지 않는다.

**산출물:** `external_error_taxonomy.csv`, `benchmark_adapter_spec.md`, `external_case_manifest.json`, 새 holdout 결과  
**완료 기준:** 정확도, 계약 적합도, 승인 출력 정확도, 증거·정책 위반률이 서로 다른 사건으로 설명되고, utility가 0인 안전 관측을 일반화 성공으로 포장하지 않는다.

## W10. 정책 집행과 공격 평가의 변별력 확보

**우선순위:** P1  
**위치:** threat model, `tab:internal_safety`, adversarial/mutation methodology

**문제:** 현재 표에서는 모든 pipeline의 policy bypass가 0%다. 정책 실행 기능이 다르거나 실질적인 금지 행위 시도가 없으면 이 지표는 UIR의 추가 효과를 입증하지 못한다.

**작업**

- 각 조건의 실제 실행 가능한 도구·권한·write capability를 표로 만든다.
- `prohibited attempted action`, `blocked action`, `executed prohibited action`, `false denial of allowed action`을 구분한다.
- action capability가 없는 조건에는 근거 없는 “0% 우회” 대신 N/A 또는 해석 가능한 별도 분모를 쓴다.
- 허용·금지 최소쌍, 예외 우선순위, approval/revocation, entity/period/unit 바인딩 오류를 평가한다.
- 주입 방어의 범위를 직접 입력, 검색 문서, tool output, Unicode/code-mixing 등 구체적 입력 경로로 분리한다.
- facts/policies가 시간에 따라 바뀌는 경우 decision과 execution 사이 snapshot 또는 재검증 정책을 명시한다.
- 데이터 유출, 권한 없는 실행, 지원되지 않는 claim을 서로 다른 attack goal로 채점한다.
- 기존 50사례 결과는 유지하되 독립적인 새 공격 holdout을 설계한다. 건수만 늘린 template 복제는 폭넓은 공격 검증으로 표현하지 않는다.
- 500 mutation은 무엇을 변형했고 얼마나 중복되며 어느 invariant를 겨냥했는지 매핑한다.

**산출물:** `capability_matrix.csv`, `policy_attack_protocol.md`, `attack_goal_results.csv`, `mutation_invariant_map.csv`  
**완료 기준:** 공격 성공률의 분모와 공격자가 통제하는 요소가 명시되어 있고, UIR의 정책 집행이 실제로 시험되었다는 증거가 있다.

## W11. 통계 및 지연시간 분석 정비

**우선순위:** P1  
**위치:** `subsec:eval_statistics`, latency methods/results(약 1829–1854, 2067–2095)

**작업**

- 0/600 AUCR의 Wilson 양측 95% 상한은 약 0.64%이며, 0/50 adversarial ASR의 상한은 약 7.13%다. 서로 바꾸어 쓰지 않는다.
- 0/200이면 같은 방식 상한 약 1.88%, 0/500이면 약 0.76%다. 이러한 구간은 정의된 표본·모형 하의 불확실성이지 미지 공격 전반의 보안 보장이 아니다.
- AUCR을 전체 요청 분모와 승인된 비어 있지 않은 출력 분모로 함께 보고한다. 후자는 실제 denominator로 재계산한다.
- McNemar는 동일 사례의 discordant pairs 2×2 표로 계산한다. 집계 백분율만으로 p-value를 재구성하지 않는다.
- “statistically comparable/indistinguishable” 대신 “no statistically significant difference was detected”로 제한한다. 동등성/비열등성을 주장하려면 별도 사전 margin과 검정 설계가 필요하다.
- effect size와 paired confidence interval을 보고하고 Holm 보정의 비교군 집합을 명시한다.
- template/언어쌍/동일 source에서 파생된 사례 상관을 고려해 필요하면 cluster bootstrap 또는 층화 분석을 한다.
- 모델 호출 여부, raw output, final answer state를 독립 필드로 로깅한다. “답이 없음”이 “모델을 호출하지 않음”을 뜻하지 않는다.
- overall workload latency와 model-invoked latency, parse/policy/execute/generate/project/render 단계, tokens, cold/warm, repetitions, hardware를 분리한다.
- C8 mean 2082.9ms, early path 0.05ms, full path 4594.7ms를 오직 두 경로의 가중평균이라고 가정하면 약 272/600 model invocations가 된다. 이는 실제 호출 횟수 검증값이 아니라 **집계 일관성 점검 힌트**다. path 정의와 실제 counts로 확인한다.
- early rejection으로 얻은 workload 개선을 transformer 연산 속도 향상으로 기술하지 않는다.

**산출물:** `paired_statistics.csv`, `latency_case_results.csv`, `statistical_analysis_plan.md`  
**완료 기준:** 모든 검정의 N·분모·pairing·비교군과 모든 latency의 실행 경로가 추적된다.

## W12. 최소 재현 패키지 공개

**우선순위:** P1 / 제출 차단  
**위치:** Implementation, Reproducibility, Supplementary Materials, Data Availability

아래 구조는 **새로 준비할 산출물의 예시이며 현재 존재한다고 확인한 저장소가 아니다**.

```text
uir-release/
  README.md
  LICENSE
  manifest.json
  environment/
  contracts/
  policies/
  facts_or_public_fixture/
  prompts/
  case_manifests/
  anonymized_raw_outputs/
  annotations/
  evaluator/
  tests/
  generated_tables/
  reproduce.sh
  limitations_and_access.md
```

**작업**

- parser/type checker/policy engine/renderer/evaluator와 최소 fixture를 함께 제공한다.
- 정확한 모델 checkpoint revision, serving stack, decoding settings, seed, max tokens, backend, quantization, 하드웨어를 기록한다.
- 재현 명령은 실제로 테스트한 명령만 README에 적는다.
- 내부 데이터 공개가 제한되면 구체적 사유, 심사 목적 접근 경로, 공개 가능한 축소 fixture, 공개/비공개 결과 범위를 구분한다.
- 모든 원자료 공개가 항상 필수라고 주장하지 않는다. 다만 주요 결론을 검토할 수 있는 최소 자료와 접근 조건은 마련한다. MDPI 데이터 정책 [S9]을 따른다.
- DOI/저장소 URL은 실제 발급·접근 확인 후에만 넣는다.
- hash는 무결성 추적 도구일 뿐 생성 과정의 진실성이나 독립 재현의 증명으로 쓰지 않는다.

**산출물:** 실제 release archive, 접근 가능한 repository/보관소, `REPRODUCIBILITY_REPORT.md`  
**완료 기준:** 독립된 실행자가 문서화된 환경에서 주요 표를 재생성할 수 있거나, 제한이 있는 표의 이유와 검토 가능 경로가 명시된다.

## W13. 논문 구조·기여·용어 정리

**우선순위:** P2  
**위치:** 초록, 서론, 관련 연구, Discussion, Conclusion 전반

**작업**

- 기여를 (1) typed multilingual policy/evidence contract, (2) verified execution/projection semantics, (3) 조건부 안전성 및 utility 검증의 세 축으로 압축한다.
- “프롬프트는 권한이 아니다”, raw/accepted 구분, 한계 문장을 여러 절에서 반복하기보다 architecture figure·metric taxonomy·threat model로 집중한다.
- Phase-4F, B6 같은 개발 이력 라벨은 최초 정의 후 주로 부록/재현성 부분으로 옮긴다.
- SLM이 사실값 생성자가 아니라 fact selection/rendering에 참여한다면 역할을 명확히 쓴다. 결정적 renderer와 SLM renderer를 문단별로 혼동하지 않는다.
- `safe`는 검증한 속성에 맞게 `policy-compliant`, `evidence-bound`, `no accepted unsupported claim` 등으로 구체화한다.
- Korean/English CNL 지원과 자유 자연어의 일반 다국어 이해를 구별한다.
- 본문에는 실제 실행을 재현하는 worked example을 우선하고 장황한 개념 반복은 줄인다.
- 길이 축소 목표는 편집상의 권고이며 MDPI의 임의적 페이지 제한으로 쓰지 않는다.
- 결과 수치 확정 후 초록을 **단락 하나, 200단어 이하**로 다시 작성한다. 현재 LaTeX 초록의 단순 공백 기준 집계는 약 299단어다. 최종 단어 수는 LaTeX markup을 제거하여 검산한다.
- 초록의 핵심 비교는 약한 C1뿐 아니라 안전성이 같은 C5와의 실제 차이를 반영한다.

**산출물:** 수정 원고, `terminology_map.md`, `abstract_wordcount.txt`  
**완료 기준:** 제목·기여·실험·결론이 같은 범위의 주장을 하고, 외부 실패 결과가 결론에 반영되어 있다.

## W14. MDPI 형식과 연구윤리·공개 항목

**우선순위:** P2 / 제출 전 필수  
**위치:** 1줄 IEEE conference class, 저자/키워드 부분, 약 2589줄 이후 acknowledgment/bibliography

**작업**

- 대상 저널의 제출 시점 공식 LaTeX template로 복사본을 변환한다. IEEE conference class와 bibliography style을 그대로 최종 제출물로 사용하지 않는다.
- 번호·수식·algorithm·TikZ·표 너비·한국어 글꼴·단위·URL line breaks를 컴파일 결과에서 검토한다.
- Author Contributions는 실제 기여를 각 저자가 확인한다.
- Funding은 기존 IITP/ITRC 지원 문구와 과제번호의 정확성을 저자가 확인한 뒤 옮긴다. 임의의 기여·지원 기관·과제번호를 생성하지 않는다.
- Conflicts of Interest, Data Availability, Supplementary Materials, 필요 시 Institutional Review Board/Informed Consent 항목을 실제 상황에 맞게 작성한다.
- annotation과 benchmark construction에서 AI를 사용했다는 사실은 Methods에 투명하게 기술한다.
- 글쓰기·코드·이미지 등에 사용한 생성형 AI의 공개는 제출 시점 저널 지침과 실제 사용 기록에 따른다. 도구·버전·목적을 확인하지 않고 정형 문구를 채우지 않는다.
- MDPI 일반 layout guide의 초록 요건 [S8]과 대상 저널 세부 지침을 함께 확인한다.
- 기존 학회 발표/논문/프리프린트와의 중복 여부를 확인한다. 현재 IEEE 클래스라는 사실만으로 학회 출판 이력을 추정하지 않는다.

**산출물:** MDPI LaTeX source package, 실제 컴파일된 PDF, backmatter verification sheet  
**완료 기준:** citation/label 오류가 없고 모든 선언문이 저자 승인 및 실제 사실과 일치한다. 이 작업지시서 작성 단계에서 원고 PDF를 컴파일·시각 검증한 것은 아니다.

## W15. 최종 투고 결정과 커버레터

**우선순위:** P2  
**작업**

- 제출 직전 저널 ISSN으로 Clarivate Master Journal List의 SCIE 상태, 기관의 실적 인정 규정, Special Issue/Topic의 open 상태·deadline·APC를 다시 확인한다.
- 초록 사전 문의에는 제목, 문제, 고유 기여, 실제 완료한 검증, 왜 해당 issue에 맞는지를 보낸다. 문의 답변을 게재 승인으로 해석하지 않는다.
- 한 저널에만 투고한다. 대안 경로는 순차적 계획으로 유지한다.
- 커버레터에서 “hallucination-free universal reasoning” 대신 지원 도메인의 policy/evidence execution contract를 강조한다.
- 주요 정정/부정적 결과/비교군 한계는 숨기지 않는다.
- 논문·보충자료·저장소·커버레터의 성능 수치가 같은 release에서 나왔는지 확인한다.

**산출물:** `submission_checklist.md`, `cover_letter.txt`, 최종 source/archive  
**완료 기준:** 아래 제출 게이트가 모두 통과한다.

## 3. 기계적 검증 규칙 — 평가 코드에 반영

아래는 구현할 검증 규칙의 예시다. 현재 실행된 평가 코드가 아니다.

```python
# Same cohort, same definitions, complete per-case data.
assert N == len(case_ids)
assert len(case_ids) == len(set(case_ids))

# E2E = raw_correct AND contract_valid only when the specification says so.
if e2e_definition == "raw_correct_and_contract_valid":
    assert n_e2e == sum(raw_correct[i] and contract_valid[i] for i in range(N))
    assert max(0, n_raw_correct + n_contract_valid - N) <= n_e2e
    assert n_e2e <= min(n_raw_correct, n_contract_valid)

# Do not force this check on a differently defined recall without fixing its name.
if recall_definition == "macro_required_claim_recall":
    assert all(len(gold_required[i]) > 0 for i in eligible_ids)
    assert macro_recall + 1e-12 >= complete_claim_set_accuracy

# Only if FULL/PARTIAL/NONE is explicitly a mutually exclusive exhaustive partition.
if output_states_are_exhaustive:
    assert n_full + n_partial + n_none == N_eligible
    assert n_covered == n_full + n_partial

# Global-count AUCR is not conditional accepted-output risk.
assert n_unsupported_accepted <= n_nonempty_accepted <= N
assert n_model_invoked <= N  # Adapt if retries are counted as separate invocations.
assert n_model_invoked_cases == sum(case.model_invoked for case in cases)

# Final tables must all come from one declared evidence release.
assert all(table.manifest_hash == final_manifest_hash for table in publication_tables)
```

추가 점검: raw 생성 실패를 빈 문자열로 누락하지 않는다. retry 수와 model-invoked case 수를 구분한다. 지원 사실을 하나도 내지 못한 경우와 실제 시스템 abstention을 같은 값으로 덮어쓰지 않는다. 안전성 0건이 구조적으로 보장된 평가기라면 독립적인 출력/실행 oracle로 구현 결함도 점검한다.

## 4. 제출 전 Definition of Done

- [ ] W01 HaluEval 교집합 모순이 원시 자료 또는 정확한 사건 재정의로 해결되었다.
- [ ] W02 CCA/recall/coverage/partial/none 정의와 전체 baseline 채점이 일관된다.
- [ ] W03 99.33%/100% 불일치와 모든 지표 분모가 정리되었다.
- [ ] 평가 gold와 런타임 계약의 데이터 흐름이 분리되어 있다.
- [ ] C5+projection, D1+fact binding, 비-LLM 대조군을 통해 UIR의 기여를 분리했거나 주장 범위를 명확히 축소했다.
- [ ] EBNF·직렬화·상태 전이·파생 fact·canonicalization 명세가 구현과 대응한다.
- [ ] AI annotation을 인간 gold로 기술하지 않고 독립 검토 근거를 확보했다.
- [ ] 외부 benchmark adapter·실패 분석·subset·held-out protocol이 공개되었다.
- [ ] policy bypass의 기회·시도·실행 및 N/A 조건이 구분된다.
- [ ] paired statistics, uncertainty, clustering, latency 경로를 재검산했다.
- [ ] 접근 가능한 재현 패키지/제한 사유/심사자 접근 경로가 있다.
- [ ] 초록과 결론에 raw-model behavior와 accepted-system behavior의 차이가 유지된다.
- [ ] MDPI template, backmatter, references, PDF 레이아웃을 검토했다.
- [ ] 최종 제출 시 SCIE·open 상태·마감·APC를 재확인했다.
- [ ] 미확인 수치를 정정된 사실처럼 쓰거나 실행하지 않은 실험을 완료했다고 쓰지 않았다.

## 5. 검토자가 확인한 정적 소스 점검 결과

- BibTeX entry 29개, 인용 키 29개.
- 정적 점검에서 누락된 BibTeX 키, 사용되지 않은 entry, undefined cross-reference, 중복 label을 발견하지 않았다.
- 이는 실제 LaTeX 컴파일 성공이나 모든 서지 정보의 정확성을 보증하지 않는다.
- 외부 `input/include/includegraphics` 의존 파일은 정적 점검에서 발견하지 않았다. 패키지·글꼴 등 컴파일 환경 의존성은 별개다.
- 별도 제공되는 JSON은 수치 관계·소스 구조에 대한 정적 감사 결과이며, 원시 실험 재현 보고서가 아니다.

## 6. 외부 근거와 확인 URL

아래 공고의 사실 정보와 위 수정 지시는 구분한다. 수정 지시는 원고를 읽은 검토자의 판단이다. 확인일은 모두 2026-10-11이며, 직접 접근이 제한된 페이지는 MDPI 공식 페이지의 검색 색인을 사용했다.

- [S1] Electronics official imprint: `https://www.mdpi.com/journal/electronics/imprint`
- [S2] Applied Sciences official imprint: `https://www.mdpi.com/journal/applsci/imprint`
- [S3] Generative AI, Large Language Models and Their Applications: `https://www.mdpi.com/journal/electronics/special_issues/6337W8FB5D`
- [S4] Agentic AI and Large Language Models for Applied Intelligent Systems: `https://www.mdpi.com/journal/applsci/special_issues/RXURPXX5L8`
- [S5] Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems: `https://www.mdpi.com/journal/electronics/special_issues/WFBEQFE47X`
- [S6] Challenges and Solutions in Large Language Models: `https://www.mdpi.com/topics/B712V62UH1`
- [S7] Advanced Applications of Large Language Models: `https://www.mdpi.com/journal/applsci/special_issues/20KN2P5456`
- [S8] MDPI Layout Style Guide, Abstracts: `https://www.mdpi.com/authors/layout`
- [S9] MDPI Research and Publication Ethics, Data Availability: `https://www.mdpi.com/ethics`
- [S10] Debenedetti et al., Defeating Prompt Injections by Design (CaMeL), arXiv:2503.18813, version 2, 2025-06-24: `https://arxiv.org/abs/2503.18813`
- [S11] AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents, ICSE 2026 Research Track: `https://conf.researchr.org/details/icse-2026/icse-2026-research-track/29/AgentSpec-Customizable-Runtime-Enforcement-for-Safe-and-Reliable-LLM-Agents`
- [S12] Target author instructions to recheck at submission: `https://www.mdpi.com/journal/electronics/instructions` and `https://www.mdpi.com/journal/applsci/instructions`

---

**최종 원칙:** 이 논문의 강점은 “확률적 모델보다 더 많이 맞힌다”는 주장이 아니라 “어떤 근거·정책·신뢰 가정 아래 무엇을 승인하는지 명시한다”는 설계에 있다. 그 장점을 설득력 있게 만들려면, 논문 자체의 지표 계약과 증거 추적도 같은 수준으로 엄격해야 한다.
