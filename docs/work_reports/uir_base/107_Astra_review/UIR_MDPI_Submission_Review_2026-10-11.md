# UIR — MDPI SCIE 투고처 추천 및 사전 심사 보고서

**검토일:** 2026-10-11  
**대상:** `_47_UIR.tex`, `references.bib`  
**권장 유형:** Original Research Article  
**사전 심사 판단:** 투고 전 Major Revision. 수치 정합성을 해결하지 않으면 reject-and-resubmit에 해당하는 판단을 받을 위험이 있다. 실제 편집부 결정이나 수락 확률을 예측한 것은 아니다.

## 1. 검토의 근거와 한계

이 보고서는 제공된 LaTeX/BibTeX 원고를 읽은 검토 의견이다. 실험 코드와 원시 출력은 제공되지 않아 재현하거나 실행 결과의 정확성을 확인하지 않았다. 아래의 “원고 결과”는 저자 보고이며, “정합성 점검”은 원고의 수식과 수치 사이 관계를 직접 검산한 것이다.

MDPI 공고는 2026-10-11에 공식 사이트의 검색 색인을 통해 확인했다. 일부 직접 페이지 요청은 429/cache 오류로 실패했다. 따라서 접수 화면의 최종 open 상태, 연장·변경된 마감, 참여 저널과 APC를 제출 직전에 다시 확인해야 한다. SCIE는 MDPI 공식 imprint 표기로 확인했으며 Clarivate Master Journal List를 독립적으로 조회한 것은 아니다.

## 2. 우선 추천

| 순위 | 저널 | Special Issue / Topic | 원고 마감 | 판단 |
|---|---|---|---|---|
| 1 | Electronics | Generative AI, Large Language Models and Their Applications | 2027-03-31 | neuro-symbolic/hybrid AI, knowledge representation, evaluation의 관점에서 가장 직접적으로 맞는다. |
| 2 | Applied Sciences | Agentic AI and Large Language Models for Applied Intelligent Systems | 2027-05-10 | 정책·근거 제약 에이전트의 시스템 설계와 실제 신뢰성 평가로 적합하다. |
| 3 | Electronics | Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems | 2027-02-15 | 소프트웨어 구조·검증·재현성 관점의 대안이다. multi-agent 기능을 억지로 추가할 필요는 없다. |
| 4 | Applied Sciences를 선택 | Topic: Challenges and Solutions in Large Language Models | 2027-06-30, 초록 2027-04-30 | 보안·신뢰성 중심으로 재구성할 때 적합하다. |
| 5 | Applied Sciences | Advanced Applications of Large Language Models | 2027-02-20 | 외부 지식·도구·도메인 응용을 중심으로 보완할 때 적합하다. |

공식 출처와 URL은 끝의 자료 목록을 참조한다. 적합성 순위는 검토자의 판단이다.

Electronics(ISSN 2079-9292)와 Applied Sciences(ISSN 2076-3417)는 공식 imprint에 SCIE로 표시되어 있다. Topic은 여러 저널의 논문을 묶는 경로이지 독립된 SCIE 저널이 아니다. 4번 Topic의 참여 목록 중 Applied Sciences를 선택해야 한다. 확인한 참여 목록은 AI, Applied Sciences, Cryptography, Mathematics, Symmetry이며 Electronics는 포함되어 있지 않다.

확인한 Electronics/Applied Sciences 공고는 APC CHF 2400을 표시한다. 세금·기관 할인·실제 청구액은 별도로 확인한다. Special Issue라는 이유로 심사가 완화되거나 게재가 보장되는 것으로 해석해서는 안 된다.

## 3. 논문의 가장 설득력 있는 기여

원고의 설계는 한국어·영어 controlled frontend, typed UIR, 외부 정책 평가, verified fact binding, 결정적 출력 검증을 연결한다. 핵심은 SLM이 생성한 토큰을 곧바로 승인 출력으로 취급하지 않는 것이다. FULL/PARTIAL/NONE을 구분하여 모든 것을 거부하는 방식과 안전한 부분 답변을 구별하려는 시도도 의미가 있다.

다음과 같은 제한을 원고가 이미 인정한다는 점은 긍정적이다.

- 근거 저장소가 틀리면 올바른 현실 지식을 보장하지 못한다.
- 자유로운 다국어 이해가 아니라 지원되는 한국어·영어 제어언어에 한정된다.
- UIR이 모든 task accuracy를 높이지 않는다.
- raw semantic accuracy, contract validity, accepted correctness, safety는 다르다.
- C5가 같은 관측 안전성을 보이며 외부 평가에는 명백한 실패도 존재한다.

따라서 “환각을 제거한 범용 추론기”보다 **조건부 정책·근거 실행 계약을 제시하고 검증하는 시스템 논문**으로 제출하는 편이 타당하다.

권장 제목 예시:

> UIR: A Typed Policy-and-Evidence Contract for Korean–English Small Language Model Agents

## 4. 제출을 막는 세 가지 수치 문제

### 4.1 HaluEval의 교집합 하한 위반

원고의 HaluEval Phi-3.5 C8은 N=200, raw semantic accuracy=72%, contract validity=36.5%, accepted E2E=6%다. Methods는 E2E를 correct와 contract-valid의 교집합 비율로 정의한다.

동일 표본·동일 correct 사건이라면:

```
n_correct = 144
n_contract_valid = 73
n_intersection >= 144 + 73 - 200 = 17
E2E >= 8.5%
reported E2E = 6% = 12/200
```

이 조합은 현재 정의하에서 불가능하다. 8.5%는 실제 정답 수치가 아니라 가능한 하한이다. raw correctness와 final correctness가 다르거나 다른 gate가 있으면 그 사건과 전이 과정을 재정의해야 한다. 원시 결과를 확인하지 않고 6%를 다른 수치로 바꾸어서는 안 된다.

**근거 위치:** `subsec:eval_metrics`, `subsec:results_halueval`, `tab:external_results`.

### 4.2 CCA와 macro recall의 관계

CCA는 required claim set을 완전히 맞힌 사례의 비율로 정의된다. 같은 표본·같은 nonempty required sets에 대한 표준 macro recall이라면, 완전정답 사례는 각각 recall=1이므로 `macro recall >= CCA`다.

C8의 CCA=53.59%, macro recall=23.78%는 이 해석과 맞지 않는다. 일부 다른 baseline도 마찬가지다. 다른 분모·집합을 쓴 recall이라면 수식과 명칭을 바꾸고 표준 recall도 보고해야 한다.

**근거 위치:** `eq:metric_cca`, `tab:internal_utility`.

### 4.3 D1 schema validity의 두 값

초록·서론은 D1 schema validity=99.33%를, 결과와 표는 100%를 보고한다. 같은 N=600이면 596건과 600건의 차이다. all cases, model-invoked cases, accepted cases 중 어떤 분모인지 및 어느 evidence version인지 확인해야 한다.

**근거 위치:** abstract, introduction, `subsec:results_grammar`, `tab:grammar_comparison`.

## 5. 주요 심사 의견

### 5.1 UIR 자체의 효과를 분리해야 한다

C5도 0% accepted unsupported 및 0% adversarial ASR을 보고한다. C8의 supported coverage 65.07%와 C5의 53.35% 차이는 흥미롭지만, C5에는 동일 partial projection이 없다.

심사자가 묻는 핵심은 “UIR이 필요한가, 아니면 동일 검증기와 결정적 renderer를 붙이면 되는가?”다. 동일 evidence/policy/scorer로 다음 대조군을 추가할 것을 권고한다.

- C5 + 동일 verified projection.
- D1 + fact-ID allowlist + 동일 deterministic rebinding.
- SLM을 제거한 CNL→DB/policy→template 시스템.
- UIR에서 partial recovery만 제거한 조건.

여기서 얻는 이득이 작더라도 결과를 보존하고, 표현 재사용·구성 가능성·감사 가능성 등 실제로 입증한 장점을 중심으로 기여를 조정해야 한다.

### 5.2 직접 관련 선행연구가 더 필요하다

CaMeL은 control/data flow 분리와 capability 기반 정책 집행을 다루며, AgentSpec은 명시적 규칙 및 runtime enforcement를 다룬다. 단순 RAG·문법제약 대비만으로 “결정적 경계”의 신규성을 주장하기 어렵다.

두 접근과 UIR을 표현 계층, 사실 출처, 다국어 frontend, 정책 권한, partial semantics, 신뢰 가정으로 비교해야 한다. 외부 논문의 성과를 UIR의 결과로 옮겨 쓰는 것은 금지한다.

### 5.3 형식명세를 실제 구현 계약으로 완성해야 한다

원고는 기여에서 EBNF를 제공한다고 선언하지만 제공된 소스에는 문법 자체가 없다. condition AST와 논리식이 있다고 해서 구체적인 입력 문법·직렬화 계약이 자동으로 완성되는 것은 아니다.

직접 fact와 계산으로 파생된 fact의 규칙, policy-aware projection, 런타임 required contract와 evaluator gold의 구분, 상태 전이의 완전한 정의를 보완해야 한다. “동등 AST→같은 hash”는 frontend 의미 보존 자체의 증명이 아니다. 신뢰 가정하의 성질, 구현 테스트, 기계검증을 구분해야 한다.

### 5.4 AI annotation과 인간 ground truth를 분리해야 한다

원고가 공개한 final audit은 같은 Gemini 계열의 세 AI 세션이며, 사람 전문가 검토가 아니다. conditions_valid의 raw agreement=0.415 및 Fleiss κ=0.1995는 특히 조건 의미 검증의 불확실성을 보여준다.

이를 Methods에 먼저 공개하고, 대표적인 조건·권한·다국어 사례에 대해 독립적인 인간 평가와 adjudication을 추가하는 편이 좋다. 불가하면 AI-audited benchmark라는 제한을 유지하고 주장을 축소해야 한다.

### 5.5 외부 평가의 실패는 범위 제한의 근거다

Qwen HaluEval에서 contract validity와 accepted E2E가 모두 0%인 것은 이용 가능한 답변을 제공하지 못한 결과다. 지원되지 않는 승인 claim이 0이라는 사실만으로 실용적 일반화 성공으로 볼 수 없다.

Qwen FinQA의 C1 accuracy=0%는 adapter, chat template, 출력 형식, generation truncation 등 원인을 먼저 조사해야 한다. 공식 evaluator와 custom adapter가 일치하는지도 검증해야 한다. 계약 수정을 개발셋에서 수행하고 새 holdout으로 재평가하되 기존 결과는 보존한다.

### 5.6 안전·정책·통계 지표를 더 정확히 보고해야 한다

현재 AUCR은 승인 출력만의 위험률이 아니라 전체 600사례 중 unsupported accepted claim이 있는 사례 비율이다. 두 분모를 혼용하지 말아야 한다. 모든 baseline의 policy bypass=0%는 정책 집행의 추가 효과를 보여주는 변별적 결과가 아니다. 실제 도구 권한과 금지 실행 기회를 함께 제시해야 한다.

0/600의 Wilson 95% 상한은 약 0.64%, 0/50의 상한은 약 7.13%다. CCA 비교의 McNemar p=0.50은 차이를 발견하지 못했다는 뜻이지 동등성 입증이 아니다.

지연시간은 전체 workload와 model-invoked 조건을 분리하고, early rejection 이득을 모델 자체 가속처럼 표현하지 않아야 한다.

### 5.7 재현 가능한 증거와 제출 형식이 필요하다

원고에 frozen evidence와 hash가 언급되더라도 실제 패키지 접근이 없으면 독자가 재현할 수 없다. evaluator, prompt, case manifest, 모델 revision, 정책·사실 fixture, raw output 접근 경로를 제공해야 한다. 제한 자료는 공개 제한과 심사자 접근 조건을 설명한다.

현재 소스는 IEEE conference 형식이고 초록은 단순 집계 약 299단어다. MDPI 일반 layout guide의 단락 하나·200단어 이하 초록 기준과 대상 저널의 세부 지침을 확인해 변환해야 한다. Data Availability, 기여·지원·이해충돌 등 선언은 실제 사실과 저자 확인에 기반해야 한다.

## 6. 권장 수정 순서

**원시 증거 고정 → 지표 정의와 재계산 → gold/runtime 분리 → 동일 검증기를 사용한 대조실험 → 명세·인간 검토·외부 실패 분석 → 재현 패키지 → 초록/결론 재작성 → MDPI 형식 변환** 순서가 적절하다.

가장 중요한 것은 검증되지 않은 수치를 미관상 일치시키는 일이 아니라, 지표 정의와 사례별 증거에서 논문의 결론이 다시 생성되게 하는 것이다.

구체적인 16개 작업, 파일 위치, 산출물과 완료 기준은 함께 제공하는 `UIR_MDPI_Revision_Work_Order_2026-10-11.md`를 따른다. 정적 검사 결과는 `UIR_source_audit_2026-10-11.json`에 기록되어 있다.

## 7. 외부 출처

1. Electronics SCIE imprint: `https://www.mdpi.com/journal/electronics/imprint`
2. Applied Sciences SCIE imprint: `https://www.mdpi.com/journal/applsci/imprint`
3. 추천 1 공고: `https://www.mdpi.com/journal/electronics/special_issues/6337W8FB5D`
4. 추천 2 공고: `https://www.mdpi.com/journal/applsci/special_issues/RXURPXX5L8`
5. 추천 3 공고: `https://www.mdpi.com/journal/electronics/special_issues/WFBEQFE47X`
6. 추천 4 Topic: `https://www.mdpi.com/topics/B712V62UH1`
7. 추천 5 공고: `https://www.mdpi.com/journal/applsci/special_issues/20KN2P5456`
8. CaMeL, arXiv:2503.18813 (v2, 2025-06-24): `https://arxiv.org/abs/2503.18813`
9. AgentSpec, ICSE 2026 Research Track: `https://conf.researchr.org/details/icse-2026/icse-2026-research-track/29/AgentSpec-Customizable-Runtime-Enforcement-for-Safe-and-Reliable-LLM-Agents`
10. MDPI Layout Style Guide: `https://www.mdpi.com/authors/layout`
11. MDPI Research and Publication Ethics: `https://www.mdpi.com/ethics`

원자료의 문장·수치 근거는 LaTeX section/label로 표시했다. 외부 문헌은 직접 관련 선행연구·출판 지침으로 사용했으며, 원고가 수행하지 않은 실험을 보충하는 증거로 사용하지 않았다.
