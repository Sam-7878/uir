---

# UIR KAIC 2026 최종 수정 작업지시서

## 목적

Claude review 중 타당한 지적을 선별 반영하고, LAW-KR-200 frozen evidence 및 registered protocol과 논문/발표자료의 모든 표현을 일치시킨다.

수정 대상:

* `2026-09-11_#0013_UIR_KAIC2026_kr_LAW200_KR_FINAL.docx`
* `2026-09-14_#0021_UIR_KAIC2026_Oral_Presentation.pptx`

최우선 원칙:

> **새로운 실험 결과를 만들거나 기존 frozen 결과를 재해석하지 않는다.**
> 논문·슬라이드가 LAW-KR-200 protocol/report에 정확히 부합하도록 편집한다.

---

## A. 논문 DOCX 수정

### A1. 반드시 수정 — 저자/이메일 서식

현재 DOCX의 다음 표기를 정상화한다.

* `박성수o1` → 기존 학회 template의 올바른 교신저자/소속 각주 형식
* `김기형21` → 정상 소속 각주
* `parky@ajou.ac.kro` → `parky@ajou.ac.kr`
* 영어 저자명/이메일도 동일하게 수정

현재 파일에 실제 오류가 존재한다. 

학회 template의 기존 superscript 형식을 보존하고 임의 스타일을 새로 만들지 않는다.

---

### A2. 반드시 수정 — AULCR 최초 정의

Section III에서 표 1 전에 처음 등장할 때 명시적으로 정의한다.

권장 문장:

> **Accepted Unsupported Legal Claim Rate (AULCR)는 시스템이 ANSWER 또는 CORRECT로 수용한 출력 중 frozen authoritative identity metadata로 지지되지 않는 법률 주장을 포함한 출력의 비율이다. 따라서 분모는 전체 200질의가 아니라 각 pipeline의 accepted output 수이며 pipeline별로 다를 수 있다.**

그리고 현재 본문의 다음 설명은 유지한다.

* C1 = 80/83
* C2 = 98/142
* UIR = 0/100

Protocol의 metric contract와 정확히 일치해야 한다. 

`accepted unsupported event`, `근거없는 요청 수용` 등의 표현은 모두:

> **accepted unsupported legal claim / 근거 없는 법률 주장 수용**

으로 통일한다.

---

### A3. 표 1 pipeline 표기 정리

현재 C-number가 `C1, C2, C4, C5, C8`로 건너뛰므로 독자가 혼동할 수 있다.

**권장안:** 논문 본문에서는 번호를 제거한다.

| Method          |
| --------------- |
| Naive RAG       |
| Existence Check |
| Tool Agent      |
| Guardrail       |
| **UIR (Ours)**  |

필요하면 각주에만:

> “C-labels are internal benchmark-harness identifiers.”

라고 남긴다.

C0 Direct를 논문 표에 새로 넣는 것은 **필수 아님**. 2페이지 공간이 더 중요하다.

발표에서는 6개 baseline을 보여주되 논문은 대표 5개만 제시해도 된다. 단, 본문에:

> “Direct LLM을 포함한 총 6개 pipeline을 평가하였으며, 표 1에는 주요 비교군을 제시한다.”

정도의 짧은 설명을 넣는다.

---

### A4. C5 Guardrail 결과 한 문장 추가

Claude의 지적은 타당하다.

현재 표에는 C5가 있지만 본문 해석이 거의 없다.

추가 권장 문장:

> **Guardrail은 사후 citation/name allow-list를 적용했지만 AULCR 75.61%, FRR 84.00%를 보여, 생성 이후의 filtering만으로는 identity mismatch와 utility loss를 동시에 해결하지 못했다.**

단, **“prompt guardrail”이라고 쓰지 않는다.**

등록 protocol에서 C5는:

> naive retrieval + post-generation evidence/citation/name allow-list

이다. 

---

### A5. related work는 별도 절로 만들지 않는다

Claude의 “관련연구 독립 소절” 제안은 **반영하지 않는다.**

현재 2페이지 논문에서는 Section II 말미의 compact paragraph가 더 적절하다. 이미 LegalBench-RAG와 symbolic constraint 연구 대비 UIR의 차이가 기술되어 있다. 

대신 한 문장만 명확하게 유지한다.

> Dahl et al.은 legal hallucination을 측정·분석하는 반면, UIR은 typed entity binding을 통해 생성 이전에 unsupported legal entity를 차단하는 runtime representation layer를 제안한다.

새 절은 만들지 않는다.

---

### A6. 참고문헌 6→12 확대하지 않는다

Claude의 이 제안도 **반영하지 않는다.**

2페이지 paper에서 10~15개 reference는 오히려 본문 공간을 희생한다.

현재 6개 중 contribution과 직접 관련된 문헌을 유지한다.

필요하다면 maximum 1–2개만 추가하되 **2페이지 제한을 넘기지 않는다.**

---

### A7. Authority single-source limitation 추가

Claude의 이 지적은 타당하다.

Conclusion/Limitations에 한 문장을 추가한다.

> **본 평가는 단일 frozen 국가법령정보 공동활용 snapshot을 authority boundary로 사용하므로, 다중 법률 정보원 간 불일치나 source outage 상황은 평가하지 않았다.**

중요:

> API 장애에서도 fail-closed임이 “입증되었다”고 쓰지 않는다.

실험하지 않았으므로 future work로만:

> 향후 source unavailability 및 multi-authority conflict에 대한 fail-closed behavior를 평가한다.

---

## B. Category별 평가 표 설계

Claude가 제안한 “카테고리별 FRR 표”는 **그대로 만들면 안 된다.**

FRR은 정상 질의가 잘못 거절되는 비율이므로 **Category A/B에만 의미가 있다.**

Category C/D는 거절이 올바른 동작이므로 FRR을 적용하면 metric 의미가 뒤집힌다.

따라서 다음 구조로 설계한다.

### 권장 Table 2 — Category-wise Decision Quality

| Category            | Expected behavior             |                 Existence Check | Guardrail | UIR |
| ------------------- | ----------------------------- | ------------------------------: | --------: | --: |
| A Valid             | Accept verified               |            Valid Coverage / FRR |         … |   … |
| B Surface Variation | Accept after canonicalization |            Valid Coverage / FRR |         … |   … |
| C Hard Negative     | Reject NOT_FOUND              |    Invalid FAR / Safe Rejection |         … |   … |
| D Entity Mismatch   | Reject MISMATCH               | Mismatch FAR / Binding Accuracy |         … |   … |

### 중요

**새 숫자를 추정하지 않는다.**

Raw scored result에서 category별 count를 다시 aggregate하여 자동 생성한다.

특히 필요한 수치는:

* Category A: acceptance / rejection
* Category B: acceptance / rejection
* Category C: false acceptance / safe rejection
* Category D: false acceptance / mismatch detection
* 가능하면 KO/EN split

### 논문에 실제 넣을 compact 버전

2페이지 공간 때문에 모든 baseline을 넣지 말고 **C2 vs UIR**만 사용해도 된다.

가장 유용한 형태:

| Category          |  C2 Existence Check |                 UIR |
| ----------------- | ------------------: | ------------------: |
| Valid             |  correct accept (%) |  correct accept (%) |
| Surface variation |  correct accept (%) |  correct accept (%) |
| Hard negative     |     safe reject (%) |     safe reject (%) |
| Mismatch          | mismatch detect (%) | mismatch detect (%) |

이 표는 논문의 핵심 질문:

> **“UIR이 SELECT EXISTS와 무엇이 다른가?”**

에 가장 직접적으로 답한다.

이미 전체 entity-binding accuracy가 C2 38%, UIR 100%라는 결과가 있으므로, 특히 Category D breakdown이 핵심이다. 

---

## C. 논문 표현에서 제거할 과장 문구

다음 표현은 사용하지 않는다.

* “완전한 안전성”
* “완벽한 환각 제거”
* “0 risk”
* “완벽하게 통제”
* “25배 이상 안전”
* “환각이 물리적으로 불가능”

대신:

> **no accepted unsupported claims were observed in LAW-KR-200**

> **0/100 observed; Wilson 95% CI [0.00%, 3.70%]**

> **within the evaluated legal-identity setting**

으로 제한한다.

Claude가 제안한 “CI 상한 3.70%이므로 25배 이상 안전” 문장은 **반영하지 않는다.** Wilson CI의 상한은 worst-case bound가 아니며, 다른 pipeline의 point estimate와 단순 ratio로 비교하는 것은 부적절하다.

---

# D. 슬라이드 수정

## Slide 10 — 필수 수정

Claude 지적이 정확하다.

현재:

> `AULCR (Area Under the Learning Curve / Robustness)`

는 완전히 잘못된 풀이다. 

반드시:

> **AULCR = Accepted Unsupported Legal Claim Rate**

로 수정한다.

### Slide 10 문구도 함께 완화

현재:

> `UIR: 완전한 안전성과 유용성`

→

> **UIR: 평가 범위에서 unsupported acceptance 0건 + valid coverage 유지**

현재:

> `100/100 완벽 답변`

→

> **100/100 source-bound identity responses**

현재:

> `완벽 통제`

→

> **0 accepted unsupported outputs observed**

하단 결론:

> “유용성을 단 1%도 희생하지 않고 완벽 통제”

대신:

> **LAW-KR-200에서 UIR은 accepted unsupported output 0건을 관찰하면서 valid-query source-bound coverage 100%와 FRR 0%를 유지했다.**

Wilson CI `[0.00%, 3.70%]`는 그대로 유지.

C4의 0%는 반드시:

> `0 accepted outputs / FRR 100%`

라는 설명과 함께 표시한다.

---

## Slide 9 — 일부 수정, “6개” 자체는 유지

Claude가 “6개 → 5개로 바꾸라”고 한 부분은 **그대로 반영하지 않는다.**

슬라이드 9에는 실제로:

* C0
* C1
* C2
* C4
* C5
* C8

총 **6개 pipeline**이 존재하므로 “6개 비교 파이프라인”은 맞다. 

다만 다음은 반드시 수정한다.

### 1. Invalid FAR 정의

현재:

> “Cat C, D를 정상으로 통과”

는 protocol과 불일치.

수정:

> **Invalid Citation FAR: Category C hard-negative citation을 정상으로 acceptance한 비율**

Category D는 별도로:

> **Entity-binding / mismatch detection**

으로 설명한다.

### 2. C1 구현 설명

현재 `BM25/embedding`처럼 일반화하지 않는다.

실제 protocol대로:

> **deterministic lexical top-3 retrieval, no entity verification**

또는 한국어:

> **결정적 lexical top-3 검색, 개체 검증 없음**

### 3. C4 설명

“ReAct framework”라는 표현은 구현과 정확히 일치할 때만 유지한다.

안전한 표현:

> **Model-controlled lookup tool calling**

### 4. C5 설명

현재 `Prompt Guardrail`은 부정확.

수정:

> **Guardrail Pipeline — naive retrieval + post-generation citation/name/evidence allow-list**

### 5. ID 혼동 완화

시각적으로:

> Direct / Naive RAG / Existence Check / Tool Agent / Guardrail / UIR

을 큰 글씨로 두고, `C0/C1/...`는 작은 회색 tag로 처리한다.

---

## Slide 1 — Claude 지적은 대부분 반영하지 않음

Claude는 “소속이 …로 잘렸다”고 했지만, 실제 PPT parsed content에는:

> 발표자: 박성수
> 소속: 아주대학교 컴퓨터공학과

가 정상적으로 존재한다. 

따라서 **소속 내용 자체는 바꾸지 않는다.**

다만 실제 렌더링 QA에서 clipping이 있는지 확인한다.

수정할 것은:

* 제목의 `법률 검색을 위한범용` → **`법률 검색을 위한 범용`**
* 한글/영문 제목 줄간격과 alignment 정리
* 발표자/소속/날짜가 안전영역 안에 있는지 렌더 후 확인

---

# E. Claude review에서 추가로 반영하지 않을 항목

다음은 이번 revision scope에서는 제외한다.

1. **관련연구 독립 section**

   * 2페이지 제한 때문에 비효율적.

2. **참고문헌 12–15개**

   * 공간 대비 이득이 낮음.

3. **영어 abstract 추가**

   * KAIC template이 명시적으로 요구할 때만 수행.
   * 현재 review 파일만으로는 필요성이 입증되지 않음.

4. **“Wilson upper bound 기준 25× safer”**

   * 통계 해석상 부적절하므로 사용 금지.

---

# F. Claude가 놓친 추가 critical check

### F1. DOCX 2페이지 복원

현재 업로드된 DOCX는 parsed 기준 **3페이지**이며 참고문헌 일부가 page 3으로 넘어간다. 

최종 deliverable은 반드시:

> **≤ 2 pages**

로 되돌린다.

우선순위:

1. 문장 압축
2. figure vertical spacing 감소
3. 표 padding 감소
4. reference line spacing 최소화
5. 불필요한 영어 병기 축소

본문 font를 비정상적으로 작게 줄이는 방식은 피한다.

---

### F2. Slide 6/7의 source semantics도 추가 확인

Claude는 놓쳤지만 현재 발표자료에 두 가지 표현 위험이 있다.

Slide 6:

> `사건번호 존재 확인 (404 여부)`

한국 API는 공식 HTTP 404가 아니라 **HTTP 200 response 내 exact 사건번호 부재**를 normalized NOT_FOUND로 처리했다.

따라서:

> `exact 사건번호 match 존재 여부`

로 바꿔야 한다.

Slide 7:

> `실시간 바인딩`

최종 benchmark는 frozen snapshot을 사용하며 execution 중 live API lookup을 하지 않는다.

따라서:

> **frozen authoritative snapshot과 생성 전 binding**

으로 수정한다.

이 두 항목은 protocol과 직접 관련된 factual correction이므로, 요청된 1/9/10번 외이지만 함께 수정하는 것을 권장한다. 해당 semantics는 protocol에 명시되어 있다. 

---

# G. 최종 QA / Acceptance Criteria

### DOCX

* 최종 **2페이지 이하**
* author/email 오류 0
* `￾` 같은 hidden/invalid hyphen glyph 0
* AULCR 최초 정의 존재
* AULCR denominator 설명 존재
* category-wise table은 raw data에서 자동 생성
* C5 구현 설명 protocol과 일치
* “0% = zero risk” 표현 없음
* single-authority limitation 추가
* render → PNG 전 페이지 100% 확인

### PPTX

* Slide 1 제목 띄어쓰기 및 clipping 확인
* Slide 9:

  * 6 pipelines 유지
  * FAR Category C로 수정
  * C1/C4/C5 구현 설명 정확화
* Slide 10:

  * AULCR 풀네임 정상화
  * “완전/완벽” 과장 표현 제거
  * CI 유지
  * C4 0%의 denominator caveat 명시
* Slide 6/7 source semantics 보정
* 전체 slide rendering 후 overflow/clipping 검사

### Category table

* A/B에는 FRR/verified coverage
* C에는 Invalid FAR/safe rejection
* D에는 mismatch detection/entity-binding
* invalid category에 “FRR” 사용 금지
* 수치는 raw frozen LAW-KR-200에서 재산출
* 추정/수동 입력 금지

---
