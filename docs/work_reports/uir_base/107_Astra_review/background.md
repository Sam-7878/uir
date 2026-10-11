## 결론

**1순위는 Electronics의 「Generative AI, Large Language Models and Their Applications」, 2순위는 Applied Sciences의 「Agentic AI and Large Language Models for Applied Intelligent Systems」입니다.** UIR을 각각 **신경·기호 결합형 표현 및 검증 구조**, **정책·근거 제약을 갖는 에이전트 시스템 아키텍처**로 제시하기에 잘 맞습니다. 두 공고의 원고 마감은 각각 **2027년 3월 31일**, **2027년 5월 10일**입니다. ([MDPI][1])

다만 현재 원고는 **투고 전 Major Revision이 필요한 상태**로 판단합니다. 아이디어가 부적합해서가 아니라, **지표 정의와 결과 수치 사이의 정합성, UIR 자체의 기여를 분리하는 비교실험, 재현 자료**를 먼저 보완해야 하기 때문입니다. 특히 아래에서 설명하는 세 가지 수치 문제는 형식 수정이나 영문 교정만으로 해결할 수 없습니다.

요청하신 파일은 작성했습니다.

**[수정 작업지시서 다운로드 — 16개 작업, 원고 위치·산출물·완료 기준 포함](uir/docs/work_reports/uir_base/107_Astra_review/UIR_MDPI_Revision_Work_Order_2026-10-11.md)**
**[투고처 추천 및 사전 심사 보고서 다운로드](uir/docs/work_reports/uir_base/107_Astra_review/UIR_MDPI_Submission_Review_2026-10-11.md)**

검토 대상은 업로드하신 `_47_UIR.tex`와 `references.bib`입니다. **실험 코드·원시 출력·데이터셋은 제공되지 않았으므로, 아래 평가는 원고 검토와 수치 관계의 검산이며 실험 재현 결과는 아닙니다.**

---

## 1. 추천하는 MDPI SCIE Special Issue / Topic

### 추천 순위

아래 순위는 **현재 논문의 내용과 필요한 수정 방향에 대한 적합성 판단**입니다. 게재 가능성이나 심사 난이도를 수치화한 순위는 아닙니다.

| 순위    | 저널 / 모집 형식                           | Special Issue 또는 Topic                                                                | 원고 마감                                 | UIR 논문과의 적합성 및 제출 방향                                                                                                                                             |
| ----- | ------------------------------------ | ------------------------------------------------------------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** | **Electronics / Special Issue**      | **Generative AI, Large Language Models and Their Applications**                       | **2027-03-31**                        | 공고가 neuro-symbolic/hybrid AI, 지식 표현과 LLM 결합, 평가 및 설명가능성을 직접 포함합니다. **typed UIR, 정책·근거 바인딩, 생성과 승인 출력의 분리**를 중심으로 제출하기에 가장 잘 맞습니다. ([MDPI][2])                    |
| **2** | **Applied Sciences / Special Issue** | **Agentic AI and Large Language Models for Applied Intelligent Systems**              | **2027-05-10**                        | 에이전트 아키텍처, 도구 사용, 지식 기반 에이전트, 신뢰성, 안전한 배포, 금융·의사결정 응용을 포함합니다. **구현과 재현 가능한 시스템 평가를 강화하는 경로**에 적합합니다. ([MDPI][3])                                                 |
| **3** | **Electronics / Special Issue**      | **Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems** | **2027-02-15**                        | 시스템 신뢰성·효율성·검증·재현성을 강조합니다. **소프트웨어 실행 구조와 결정적 검증 계층**을 부각하면 적합합니다. 제목에 맞추려고 현재 없는 multi-agent 기능을 추가할 필요는 없습니다. ([MDPI][4])                                      |
| **4** | **Applied Sciences 선택 / Topic**      | **Challenges and Solutions in Large Language Models**                                 | **2027-06-30** — 초록 마감 **2027-04-30** | prompt injection 방어, 제어 가능성, 신뢰성 등을 모집합니다. **정책 우회 방지와 근거 기반 출력의 보안적 의미**를 중심으로 재구성할 때 적합합니다. 이 Topic에서는 참여 저널 중 **Applied Sciences**를 선택하는 것을 권합니다. ([MDPI][5]) |
| **5** | **Applied Sciences / Special Issue** | **Advanced Applications of Large Language Models**                                    | **2027-02-20**                        | 외부 지식·도구·도메인 전문성을 결합한 LLM 응용을 다룹니다. **기업·금융 도메인 사례와 실행 가능한 응용 평가**를 강화할 경우 좋은 대안입니다. ([MDPI][6])                                                                 |

### SCIE와 모집 상태 확인에서 주의할 점

**Electronics, ISSN 2079-9292**와 **Applied Sciences, ISSN 2076-3417**는 MDPI 공식 imprint에 **Science Citation Index Expanded, SCIE** 등재가 명시되어 있습니다. 이번 추천은 이 두 저널의 경로를 중심으로 제한했습니다. ([MDPI][7])

**Topic 자체가 SCIE 저널은 아닙니다.** 예를 들어 4번 Topic은 여러 저널이 참여하는 묶음이며, 실제 논문이 게재되는 저널을 선택해야 합니다. 확인한 참여 목록에는 Applied Sciences가 있지만 Electronics는 없습니다. ([MDPI][5])

확인한 두 저널의 공고에는 **APC가 CHF 2400**으로 표시되어 있습니다. 실제 청구액, 세금, 기관 할인은 별도 확인이 필요합니다. ([MDPI][1])

**확인 기준일은 2026년 10월 11일입니다.** 일부 MDPI 페이지의 직접 열기는 접근 제한으로 실패하여 공식 페이지의 검색 색인을 사용했습니다. 따라서 위 날짜는 확인된 **공고상 마감일**이며, 제출 직전 접수 화면에서 모집 상태·마감·참여 저널을 다시 확인해야 합니다. SCIE도 이번에는 MDPI 공식 표기로 확인했으며, **Clarivate Master Journal List를 독립적으로 검증한 것은 아닙니다.**

### 두 우선 후보 중 선택한다면

**UIR이라는 표현과 실행 계약의 개념적 기여를 중심으로 발전시키려면 1순위 Electronics**, **구현·비교실험·응용 신뢰성 평가를 중심으로 발전시키려면 2순위 Applied Sciences**를 권합니다. 현재 원고는 양쪽으로 발전시킬 수 있지만, 어느 경로든 아래 수치 정합성과 대조실험 문제는 먼저 해결해야 합니다.

---

## 2. 논문에 대한 종합 심사 의견

### 권고 판정: 투고 전 Major Revision

현재 원고를 “UIR 개념을 처음 소개하는 아이디어 논문” 정도로만 보기는 어렵습니다. 원고는 typed representation, 정책 의미론, 검증된 사실 바인딩, 다국어 frontend, 내부·외부 평가까지 포괄하는 **시스템 연구 논문**으로 구성되어 있습니다. 따라서 심사에서도 개념의 흥미뿐 아니라 **명세의 완결성, 구현과 명세의 대응, 지표의 정확성, 비교의 공정성**을 요구받을 가능성이 높습니다. 

### 유지해야 할 강점

가장 좋은 부분은 다음의 구분입니다.

> **모델이 생성한 것과 시스템이 승인한 것은 다르다.**

원고는 모델의 semantic correctness, contract validity, accepted-system correctness, system safety를 구분하고, 근거와 정책 검증을 통과한 내용만 승인 출력에 포함시키려 합니다. 또한 FULL/PARTIAL/NONE을 구분하여 “모두 거부하면 안전하다”는 단순한 접근을 넘어가려는 방향이 좋습니다. 

신뢰 저장소가 틀릴 수 있다는 점, 지원 범위가 한국어·영어 제어언어라는 점, C5도 같은 관측 안전성을 보인다는 점, 외부 평가에 부정적 결과가 있다는 점을 원고가 인정하고 있다는 것도 장점입니다. **이 한계들은 삭제할 내용이 아니라, 논문의 주장 범위를 정확히 만드는 내용**입니다.  

권장하는 중심 주장은 다음과 같습니다.

> **UIR은 일반적인 모델 추론 능력을 향상시키는 방법이라기보다, 지원되는 요청을 정책·근거 기반 실행 계약으로 변환하여 승인 가능한 출력과 실행을 결정하는 아키텍처이다.**

제목도 이 범위를 드러내도록 다음처럼 조정하는 방안을 권합니다.

**UIR: A Typed Policy-and-Evidence Contract for Korean–English Small Language Model Agents**

UIR이라는 이름을 유지하되, “Universal”이 무제한 자연어 이해나 모든 도메인에 대한 보장을 뜻하지 않도록 하는 방향입니다.

---

## 3. 투고 전에 반드시 해결해야 할 세 가지 수치 문제

### 3.1. HaluEval 결과가 현재의 교집합 정의와 양립하지 않습니다

Methods에서는 accepted E2E accuracy를 다음과 같이 정의합니다.

$$
\mathrm{E2EAcc}
=
\frac{N_{\mathrm{correct}\land\mathrm{contract\text{-}valid}}}
{N_{\mathrm{eval}}}.
$$

그런데 Phi-3.5의 UIR 결과는 **N=200, raw semantic accuracy 72%, contract validity 36.5%, accepted E2E accuracy 6%**&#xC785;니다.   

동일 표본과 동일한 `correct` 사건을 사용했다면, 정답은 144건이고 contract-valid는 73건입니다. 따라서 교집합은 최소한 다음과 같아야 합니다.

$$
144+73-200=17\text{건},\qquad 17/200=8.5\%.
$$

**보고된 6%, 즉 12건은 이 하한보다 작습니다.**

이는 반올림만으로 설명하기 어렵습니다. 다만 이것이 곧 “정답은 8.5%”라는 뜻은 아닙니다. 8.5%는 가능한 최소값일 뿐입니다.

**필요한 수정:** 사례별 raw correctness, contract validity, 투영 후 답변, 최종 correctness를 연결해 재계산해야 합니다. 실제 E2E가 투영 후 정답성이나 제3의 조건을 포함한다면, raw correctness와 다른 사건임을 수식과 표에서 분리해야 합니다. **6%를 임의의 다른 숫자로 바꾸면 안 됩니다.**

### 3.2. Complete claim-set accuracy와 macro recall의 관계가 맞지 않습니다

원고는 완전정답률을 \(A_i=R_i\)인 사례의 비율로 정의합니다. 그런데 C8의 내부 결과는 **완전정답률 53.59%, macro recall 23.78%**&#xC785;니다.  

동일한 418개 사례와 비어 있지 않은 동일 required claim set을 대상으로 통상적인 macro recall을 계산했다면,

$$
\mathrm{MacroRecall}
=
\frac{1}{N}\sum_i
\frac{|A_i\cap R_i|}{|R_i|}
\geq
\mathrm{CCA}
$$

가 성립해야 합니다. 완전정답 사례는 각각 recall이 1이기 때문입니다.

따라서 **현재 표는 서로 다른 분모·집합·정의가 섞였거나, 계산 또는 설명에 오류가 있을 가능성이 있습니다.**

**필요한 수정:** “required claims”, “전체 fact catalog”, “승인된 관련 claim”, “실제 출력된 모든 claim”을 구분하고 정확한 수식을 제시해야 합니다. 다른 의미의 recall을 썼다면 명칭을 바꾸고 표준 recall도 함께 보고하는 것이 좋습니다.

### 3.3. D1의 schema validity가 99.33%와 100%로 다르게 보고됩니다

초록과 서론에는 D1의 schema validity가 **99.33%**, Results와 비교 표에는 **100%**&#xB85C; 나옵니다.    

같은 N=600이라면 596건과 600건의 차이입니다. 다만 model-invoked subset 등 다른 분모를 사용했을 수도 있으므로, 먼저 분모와 실험 버전을 확인해야 합니다.

**필요한 수정:** 최종 manifest 하나에서 초록·표·본문 수치를 자동 생성하도록 연결하십시오. 이 문제는 작은 오타일 수 있지만, 원고가 “frozen evidence와 자동 생성 표”를 강조하기 때문에 심사자의 신뢰에 더 큰 영향을 줄 수 있습니다.

---

## 4. 방법론과 기여 측면의 주요 보완 사항

### 4.1. “왜 UIR인가?”를 보여주는 비교실험이 필요합니다

현재 가장 중요한 비교 대상은 Naive RAG만이 아니라 **C5 guardrail pipeline**입니다. C5도 내부 평가에서 accepted unsupported claims와 adversarial ASR이 모두 0%입니다. C8의 supported coverage는 65.07%, C5는 53.35%이지만, C5에는 동일한 partial-answer 경로가 없습니다.  

따라서 심사자는 다음을 물을 수 있습니다.

> “개선은 UIR 표현 자체에서 나온 것인가, 아니면 UIR에만 부착한 검증기와 부분 답변 복구 기능에서 나온 것인가?”

권장하는 핵심 대조군은 다음과 같습니다.

| 추가 대조군                                                  | 확인하려는 질문                           |
| ------------------------------------------------------- | ---------------------------------- |
| **C5 + 동일 verified projection**                         | 부분 답변의 이득이 UIR 없이도 재현되는가?          |
| **D1 + fact-ID allowlist + 동일 deterministic rebinding** | UIR의 이득이 문법 제약에 의미 검증을 결합한 것 이상인가? |
| **SLM을 제거한 CNL → DB/정책 → template 시스템**                 | 이 과제에서 SLM이 실제로 제공하는 기능과 비용은 무엇인가? |
| **UIR에서 partial recovery만 제거한 조건**                      | partial semantics의 순수한 효과는 얼마인가?   |

이 비교에서는 evidence, 정책, 도구 권한, 모델, 생성 한도, scorer를 가능한 한 동일하게 맞춰야 합니다. 결과가 UIR에 불리해도 유지하고, 그에 맞춰 기여를 표현 재사용성·구성 가능성·감사 가능성 등으로 조정해야 합니다.

### 4.2. 직접 관련 선행연구와의 차별화가 더 필요합니다

**CaMeL**은 trusted query로부터 control/data flow를 분리하고 capability 기반 정책을 집행하는 접근입니다. **AgentSpec**은 명시적 규칙과 runtime enforcement를 통한 에이전트 제약을 다룹니다. 따라서 “모델 밖에 결정적 안전 경계를 둔다”는 설명만으로 신규성을 충분히 확보하기는 어렵습니다. ([디지털 객체 식별자][8])

UIR의 차별점은 **다국어 frontend의 공유 표현, typed policy/evidence contract, fact provenance, 승인 출력의 구성 규칙, safe partial semantics** 중 실제로 새롭고 검증한 부분으로 좁혀야 합니다. 작업지시서에는 이 축으로 선행연구 비교표를 작성하도록 포함했습니다.

### 4.3. 형식명세를 실제 구현 가능한 계약으로 완성해야 합니다

기여 목록에는 **EBNF grammar를 제공한다**고 되어 있습니다. 그러나 제공된 소스를 정적으로 점검했을 때 문법을 제공한다는 문장은 있으나, EBNF 자체는 포함되어 있지 않았습니다. 

또한 현재 원고는 frontend 오류로 의미가 잘못 컴파일될 수 있으며, 가장 강한 안전성 주장은 A1–A5 신뢰 가정에 의존한다고 인정합니다. 

보완의 핵심은 긴 증명 문장을 더 추가하는 것이 아니라, **구체적인 grammar·직렬화 규격·상태 전이·구현 테스트의 연결**입니다. 특히 다음을 명확히 해야 합니다.

* “동등한 AST이면 같은 hash”와 “frontend가 원래 요청의 의미를 보존한다”는 서로 다른 주장입니다.
* 직접 가져온 fact와 여러 fact를 계산하여 얻은 파생 fact는 다른 규칙이 필요합니다.
* 실행 시 required contract와 평가용 gold answer가 분리되어야 합니다.
* 승인·거부·승인 대기·read-only·clarification 등의 상태가 알고리즘과 의미론에서 일치해야 합니다.

### 4.4. AI annotation을 인간 ground truth와 구별해야 합니다

원고에 따르면 최종 audit은 사람 전문가가 아니라 **같은 Gemini 계열의 세 AI 세션**입니다. `conditions_valid`의 raw agreement는 **0.415**, Fleiss’ \(\kappa\)는 **0.1995**입니다. 이 사실은 단순히 한계 절에만 둘 내용이 아니라, benchmark methodology의 핵심 정보입니다. 

**독립적인 한국어·영어 및 도메인 이해가 있는 사람 평가자의 검토를 추가하는 것을 강하게 권합니다.** 전수 검토가 어렵다면 사전에 정한 층화 표본과 불일치 조정 절차를 사용하고, human-audited subset과 AI-audited 전체를 별도로 보고하십시오. 이것은 MDPI의 일률적인 필수 요건이라는 뜻이 아니라, 이 논문의 의미 검증 주장을 강화하기 위한 심사상 권고입니다.

### 4.5. 외부 평가의 실패를 “안전성 성공”으로만 해석하면 안 됩니다

Qwen의 HaluEval 결과는 **contract validity 0%, accepted E2E accuracy 0%**&#xC785;니다. 원고도 이것이 utility success가 아니라고 인정합니다. 이 결과는 “모델이 항상 틀린다”는 뜻도 아니지만, “실용적인 일반화가 성공했다”는 뜻도 아닙니다.  

또한 Qwen FinQA의 Naive RAG가 task accuracy 0%로 보고되어 있으므로, 단순히 약한 baseline으로 받아들이기 전에 **chat template, 출력 파싱, 생성 길이 제한, adapter, 지원 가능한 연산**을 확인해야 합니다. 

부정적 결과는 유지하되, 계약을 수정한다면 개발셋에서만 조정하고 새로운 holdout으로 검증하는 편이 적절합니다.

### 4.6. 안전성·정책·통계 표현을 더 엄밀하게 해야 합니다

현재 AUCR은 **승인된 답변만을 분모로 한 위험률이 아니라, 전체 평가 사례 중 unsupported accepted claim이 발생한 사례의 비율**입니다. 이를 “accepted outputs의 20.83%”처럼 표현하면 분모가 달라집니다. 전체 요청 기준과 승인된 비어 있지 않은 출력 기준을 구분해 함께 보고하는 편이 좋습니다. 

모든 baseline의 policy bypass가 0%인 것도 해석이 필요합니다. 도구 실행 권한이 없는 시스템과 실제 금지 실행을 시도할 수 있는 시스템을 같은 방식으로 0% 처리했다면 정책 집행의 변별력을 보여주기 어렵습니다. **금지 행위 시도, 차단, 실제 실행, 허용 행위의 오거부**를 나눠야 합니다. 

통계적으로도 **0/600의 Wilson 95% 상한 약 0.64%와 0/50의 상한 약 7.13%는 다릅니다.** 후자는 원고의 50개 공격 사례에 대해 같은 방식으로 직접 계산한 값입니다. 또한 McNemar \(p=0.50\)은 “차이를 발견하지 못했다”는 의미이지 **동등성의 증명**이 아닙니다.  

---

## 5. MDPI 제출 준비에서 필요한 수정

현재 소스는 IEEE conference class를 사용하고 있습니다. 초록은 단순 공백 기준 정적 집계로 약 299단어인데, MDPI 일반 layout guide는 **단락 하나, 200단어 이하**의 초록을 안내합니다. 최종 제출 시 대상 저널의 세부 지침과 함께 확인해야 합니다.  ([MDPI][9])

형식 변환보다 먼저 **결과 수치를 확정한 뒤 초록을 다시 쓰는 순서**를 권합니다. 현재처럼 많은 실험 수치를 초록에 넣기보다, 문제·UIR의 핵심 구조·검증된 주결과·적용 범위를 남기는 편이 좋습니다.

재현성도 중요합니다. 원고가 frozen manifest와 hash를 언급하는 것과, 심사자가 실제 자료에 접근하여 검토할 수 있는 것은 다릅니다. MDPI는 Data Availability Statement를 요구하며, 필요한 경우 심사 과정에서 원시 자료를 요청할 수 있다고 안내합니다. 공개 제한이 있는 자료는 구체적인 제한 사유와 접근 조건을 설명해야 합니다. ([MDPI][10])

작업지시서에는 **모델 revision, prompt, policy/fact fixture, case manifest, evaluator, 원시 출력 접근 경로, 표 자동 생성**을 재현 패키지에 포함하도록 명시했습니다. Author Contributions, Funding, 이해충돌, AI 사용 공개 등은 실제 사실과 저자 확인에 근거해 작성하도록 했으며, 없는 내용을 자동으로 채우지 않도록 했습니다.

---

## 6. 작성한 작업지시서의 사용 순서

작업지시서는 다음 순서로 진행하도록 구성했습니다.

**원시 증거 고정 → 지표 정의·재계산 → 런타임과 평가 gold 분리 → 동일 검증기를 사용하는 대조실험 → 명세·독립 평가·외부 실패 분석 → 재현 패키지 → 초록·결론 재작성 → MDPI 형식 변환**

각 작업에는 **우선순위, 원고의 section/label 및 탐색용 줄 번호, 필요한 자료, 구체적 변경 내용, 산출물, 완료 기준**이 들어 있습니다. 원본 `.tex`와 `.bib`는 변경하지 않았습니다. 정적 점검 결과도 별도로 보존했습니다.

[정적 소스·수치 관계 점검 결과 JSON](sandbox:/mnt/data/UIR_source_audit_2026-10-11.json)

**최종적으로, 이 논문의 가장 설득력 있는 방향은 “더 똑똑한 SLM”이 아니라 “무엇을 승인할지 명시하는 정책·근거 기반 실행 계약”입니다. 그 기여를 인정받으려면, 논문 자체의 지표 정의와 증거 추적도 UIR이 지향하는 수준으로 엄격하게 정리되어야 합니다.**

[1]: https://www.mdpi.com/journal/electronics/special_issues/6337W8FB5D?utm_source=chatgpt.com "Generative AI, Large Language Models and Their Applications | Electronics | MDPI"
[2]: https://www.mdpi.com/journal/electronics/special_issues/6337W8FB5D "https://www.mdpi.com/journal/electronics/special_issues/6337W8FB5D"
[3]: https://www.mdpi.com/journal/applsci/special_issues/RXURPXX5L8 "https://www.mdpi.com/journal/applsci/special_issues/RXURPXX5L8"
[4]: https://www.mdpi.com/journal/electronics/special_issues/WFBEQFE47X "https://www.mdpi.com/journal/electronics/special_issues/WFBEQFE47X"
[5]: https://www.mdpi.com/topics/B712V62UH1 "https://www.mdpi.com/topics/B712V62UH1"
[6]: https://www.mdpi.com/journal/applsci/special_issues/20KN2P5456 "https://www.mdpi.com/journal/applsci/special_issues/20KN2P5456"
[7]: https://www.mdpi.com/journal/electronics/imprint "https://www.mdpi.com/journal/electronics/imprint"
[8]: https://doi.org/10.48550/arXiv.2503.18813 "https://doi.org/10.48550/arXiv.2503.18813"
[9]: https://www.mdpi.com/authors/layout "https://www.mdpi.com/authors/layout"
[10]: https://www.mdpi.com/ethics "https://www.mdpi.com/ethics"
