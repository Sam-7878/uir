분석 결과, 이번에는 **논문 초안을 바로 작성하기보다 추가 개발이 필요합니다.** 다만 Phase 4C가 실패한 것은 아닙니다. 오히려 Phase 4C의 원래 목적이었던 **“실제 모델 추론 결과인지, provenance와 raw evidence가 진짜인지, gold가 generation 단계에 직접 들어가지 않았는지”를 검증하는 작업은 상당히 잘 수행되었습니다.**

실제로 이번 결과는 Phi-3.5-mini의 실제 local inference를 사용했고, 600개 공통 case × 9개 pipeline으로 5,400개 결과를 생성했으며, smoke test에서도 placeholder·response hash 누락·token 누락 등의 문제가 발견되지 않았습니다.   또한 report가 Phase 4C의 `READY_FOR_FINAL_MANUSCRIPT_AUTHENTIC`을 **“evidence authenticity/provenance/consistency gate”**로 한정하고 외부 benchmark superiority를 인증하는 것은 아니라고 명시한 것도 적절합니다. 

문제는 그 다음 단계입니다. 원시 결과와 당시 실행 commit의 코드를 함께 확인하니, **최종 SCI 논문의 primary evidence로 사용하기 전에 고쳐야 할 평가-validity 문제가 남아 있습니다.**

가장 중요한 문제는 internal benchmark의 runtime gate입니다. `freeze_inputs.py`에서 `runtime_entity_exists`, `runtime_policy_permit`, `runtime_uir_compiles`가 원래 데이터의 `entity_valid`, `policy_valid`, `uir_ready`, 심지어 `expected_outcome == "COMMIT"`에서 만들어집니다.  그리고 C8은 실제로 이 세 값과 `facts`가 모두 참일 때만 모델을 호출합니다.

즉 현재 구조는 개념적으로

$$
\text{actual entity/policy/compiler check}
$$

를 수행하는 대신 일부 경우

$$
\text{benchmark annotation}
\rightarrow
\text{runtime decision flag}
$$

로 변환된 값을 사용하고 있습니다.

이 때문에 report의 C8 결과인

* Unsupported accept: **0%**
* Invalid FAR: **0%**
* Attack success: **0%**
* Useful answer: **69.38%**
* Numeric exact: **62.92%**

자체는 재현되지만,  그 중 특히 attack/FAR 측정은 실제 runtime verification 성능과 benchmark annotation 효과를 완전히 분리하기 어렵습니다. 따라서 **Phase 4D에서는 entity registry, policy engine, UIR compiler를 실제로 실행하여 해당 결정값을 생성하도록 바꾸는 것이 필수**입니다.

두 번째는 공격 성공 판정입니다. 현재 scorer는 adversarial case가 reject되지 않으면 곧바로 `attack_success=True`로 처리합니다.  그러나 공격 프롬프트가 포함되어 있어도 모델이 그 공격을 무시하고 정상적으로 grounded response를 만들 수 있습니다. 따라서 앞으로는 이전 Security Benchmark에서 정립했던 것처럼 **attack class가 아니라 explicit attack goal을 독립 oracle이 평가**해야 합니다.

세 번째는 FinQA입니다. 현재 외부 결과는 C1/C2/C4가 3.5%, C8이 1.0%라서 UIR utility superiority를 전혀 보여주지 못합니다. Report 역시 이를 정직하게 negative external-generalization result로 기록했습니다.  그런데 raw output과 executor를 분석해 보면 이것을 순수하게 “UIR의 일반화 실패”라고 결론내리기에도 문제가 있습니다.

현재 C8 prompt는 FinQA arithmetic program을 생성하게 하지만, 모델은 실제로 다음처럼 source reference를 사용합니다.

```text
greater(E03, E04)
```

반면 executor는 `E03`, `E04`와 같은 evidence reference를 operand로 해석하지 못하고 **source 안의 실제 숫자 literal 또는 `#0` 같은 이전 step reference만 허용**합니다.

즉 여기에는

$$
\boxed{\text{UIR output contract} \neq \text{UIR executor grammar}}
$$

라는 adapter-level inconsistency가 있습니다.

따라서 FinQA 결과를 final external-generalization evidence로 쓰기 전에, 숫자 자체를 모델에게 복사시키는 대신

```text
N001, N002, ...
```

같은 **source-bound numeric evidence IDs를 operand로 사용하는 typed arithmetic UIR**로 바꾸는 것이 맞습니다.

네 번째는 HaluEval입니다. 현재 C8은 6% accuracy와 63.5% invalid-output rate였고, report도 exact-quote contract가 너무 brittle하다고 명시했습니다.  실제 구현을 보면 모델에게 단순 Yes/No뿐 아니라 `evidence_quote`를 원문에서 정확히 복사하도록 요구한 뒤, 그 문자열이 knowledge의 literal substring이 아니면 전체 결과를 `INVALID`로 만듭니다.

이 방식은 우리가 internal C8에서 잘 사용하고 있는

$$
\text{model selects reference}
\rightarrow
\text{deterministic layer renders trusted content}
$$

라는 UIR 철학과도 맞지 않습니다.

따라서 HaluEval 역시

```json
{
  "judgement": "Yes",
  "evidence_refs": ["K003", "K007"]
}
```

처럼 **evidence-ID selection 방식**으로 바꾸는 것이 더 자연스럽습니다.

또 하나 중요한 부분이 utility입니다. 현재 `useful_answer`는 완전한 답을 요구하지 않고 **expected claim 중 하나 이상 맞고 unsupported claim이 없으면** success로 처리합니다.  이는 C8의 강점인 high precision은 잘 측정하지만 completeness는 과대평가할 수 있습니다. 따라서 Phase 4D에서는 다음을 분리해야 합니다.

$$
\text{Claim Precision}
$$

$$
\text{Claim Recall}
$$

$$
\text{Complete Claim-Set Accuracy}
$$

$$
\text{Safe Partial Answer Rate}
$$

$$
\text{False Rejection Rate}
$$

이렇게 해야 C8이 실제로 만드는 중요한 trade-off인

$$
\boxed{
\text{Unsupported generation risk}
\rightarrow
\text{Abstention / bounded incompleteness}
}
$$

를 논문에서 훨씬 설득력 있게 보여줄 수 있습니다.

마지막으로 latency도 보강이 필요합니다. Phase 4C 보고서 자체가 C6/C8의 all-case P50에 **310개의 non-model deterministic rows**가 포함되어 있으므로 이를 model inference latency라고 표현해서는 안 된다고 명시합니다.  따라서 최종 논문에서는 반드시

* workload end-to-end latency
* model-invoked latency
* deterministic rejection latency
* committed-path latency

를 분리해야 합니다.

### 종합 판정

제가 판단하는 현재 상태는 다음과 같습니다.

| 항목                                         | 판정           |
| ------------------------------------------ | ------------ |
| 실제 Phi-3.5 inference                       | **PASS**     |
| raw output authenticity                    | **PASS**     |
| raw hash / provenance                      | **PASS**     |
| generation/scoring separation              | **PASS**     |
| Phase-4B simulated evidence 제거             | **PASS**     |
| C4 실제 model-generated tool call            | **PASS**     |
| 통계 재계산                                     | **대체로 PASS** |
| C8 unsupported-claim containment mechanism | **유망함**      |
| runtime evaluation independence            | **추가 수정 필요** |
| behavioral attack oracle                   | **추가 수정 필요** |
| complete utility metric                    | **추가 수정 필요** |
| FinQA adapter validity                     | **수정 필요**    |
| HaluEval UIR contract                      | **수정 필요**    |
| multi-model generalization                 | **추가 필요**    |
| 최종 SCI Results 작성                          | **아직 보류**    |

따라서 이번에는 **Phase 4D 추가 작업지시서**를 작성했습니다.

[UIR Phase 4D — Publication Validity & External Generalization Work Order](uir/docs/work_reports/104_uir_pahse_4d/UIR_PHASE4D_PUBLICATION_VALIDITY_EXTERNAL_GENERALIZATION_WORK_ORDER.md)

이 작업지시서에서 가장 중요한 순서는 다음입니다.

**1. Phase 4C evidence는 그대로 보존**하고 새 `uir_phase4d`를 만듭니다.

**2. `expected_outcome`, `entity_valid`, `policy_valid`, `uir_ready`에서 runtime decision을 만들어 내는 경로를 완전히 제거**합니다.

**3. 실제 entity registry + executable policy + actual UIR compile 결과로 C8 gate를 구성**합니다.

**4. FinQA를 source-bound typed arithmetic UIR로 고칩니다.**

```text
raw number generation
        ↓
N001 / N002 evidence references
        ↓
typed arithmetic steps
        ↓
deterministic executor
```

**5. HaluEval도 exact quote generation에서 evidence-ID selection으로 전환**합니다.

```text
free-text quote
        ↓
K001 / K002 evidence references
        ↓
deterministic quote rendering
```

**6. utility를 partial success와 complete success로 분리**합니다.

**7. Phi-3.5 외에 최소 한 개 7B/8B 모델을 추가**합니다.

**8. latency를 early rejection과 actual LLM invocation으로 분리**합니다.

여기까지 완료한 뒤에도 FinQA나 HaluEval 성능이 낮게 나온다면, 그것을 다시 억지로 개선하는 것은 권하지 않습니다. 그 경우 오히려 논문의 핵심을 다음과 같이 정리하는 것이 더 강합니다.

> **UIR의 주된 장점은 모든 자연어 과업의 정확도를 높이는 것이 아니라, semantic selection과 trusted factual execution을 분리하여 unsupported factual transitions를 구조적으로 통제하는 데 있다.**

즉,

$$
\text{UIR}
\neq
\text{general-purpose accuracy booster}
$$

이고,

$$
\boxed{
\text{UIR}
=
\text{semantic representation}
+
\text{verified-reference binding}
+
\text{deterministic trusted execution}
}
$$

이라는 방향입니다.

Phase 4D가 끝나고 결과가 나오면 그때는 **추가 개발을 더 반복하기보다 결과가 좋든 나쁘든 freeze하고**, 지금까지 Phase 3–4C에서 축적한 결과와 Phase 4D의 final evidence를 합쳐 논문 전체 초안을 작성하는 것이 가장 적절합니다.
