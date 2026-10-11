네. 지금 범위를 **UIR concept → semantic canonicalization → legal entity verification → hallucination-resistant legal retrieval**로 확정했다면, 제목과 서사도 그 흐름에 맞게 수정하는 편이 좋습니다.

기존 제목인 **“UIR: A Universal Intermediate Representation for LLM-Based Intelligent Systems”**는 범위가 너무 넓어서, 2페이지 논문이 실제로 보여주는 내용보다 큰 주장을 하는 인상을 줄 수 있습니다. 이번 논문은 UIR의 전체 가능성을 선언하기보다, **UIR이라는 개념을 소개하고 법률 검색에서 왜 필요한지를 명확한 사례로 증명하는 논문**으로 만드는 것이 좋습니다.

제가 가장 추천하는 제목은 다음입니다.

> **UIR: A Universal Intermediate Representation for Hallucination-Resistant Legal Retrieval**

이 제목이 가장 좋습니다. UIR이라는 새로운 개념을 앞에 살리고, 이번 논문에서 실제로 보여주는 application을 뒤에 붙입니다.

조금 더 architecture 쪽을 강조하고 싶다면:

> **UIR: A Typed Intermediate Representation for Hallucination-Resistant Legal Retrieval**

도 좋습니다. 다만 `Universal`이 UIR의 장기적인 정체성을 더 잘 살리므로 저는 첫 번째를 선호합니다.

또 하나의 대안은:

> **From Natural Language to Verified Legal Retrieval: A Universal Intermediate Representation for LLM Systems**

인데, 이 제목은 서사가 매우 잘 드러나는 대신 조금 깁니다.

---

## 논문의 핵심 서사는 이렇게 바꾸는 것이 좋습니다

이전에는

$$
\text{Multilingual Input}
\rightarrow
\text{Canonical UIR}
$$

이 사실상 논문의 중심이었습니다.

이제는 그것을 **첫 단계**로 낮춰야 합니다.

전체 흐름은:

$$
\boxed{
Natural\ Language
\rightarrow
Semantic\ Canonicalization
\rightarrow
Typed\ Legal\ Entity
\rightarrow
Entity\ Verification
\rightarrow
LLM
}
$$

입니다.

즉 독자가 논문을 읽고 기억해야 할 것은:

> **UIR은 여러 자연어 표현을 하나의 typed semantic representation으로 바꾸고, 그 representation에 포함된 legal entity를 검증한 뒤에만 LLM을 호출한다. 따라서 존재하지 않는 법률 entity가 LLM의 자유 생성으로 넘어가는 것을 차단할 수 있다.**

이 한 문장이 이번 논문의 전부라고 생각하면 됩니다.

---

# 논문 문제 제기도 바뀌어야 합니다

기존의 문제:

> LLM은 자연어 표현의 다양성과 ambiguity를 처리하기 어렵다.

이 정도로는 약합니다.

이번에는 다음처럼 가는 것이 좋습니다.

### Problem

LLM 기반 legal retrieval에서는 자연어 요청이 곧바로 retrieval 또는 generation으로 전달됩니다.

예:

> “Summarize 999 U.S. 999.”

여기에는 두 종류의 정보가 섞여 있습니다.

* 사용자의 **의도**: summarize
* 사실이라고 주장되는 **entity**: `999 U.S. 999`

일반적인 LLM에서는 둘 다 text token입니다.

따라서 모델은

$$
Intent
$$

와

$$
Claimed\ Fact
$$

를 구조적으로 구분하지 않습니다.

그 결과 존재하지 않는 citation도 자연어 문맥에 들어오면 실제 판례처럼 처리될 가능성이 있습니다.

여기서 UIR을 제안합니다.

---

# 핵심 철학은 여전히 `Prompt ≠ Authority`

이것을 법률 사례와 직접 연결하면 훨씬 강력해집니다.

사용자가

> “999 U.S. 999 판례를 요약하라.”

고 말했다고 해서

$$
999\ U.S.\ 999
$$

가 실제 판례가 되는 것은 아닙니다.

즉,

$$
\boxed{User\ Prompt \neq Factual\ Authority}
$$

입니다.

UIR은 이를

```text
intent      = SUMMARIZE
domain      = LAW
entity_type = CASE
citation    = "999 U.S. 999"
```

로 분리합니다.

그리고 `citation`은 LLM이 아니라 **authoritative entity source**가 검증합니다.

현재 구현에서도 영어 법률 frontend가 US citation ID를 별도 typed field로 추출하고, 존재하지 않는 citation 패턴을 `ID_NOT_FOUND`로 처리하는 구조가 구현되어 있습니다. 

이것이 이번 논문의 가장 좋은 demonstration입니다.

---

# 따라서 contribution도 수정해야 합니다

이제 contribution은 아래 3개가 가장 깔끔합니다.

**C1 — Semantic Canonicalization**
자연어 요청을 language-independent typed UIR로 변환하여 intent와 entity를 명시적으로 분리한다.

**C2 — Pre-generation Entity Verification**
UIR에 추출된 legal entity를 authoritative source에 binding하여 모델 실행 전에 존재 여부를 검증한다.

**C3 — Hallucination-Resistant Legal Retrieval**
검증되지 않은 legal entity에 대한 generation을 차단함으로써 unsupported legal-entity fabrication을 방지하는 prototype을 제시한다.

여기서 중요한 것은 **C1 → C2 → C3가 원인과 결과 관계**라는 점입니다.

$$
Canonicalization
\Rightarrow
Entity\ Verification
\Rightarrow
Hallucination\ Prevention
$$

좋은 논문 구조입니다.

---

# 논문 본문 구조도 이렇게 바꾸겠습니다

2페이지라면 저는 다음 구성을 권합니다.

### I. Introduction — 약 25%

첫 문단에서 legal hallucination 문제를 바로 제기합니다.

예를 들어:

> Large language models are increasingly used for legal information retrieval, but natural-language prompts do not distinguish user intent from factual authority. A model may therefore process an unverifiable citation as if it were an existing legal entity.

그리고 기존 RAG에서도 retrieval이 실패하거나 잘못된 entity가 입력되면 LLM이 여전히 생성할 수 있다는 문제를 짚습니다.

그 다음 바로:

> We propose UIR, a Universal Intermediate Representation that separates semantic intent from factual entities before model invocation.

---

### II. UIR Architecture — 약 35%

여기서 UIR의 기본 개념을 설명합니다.

$$
UIR = \langle
Domain, Intent, Entity, Parameters, Constraints
\rangle
$$

정도로 단순화합니다.

그리고 그림:

```text
Korean / English Legal Query
            │
            ▼
   Semantic Canonicalization
            │
            ▼
     ┌────────────────┐
     │   Typed UIR    │
     │ domain = LAW   │
     │ action = ...   │
     │ entity = ...   │
     └────────┬───────┘
              │
              ▼
      Entity Verification
        │             │
    VERIFIED       NOT FOUND
        │             │
        ▼             ▼
       LLM        Reject/Abstain
```

그리고 그림 중앙 또는 caption에:

> **Prompt ≠ Authority**

를 넣습니다.

현재 UIR architecture에서도 language-specific frontend가 공통 AST/UniversalIR로 수렴한 뒤 policy/fact binding을 수행하는 구조이므로 이 simplified diagram은 실제 구현과 잘 맞습니다. 

---

### III. Legal Retrieval Case Study — 약 30%

여기서 법률 사례를 보여줍니다.

예:

**Valid**

```text
"Summarize 410 U.S. 113"
        ↓
UIR
        ↓
Citation verification
        ↓
VERIFIED
        ↓
LLM
```

**Invalid**

```text
"Summarize 999 U.S. 999"
        ↓
UIR
        ↓
Citation verification
        ↓
NOT FOUND
        ↓
ABSTAIN
```

그리고 small table:

| Evaluation                                    |        Result |
| --------------------------------------------- | ------------: |
| KO/EN semantic pairs                          |           300 |
| Equivalent UIR                                |       300/300 |
| Invalid-entity prevention                     | 100% observed |
| Unsupported-claim acceptance after validation |   0% observed |

현재 controlled evaluation에서도 cross-lingual equivalence 300/300이 관찰되었고, invalid-entity fabrication prevention 역시 100% observed로 기록되어 있습니다.  

다만 표 아래에는 작게라도:

> *Results are obtained from a controlled prototype evaluation.*

이라고 명시하는 것이 좋습니다.

---

### IV. Conclusion — 약 10%

여기서는 UIR 전체 미래를 조금 열어둘 수 있습니다.

예를 들면:

> The legal retrieval case suggests that UIR can serve as a semantic contract between natural-language agents and authoritative structured information systems.

이 정도는 매우 좋습니다.

여기서 RDB 이야기를 살짝 넣는 것도 가능합니다.

> Because legal identifiers in UIR are explicitly typed, they can also be directly mapped to existing structured databases without converting all domain data into vector representations.

이 한 문장은 향후 **UIR ↔ legacy RDB orchestration** 연구의 씨앗이 됩니다.

그 이상은 이번 논문에서 확장하지 않는 편이 좋습니다.

---

# Abstract 역시 완전히 다시 쓰는 것이 좋습니다

제가 생각하는 abstract의 논리 순서는 다음입니다.

> ① LLM legal retrieval의 문제
> ② 자연어에는 intent와 factual assertion이 섞여 있음
> ③ UIR 제안
> ④ semantic canonicalization
> ⑤ typed legal entity verification
> ⑥ controlled prototype result
> ⑦ hallucination-resistant retrieval 가능성

예를 들면 다음 정도입니다.

> *Large language models (LLMs) are increasingly used for legal information retrieval, but natural-language prompts do not explicitly distinguish user intent from factual authority. Consequently, an unverifiable legal citation may be processed as if it were a valid entity and propagated into model generation. This paper introduces UIR, a Universal Intermediate Representation that converts multilingual natural-language requests into a canonical typed semantic representation before model invocation. UIR separates action intent from legal entities and binds typed identifiers to an external verification step. In a controlled Korean-English prototype, semantically equivalent requests were consistently mapped to equivalent UIRs, while invalid entities were rejected before downstream generation. The results suggest that UIR can provide a lightweight semantic contract for hallucination-resistant legal retrieval while keeping the LLM as a replaceable reasoning component rather than a factual authority.*

이 정도면 이전 abstract보다 훨씬 논문답습니다.

---

## 그리고 아주 중요한 포지셔닝 하나

이번 논문에서 **“hallucination-free”라는 단어는 제목에 쓰지 않는 것**을 권합니다.

대신:

> **Hallucination-Resistant**

가 좋습니다.

왜냐하면 우리가 실제로 보여주는 것은

$$
\text{all LLM hallucination} = 0
$$

가 아니라,

$$
\text{unverified legal entity}
\rightarrow
\text{pre-generation rejection}
$$

이기 때문입니다.

이렇게 써야 reviewer가 공격하기 어렵습니다.

---

### 최종 추천 제목

> **UIR: A Universal Intermediate Representation for Hallucination-Resistant Legal Retrieval**

### 이 논문의 한 문장 정의

> **UIR separates what the user wants from what the system is allowed to accept as fact.**

저라면 이번 KAIC 논문의 모든 문단이 결국 이 문장으로 수렴하도록 다시 작성하겠습니다.

그리고 이 방향이면 기존의 “한국어/영어 UIR 변환 논문”보다 훨씬 강해집니다. **다국어 canonicalization은 기술적 기반이고, legal entity verification이 mechanism이며, hallucination-resistant retrieval이 observable benefit**이 됩니다. 이 세 단계가 명확하기 때문에 2페이지라는 짧은 논문에서도 contribution을 매우 선명하게 전달할 수 있습니다.





예. 그래서 이번 수정에서는 **작은 법률 사례와 큰 정량 비교를 분리**했습니다. 이 구성이 현재 보유한 `_47_UIR` 실험 자산을 가장 안전하면서도 강하게 활용하는 방법이라고 봅니다.

구체적 사례는 **`999 U.S. 999`**입니다. 법률 frontend가 이를 단순 문자열이 아니라 typed citation으로 UIR에 넣고, fact/entity 검증에서 `ID_NOT_FOUND`가 나오면 **LLM을 호출하기 전에 종료**합니다. 반대로 prototype에 등록된 `410 U.S. 113` 같은 식별자는 fact retrieval 단계로 진행합니다. 기존 구현 문서에도 이 흐름과 가짜 citation 차단이 명시되어 있습니다.  

정량 결과는 예전 10-case 법률 실험의 “100%→0% hallucination” 표를 쓰지 않았습니다. 그 수치는 후속 `_47_UIR` 강화 과정에서 표본이 작고 tautological할 수 있다는 문제가 실제로 지적되었기 때문입니다.  대신 최종 Phase-4F의 **N=600 matched benchmark**에서 다음 네 baseline만 압축해 넣었습니다.

| Pipeline              | Accepted Unsupported Claims ↓ | Supported Coverage ↑ |
| --------------------- | ----------------------------: | -------------------: |
| C1 Naive RAG          |                        49.33% |               53.11% |
| C2 RAG + Entity Check |                        33.17% |               53.59% |
| C5 Guardrail          |                         0.00% |               53.35% |
| **C8 UIR**            |                     **0.00%** |           **65.07%** |

이 표의 장점은 상당히 큽니다. **단순 entity existence check만으로도 49.33→33.17%까지는 좋아지지만 충분하지 않다**는 것을 보여주고, Guardrail 역시 0% unsupported acceptance를 달성한다는 사실을 숨기지 않습니다. 그럼에도 UIR은 0%를 유지하면서 supported coverage가 **65.07%**로 가장 높습니다. 또한 complete accuracy는 Naive RAG 53.11%, UIR 53.59%로 통계적으로 유사했습니다(`p=0.50`). 즉 “전부 거절해서 0%를 만들었다”가 아니라 **fabrication을 verified partial answer/abstention으로 재배분했다**는 해석이 가능합니다.  

이 점이 이번 논문의 서사를 훨씬 강하게 만듭니다.

> **Semantic canonicalization → typed legal entity → pre-generation verification → hallucination-resistant retrieval**

그리고 그 아래에 실제 관찰 결과를 붙입니다.

> **Naive RAG: 49.33% unsupported acceptance
> Entity check: 33.17%
> UIR: 0.00%**

다만 논문에는 중요한 제한도 명시했습니다. **600-case benchmark 자체는 law-only corpus가 아닙니다.** 따라서 이를 “600개 법률 질의에서 hallucination 0%”라고 쓰지 않고, “법률 prototype에 사용된 동일한 typed verification/output-contract mechanism을 분리해 평가한 controlled internal benchmark”라고 정확히 표현했습니다. 이것이 reviewer 대응에도 훨씬 안전합니다.

관련 연구도 법률 쪽으로 다시 맞췄습니다. Dahl et al.은 법률 LLM에서 실제 case에 관한 검증 가능한 질문에서도 높은 hallucination 문제가 있음을 체계적으로 분석했고, LegalBench-RAG는 legal RAG에서 retrieval 자체의 정확성이 별도의 핵심 문제임을 다룹니다. 최근 ACL 2026 연구도 symbolic constraint를 이용해 legal hallucination을 줄이는 방향을 제안하고 있어, UIR을 **“단순 RAG 개선”이 아니라 request-level typed semantic contract**로 차별화하기 좋습니다. ([arXiv][1])

수정한 최종본은 아래입니다.

[영문 제출용 최종본](sandbox:/mnt/data/UIR_KAIC2026_Submission_EN_FINAL.docx)

[한국어 번역 최종본](sandbox:/mnt/data/UIR_KAIC2026_Korean_Translation_FINAL.docx)

두 파일 모두 다시 렌더링하여 **2페이지 구성과 표/그림 배치까지 확인**했습니다.

한 단계 더 강화할 여지는 있습니다. 제출 일정이 허용한다면 **50~200건 정도의 law-only citation verification benchmark**를 새로 수행해서 `Valid citation / nonexistent citation / false-premise citation` 세 종류만 비교하면, 이번 논문의 마지막 약점인 “정량 benchmark가 법률 전용이 아니다”도 제거됩니다. 다만 지금 상태도 2페이지 conference paper로는 이전 버전보다 contribution이 훨씬 명확합니다.

[1]: https://arxiv.org/abs/2401.01301?utm_source=chatgpt.com "Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models"


좋습니다. 이번에는 **기존 `_47_UIR` 결과를 재포장하는 것이 아니라, KAIC 논문의 주장에 정확히 맞는 독립된 `LAW-200` benchmark를 새로 만드는 것**이 좋습니다. 핵심은 “UIR이 가짜 citation 패턴을 hard-code로 잡았다”가 아니라, **실제 authoritative legal source에 근거한 entity verification이 Naive RAG·단순 existence check·agent/guardrail 대비 unsupported legal claims을 얼마나 줄이는가**를 검증하는 것입니다.

특히 CourtListener에는 citation 자체를 검증하는 v4 API가 있고, `200=found`, `404=형식은 유효하지만 database에서 찾지 못함`, `400=잘못된 reporter`, `300=ambiguous`를 구분합니다. 공식 문서도 이 API를 hallucinated citation 방지를 위한 guardrail 용도로 명시하고 있어 benchmark의 authoritative source로 적합합니다. ([FLP Wiki][1])

아래 작업지시서는 그대로 Codex/개발 Agent에 전달할 수 있도록 작성했습니다.

"/uir/docs/work_reports/uir_law/300_law_200_benchmark/LAW-200 UIR Legal Citation Verification Benchmark 작업지시서.md"

이 설계에서 특히 좋은 부분은 **Category D의 `citation ↔ case-name mismatch`**입니다. 단순 existence check는 citation 자체가 실제로 존재하기 때문에 통과하지만, UIR이 citation을 case entity와 결합해 검증한다면 mismatch를 탐지할 수 있습니다. 따라서 reviewer가 “그냥 SQL에서 `SELECT EXISTS` 하면 되는 것 아닌가?”라고 질문해도 실험적으로 답할 수 있게 됩니다.

또한 LAW-200은 굳이 한국 판례 DB와 미국 판례 DB를 동시에 사용하지 않고, **하나의 CourtListener authoritative source에 대해 질의 언어만 한국어/영어로 바꾸는 방식**을 권합니다. 이렇게 해야 legal-source coverage 차이가 결과에 섞이지 않고, semantic canonicalization과 entity verification을 깨끗하게 분리할 수 있습니다. CourtListener의 citation verification API 자체도 citation text 또는 volume/reporter/page로 lookup하며 valid/404/ambiguous를 구별하므로 이 실험에 잘 맞습니다. ([FLP Wiki][1])

그리고 이번 결과에서 가장 기대되는 표는 단순히 **“RAG 49.33% → UIR 0%”**를 다시 재현하는 것이 아닙니다. 새 LAW-200에서 예를 들어 `Naive RAG → Existence Check → UIR` 순으로 unsupported acceptance가 단계적으로 낮아지고, 동시에 valid-case coverage가 유지된다면, **UIR의 contribution이 정확히 어디에서 나오는지** 2페이지 안에서도 상당히 강하게 보여줄 수 있습니다. 기존 Phase-4F에서도 Naive RAG 49.33%와 UIR 0%의 차이는 매우 유의했고, complete accuracy는 거의 동일했습니다.  이번 LAW-200은 그 결과를 **법률 도메인에 직접 맞춘 독립 검증**으로 만드는 작업입니다.

[1]: https://wiki.free.law/c/courtlistener/help/api/rest/v4/citation-lookup?utm_source=chatgpt.com "Citation Lookup and Verification API - FLP Wiki"
