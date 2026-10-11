분석 결과, **UIR 아키텍처 자체의 추가 개발은 더 이상 필요하지 않습니다.** 하지만 지금 바로 논문 초안을 새로 작성하기에는 Phase 4D의 **최종 report와 frozen raw evidence 사이에 publication-blocking 불일치가 남아 있습니다.** 따라서 마지막으로 **Phase 4E — Final Publication Reconciliation**을 수행하는 것이 필요하다고 판단했습니다.

Phase 4D가 기술적으로 큰 진전을 이룬 것은 분명합니다. 실제 entity registry, executable policy engine, deterministic multilingual UIR compiler, behavioral attack oracle을 분리했고, 18개 publication gate를 모두 통과했다고 보고되어 있습니다.  또한 FinQA/HaluEval과 두 model family까지 확장한 것은 현재 논문의 external-validity 측면에서 중요한 발전입니다. 

그런데 zip의 raw evidence를 직접 재계산하니 네 가지 중요한 문제가 확인되었습니다.

### 1. 최종 report와 canonical raw CSV가 서로 다릅니다

예를 들어 `strong_baseline_summary_actual.csv`를 `per_case_evidence_actual.jsonl`에서 직접 재계산하면 다음과 같습니다.

| Pipeline | Unsupported accept | Attack success |
| -------- | -----------------: | -------------: |
| C0       |             35.83% |            66% |
| C1       |             49.33% |            92% |
| C2       |             33.17% |            84% |
| C3       |             27.33% |            50% |
| C4       |             23.83% |         **0%** |
| C5       |             **0%** |         **0%** |
| C6       |             11.00% |         **0%** |
| C7       |         **78.00%** |            90% |
| C8       |             **0%** |         **0%** |

그런데 Phase 4D final report에는 C4=76%, C5=91%, C6=90%, C7=66% attack success 등 다른 값이 들어가 있습니다. 

즉 현재 automated consistency gate가 **final Markdown report까지 정확히 검증하지 못했습니다.**

---

### 2. 가장 중요한 것은 `65.07% task completion`의 정의 문제입니다

Phase 4D 개발계획에서는 Task Completion을 명시적으로:

> 모든 필요한 fields/claims가 생성되었는가

로 정의했습니다. 

하지만 raw 418 COMMIT-eligible cases를 다시 계산하면 C8은:

* **224 complete verified answers**
* **48 safe partial answers**
* **146 fail-closed/no-answer**

입니다.

따라서:

$$
224/418 = 53.59\%
$$

가 **complete claim-set accuracy**이고,

$$
(224+48)/418 = 65.07\%
$$

는 **supported-answer coverage**입니다.

즉 현재 report가 주장하는:

> C8 65.07% vs C1 53.11%, +11.96% task-completion superiority



는 엄밀하게는 동일한 endpoint 비교가 아닙니다.

동일한 complete-answer 기준으로 비교하면:

* C1 = **53.11%**
* C8 = **53.59%**

차이는 **+0.48 percentage point**입니다.

matched raw cases를 보면 discordant pair가 `C1 wrong / C8 correct = 2`, 반대가 0이라 exact McNemar two-sided `p = 0.5`입니다.

즉 **complete-task superiority는 통계적으로 증명되지 않았습니다.**

그렇다고 결과가 나쁜 것은 아닙니다. 오히려 논문의 이야기를 다음처럼 바꾸면 더 강하고 정직합니다.

> C8 maintained approximately the same complete-answer accuracy as Naive RAG while converting additional failures into safe partial verified answers and preventing unsupported accepted claims.

이것이 훨씬 흥미로운 결과입니다.

---

### 3. Qwen external evaluation은 실제로 N=200이 아니라 N=10입니다

Phase 4D report는 FinQA N=200, HaluEval N=200을 두 model family에서 평가한 것처럼 서술합니다. 

하지만 zip의:

```text
external_generalization_summary.csv
stat_generalization_actual.csv
```

를 직접 확인하면:

```text
Qwen FinQA       N = 10
Qwen HaluEval    N = 10
```

입니다.

따라서 현재의:

> Phi 6% → Qwen 70%

같은 결과는 **10-case pilot**이지 200-case cross-model replication이 아닙니다.

Phase 4D final evidence report도 이 결과를 강한 model-scaling evidence로 해석하고 있습니다. 

이 상태로 SCI 논문에 넣으면 reviewer가 바로 문제를 제기할 가능성이 높습니다.

---

### 4. 계획했던 진짜 constrained-decoding baseline이 final artifact에 없습니다

Phase 4D implementation plan에는 명확하게:

> `lm-format-enforcer` v0.11.3을 실제 logits processor로 사용

한다고 되어 있습니다. 

하지만 업로드된 Phase 4D zip에는:

* `lm-format-enforcer` result
* external structured baseline summary
* raw constrained-decoding capture

가 없습니다.

현재 C3는 실제 raw output을 보면 **일반 generation + JSON-schema instruction/post-validation**에 가깝습니다.

따라서 현재 C3를:

> JSON Schema Structured Decoding

이라고 부르는 것도 수정해야 합니다.

두 가지 선택지가 있습니다.

1. 실제 `lm-format-enforcer` baseline을 실행하거나,
2. C3를 **JSON-schema prompted/post-hoc validation baseline**으로 낮춰 표현하는 것.

상위 SCI 저널을 목표로 한다면 1번이 좋습니다.

---

## 반대로 매우 중요한 긍정적 결과도 있습니다

FinQA가 거의 실패했다는 것은 숨길 필요가 없습니다. 실제 Phase 4D failure analysis에서 95.5%가 program execution error였습니다. 

이것은 오히려 논문의 좋은 negative result가 될 수 있습니다.

UIR는:

> **잘못된 arithmetic reasoning을 올바르게 만들어주는 장치가 아니다.**

대신:

> **잘못된 reasoning이 검증되지 않은 결과로 넘어가는 것을 막는 장치이다.**

입니다.

HaluEval에서도 Phi-3.5가 format/evidence contract를 잘 따르지 못하면서 utility가 무너졌습니다. 

따라서 이 논문의 훨씬 강한 최종 결론은:

$$
\boxed{\text{System-level verifiability} \neq \text{Model-level reasoning ability}}
$$

입니다.

UIR는 전자를 강화합니다.

후자는 여전히 base model의 능력에 의존합니다.

이 distinction이 오히려 상당히 좋은 SCI 논문의 결과라고 봅니다.

---

## 현재 단계 최종 평가

| 영역                                    | 판단             |
| ------------------------------------- | -------------- |
| UIR architecture                      | **완료**         |
| Policy Engine                         | **완료**         |
| Formal semantics                      | **완료**         |
| Runtime decoupling                    | **완료**         |
| Real model inference                  | **완료**         |
| Official FinQA/HaluEval               | **완료**         |
| Mutation tests                        | **완료**         |
| Internal raw evidence                 | **강함**         |
| Metric semantics                      | **수정 필요**      |
| Final report consistency              | **수정 필요**      |
| Qwen cross-model evidence             | **N 부족**       |
| Genuine constrained decoding baseline | **누락**         |
| 추가 architecture 개발                    | **불필요**        |
| 바로 논문 작성                              | **아직 한 단계 이름** |

그래서 **Phase UIR-4E Final Publication Reconciliation** 작업지시서를 작성했습니다.

[Phase UIR-4E Final Publication Reconciliation 작업지시서](sandbox:/mnt/data/CODEX_UIR_PHASE4E_FINAL_PUBLICATION_RECONCILIATION_WORK_ORDER.md)

이번 Phase 4E는 지금까지와 달리 **새 기능을 개발하는 Phase가 아닙니다.**

핵심은 네 가지뿐입니다.

1. 현재 600-case Phi raw output을 다시 생성하지 않고 **한 개의 frozen scorer로 재계산**
2. `complete answer / safe partial / no verified answer`를 명확히 분리
3. Qwen FinQA/HaluEval을 실제 **N=200씩** 완료하고 raw capture 저장
4. 실제 `lm-format-enforcer` 같은 constrained-decoding baseline을 추가

그리고 마지막으로 모든 표를 사람이 복사하지 못하도록:

```text
raw JSONL
→ final CSV
→ statistics
→ Markdown table
→ LaTeX table
```

을 자동 생성하게 했습니다.

Phase 4E에서 최종적으로:

```text
READY_FOR_MANUSCRIPT_DRAFT_FINAL
```

이 나오면 **그때는 정말 추가 개발을 중단하는 것이 맞습니다.**

그 후 작성할 논문은 기존 preview와 상당히 달라져야 합니다. 중심 주장은 “UIR이 모든 task에서 RAG보다 정확하다”가 아니라,

> **UIR separates probabilistic model reasoning from deterministic evidence and policy authority, transforming unsupported or uncertain model behavior into verified answers, safe partial answers, or explicit abstention rather than silently accepted fabrication.**

가 되어야 합니다.

저는 이 framing이 지금까지 나온 **positive result와 negative result를 모두 정직하게 설명하면서도 오히려 훨씬 수준 높은 논문**으로 만드는 방향이라고 판단합니다.
