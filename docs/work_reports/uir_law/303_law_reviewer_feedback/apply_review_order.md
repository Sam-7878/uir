두 심사 의견은 서로 보완적입니다. **#1의 비판은 현재 논문의 가장 중요한 methodological point를 찌르고 있고, #2는 바로 다음 연구 방향을 제시하고 있습니다.** 현재 9월 19일 버전에는 이미 많은 개선이 들어갔지만, 몇 가지를 더 반영하면 논문의 방어력이 좋아집니다.

현재 원고는 LAW-KR-200의 네 범주별 결과까지 제시하고 있어 9월 11일 판보다 훨씬 강해졌습니다. 특히 A/B/C/D에서 Existence Check와 UIR을 직접 비교하는 표 2는 #1 리뷰에 대응하는 핵심 자료입니다. 

## 1. Reviewer #1의 “결과가 설계상 필연” 지적은 적극 반영하는 것이 좋습니다

이 지적은 타당합니다.

UIR이

$$
NOT\_FOUND/MISMATCH \rightarrow \text{no model invocation}
$$

으로 설계되어 있으므로, verifier가 정확하게 작동한다면 해당 branch에서 hallucination이 발생하지 않는 것은 **UIR 설계의 직접적 결과**입니다.

따라서 논문의 empirical contribution을

> “UIR이 통계적으로 기존 방법보다 hallucination을 제거했다”

보다

> **“UIR의 typed canonicalization과 identity binding이 자연어 질의를 의도한 deterministic verification branch로 정확히 routing하면서, valid query를 과도하게 reject하지 않는지를 검증했다.”**

로 바꾸는 것이 더 좋습니다.

즉 평가의 핵심은 사실:

$$
\boxed{
\text{Does UIR route the right query to the right semantic branch?}
}
$$

입니다.

### 현재 본문에 넣기 좋은 문장

Ⅲ절 결과 끝에 다음 문장을 권합니다.

> **UIR의 NOT_FOUND/MISMATCH 경로는 설계상 모델 생성을 수행하지 않으므로, 해당 경로의 비근거 생성 차단 자체는 구조적 특성이다. 따라서 본 평가의 핵심은 0%라는 수치 자체보다 자연어 질의가 올바른 UIR 상태로 정규화·바인딩되는지, 그리고 이 과정에서 유효 질의의 coverage와 FRR을 유지하는지를 검증하는 데 있다.**

이 한 문장이 Reviewer #1의 비판을 거의 정면으로 흡수합니다.

오히려 논문의 신뢰성이 높아집니다.

---

## 2. McNemar p-value는 삭제하거나 크게 약화하는 편이 낫습니다

현재 원고는 여전히:

> exact McNemar p=6.31e-30; Holm-adjusted p=1.89e-29

를 강조합니다. 

Reviewer #1이 바로 이 부분을 지적했습니다.

제 추천은 **2페이지 최종 논문에서는 p-value 문장을 삭제하는 것**입니다.

그 대신 공간을 다음에 쓰는 것이 훨씬 가치 있습니다.

> Existence Check: D Mismatch safe outcome 19/50
> UIR: D Mismatch safe outcome 50/50

그리고:

> Surface variation: C2 25/50 vs UIR 50/50

이미 표 2가 이를 제공합니다. 

이것은 p-value보다 훨씬 직접적으로 **UIR의 semantic canonicalization과 entity binding이 무엇을 해결하는지** 보여줍니다.

따라서 결과 문단은 예를 들어:

> 표 2에서 UIR은 A/B의 유효·표현변형 질의 100건을 모두 verified path로 처리했으며, C/D의 hard negative와 mismatch 100건을 모두 safe outcome으로 처리했다. 반면 Existence Check는 surface variation에서 25/50, mismatch에서 19/50의 올바른 결과만 보였다. 이는 본 benchmark에서 UIR의 이점이 단순 존재 확인이 아니라 canonicalization과 identity binding에 있음을 보여준다.

로 바꾸는 것을 권합니다.

---

# 3. “0%”를 contribution의 중심에서 조금 내려놓는 것이 좋습니다

Reviewer #1을 보면 심사자가 가장 경계하는 것은:

> “당연히 reject하도록 코딩해 놓고 0%라고 한다.”

입니다.

따라서 논문의 strongest result를

> **AULCR 0%**

하나로 두지 말고,

$$
\boxed{
Canonicalization + Binding + Utility Preservation
}
$$

세 가지의 조합으로 옮기는 것이 좋습니다.

즉:

* KO–EN canonical equivalence: 100/100
* Valid A/B: verified path 100/100
* Hard negative C: safe rejection 50/50
* Mismatch D: safe outcome 50/50
* FRR: 0/100

입니다.

이렇게 하면 “0%는 구조적으로 당연하다”는 공격을 받더라도 논문은 살아 있습니다.

---

# 4. 표 2가 Reviewer #1 대응의 핵심이므로 오히려 더 강조하세요

현재 표 2는 아주 좋은 수정입니다.

| Category    | Exist. Check |   UIR |
| ----------- | -----------: | ----: |
| A Valid     |         8/50 | 50/50 |
| B Surface   |        25/50 | 50/50 |
| C Hard Neg. |        50/50 | 50/50 |
| D Mismatch  |        19/50 | 50/50 |



특히 두 행이 중요합니다.

**B Surface variation**
→ semantic canonicalization의 효과

**D Mismatch**
→ identity binding의 효과

따라서 표 제목도 지금의 “범주별 올바른 결과”보다:

> **표 2. Semantic canonicalization 및 identity binding의 범주별 결과**

처럼 contribution과 직접 연결하면 더 좋습니다.

---

# 5. Reviewer #2의 multi-model 지적은 Future Work에 반드시 넣는 것이 좋습니다

이 의견도 타당합니다.

현재 연구는 Phi-3.5-mini-instruct 3.8B 하나에 한정되어 있으며 원고도 이를 limitation으로 밝히고 있습니다. 

여기에 사용자가 계획하는 **Qwen3 실험을 구체적으로 넣는 것**은 매우 좋은 대응입니다.

단순히:

> “다른 LLM에서도 시험한다.”

보다:

> **“Qwen3 계열의 서로 다른 model scale에서 UIR의 model-independence를 검증한다.”**

라고 쓰는 것이 좋습니다.

Qwen3에는 공개된 **Qwen3-4B** 및 **Qwen3-4B-Base** 모델이 있고 Apache-2.0으로 제공되므로 연구용 architecture modification에도 적합합니다. Qwen3-4B-Base는 4.0B parameters, 36 layers의 공개 causal LM입니다. ([Hugging Face][1])

---

# 6. 그런데 Qwen3 future work는 두 단계로 쓰는 것이 좋습니다

이 부분은 현재 UIR의 발전 방향을 아주 잘 보여줄 수 있습니다.

### 단계 1 — Model-independent replication

현재 UIR 구조는 그대로 두고:

$$
UIR \rightarrow Qwen3
$$

로 backbone만 교체합니다.

목적:

> **UIR 효과가 Phi-3.5 특정 모델에 의존하는지 검증**

입니다.

예를 들면:

* Phi-3.5-mini
* Qwen3-4B
* 이후 다른 규모 Qwen

를 비교합니다.

### 단계 2 — UIR-native model 연구

그 다음에는 사용자가 말씀하신 더 큰 연구 방향:

$$
Natural Language
\rightarrow UIR
\rightarrow Semantic Representation
\rightarrow Qwen3
$$

또는 model 내부에 UIR semantic representation을 주입합니다.

목표는:

* sample efficiency
* parameter efficiency
* context/token efficiency
* semantic consistency

를 검증하는 것입니다.

현재 논문에서는 아직 결과가 없으므로 **명확히 future research hypothesis**로 적어야 합니다.

---

# 7. Code Generation과 Medical/Bio 확장도 적극적으로 넣을 수 있습니다

저는 이 부분을 넣는 것을 권합니다.

오히려 이 내용이 **UIR이 단순한 법률 전용 DSL이 아니라 Universal IR이라는 점**을 보강합니다.

심사위원이 독창성 2/5, 3/5를 준 이유 중 하나는 현재 논문만 보면:

> “법률용 structured verifier 아닌가?”

라고 볼 여지가 있기 때문입니다.

따라서 미래 확장성을 짧게 명시하면 UIR의 “Universal”이라는 이름에 설득력이 생깁니다.

---

## 8. 세 domain은 UIR을 검증하기에 좋은 서로 다른 테스트입니다

### Legal

현재:

```text
Intent
Case ID
Case Name
Authority
```

### Code Generation

예:

```text
Intent       = GENERATE_CODE
Language     = PYTHON
API          = torch.nn.Linear
Signature    = ...
Constraints  = Python >= 3.12
Tests        = ...
```

여기서 `Prompt ≠ Authority`는:

> 모델이 존재한다고 말한 API가 실제 API라는 보장은 없다.

입니다.

따라서:

$$
Prompt
\rightarrow
Typed\ API\ UIR
\rightarrow
API/Compiler/Test\ Verification
\rightarrow
Code\ Generation
$$

이라는 동일한 architecture가 가능합니다.

이것은 UIR과 매우 잘 맞습니다.

---

### Medical / Bio

예:

```text
Intent       = SUMMARIZE
Entity       = DRUG / GENE / DISEASE
Identifier   = ...
Evidence     = verified biomedical source
Constraints  = ...
```

여기도:

> 사용자가 제시한 약물–질환 관계나 gene association을 사실로 자동 승격해서는 안 된다.

는 동일한 `Prompt ≠ Authority` 원칙을 적용할 수 있습니다.

다만 의료 영역에서는 임상 안전성까지 주장하지 않고:

> **biomedical entity/evidence grounding**

수준에서 시작하는 것이 적절합니다.

---

# 9. 이것이 오히려 “Universal”을 실증하는 장기 benchmark가 됩니다

아주 좋은 다음 논문 구조가 나옵니다.

$$
\text{Legal}
\qquad
\text{Code}
\qquad
\text{Bio/Medical}
$$

세 domain의 surface semantics는 전혀 다르지만 UIR core는:

$$
\boxed{
Intent
+
Typed\ Entity
+
Constraints
+
Authority
+
Output\ Contract
}
$$

로 동일합니다.

그렇다면 다음 연구 질문은:

> **Can one UIR semantic contract generalize across heterogeneous authoritative domains?**

가 됩니다.

이것은 현재 법률 paper보다 훨씬 강한 **Universal IR 논문**이 될 수 있습니다.

---

# 10. 현재 논문의 Future Work 문단은 이렇게 수정하는 것을 권합니다

현재 마지막 문장은 source outage, US replication, legacy RDB 중심입니다. 

이를 약간 확장하면 좋습니다.

### 권장 최종 문안

> 결과는 2026-09-11에 동결한 대법원 identity metadata, 한·영 100쌍 및 로컬 3.8B 모델에 한정되며, 실체적 법리 추론이나 보편적 환각 제거를 의미하지 않는다. 또한 단일 국가법령정보 공동활용 snapshot을 권위 경계로 사용하므로 다중 정보원 불일치와 source outage는 평가하지 않았다. 향후에는 (1) Qwen3를 포함한 다양한 규모와 계열의 공개 LLM에서 UIR의 모델 독립성을 검증하고, (2) UIR semantic representation을 모델 입력 및 내부 표현과 결합하여 sample·parameter efficiency에 미치는 영향을 분석하며, (3) 미국 판례뿐 아니라 code generation과 biomedical/medical entity grounding으로 UIR을 확장하고, (4) source unavailability와 multi-authority conflict에 대한 fail-closed 동작 및 legacy RDB 연계를 평가할 예정이다.

이 정도면 공간 대비 정보량이 상당히 좋습니다.

---

## 11. 다만 2페이지라면 더 압축한 버전이 좋습니다

현재 업로드한 파일은 parsed 기준으로 **참고문헌 마지막 한 줄이 3페이지로 넘어가 있습니다.** 

KAIC가 2페이지 제한이면 지금 상태에서는 문장을 늘리면 안 됩니다.

따라서 실제 원고에는 아래 정도로 압축하는 것이 가장 좋습니다.

> **향후에는 Qwen3 등 다양한 공개 LLM에서 모델 독립성을 검증하고, UIR semantic representation을 모델 내부 표현과 결합해 sample/parameter efficiency를 평가할 예정이다. 또한 법률을 넘어 code generation과 biomedical entity grounding으로 domain을 확장하고, 다중 authority 및 legacy RDB 연계를 연구한다.**

두 문장 정도면 충분합니다.

---

# 12. Reviewer #1에 대응해 Conclusion도 한 문장 바꾸면 좋습니다

현재:

> “UIR은 ... 근거 없는 법률 주장 수용을 낮추면서 valid identity coverage를 유지했다.”

도 괜찮습니다.

하지만 다음이 더 정확합니다.

> **본 결과는 생성 차단 자체의 효과보다, 자연어 질의를 typed UIR로 canonicalize하고 올바른 verification branch에 routing하면서 valid identity coverage를 유지할 수 있음을 보여준다.**

이 문장이 이번 review에 가장 직접적인 답입니다.

---

## 반영 우선순위

제가 실제 camera-ready라면 다음 순서로 합니다.

1. **McNemar p-value 강조 삭제**
2. **“0% 자체가 contribution이 아니라 correct semantic routing + coverage preservation이 contribution”이라는 문장 추가**
3. **표 2 B/D 결과 강조**
4. **Reviewer #2 대응: Qwen3 multi-model validation 추가**
5. **Qwen3-native UIR / sample·parameter efficiency를 future work에 추가**
6. **Code Generation + Bio/Medical domain extension 추가**
7. 미국법/CourtListener와 multi-authority/RDB future work는 짧게 유지

이렇게 하면 두 심사위원의 지적을 모두 수용하면서, 오히려 논문의 핵심을 더 **“UIR이라는 범용 semantic representation”** 쪽으로 끌어올릴 수 있습니다.

그리고 독창성 점수가 2/5와 3/5였다는 점을 생각하면, **법률 한 도메인의 deterministic verifier가 아니라 여러 모델·여러 도메인에서 재사용되는 universal semantic contract라는 장기 연구 방향을 명시하는 것은 특히 가치가 있습니다.** 현재 Qwen3-4B 같은 공개 모델은 소스 생태계와 Apache-2.0 라이선스가 있어 후속 UIR-native architecture 실험의 현실적인 출발점이기도 합니다. ([Hugging Face][2])

[1]: https://huggingface.co/Qwen/Qwen3-4B-Base?utm_source=chatgpt.com "Qwen/Qwen3-4B-Base · Hugging Face"
[2]: https://huggingface.co/Qwen/Qwen3-4B/tree/main?utm_source=chatgpt.com "Qwen/Qwen3-4B at main"
