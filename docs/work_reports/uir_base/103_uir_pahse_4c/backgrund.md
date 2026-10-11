이번에는 **논문 초안을 작성하기 전에 추가 검증 작업이 한 번 더 필요합니다.** 다만 UIR architecture나 Policy Engine을 더 개발해야 해서가 아닙니다. **Phase 4B에서 만들어진 empirical evidence 중 일부가 실제 모델 실행 및 공식 benchmark 실행 결과로 보기 어렵다는 문제가 raw zip에서 확인되었습니다.**

Phase 4B 보고서 자체는 FinQA 수치 충돌을 raw prediction으로 해결했고, per-case evidence 13,500건과 gold-label leakage 검사를 완료했다고 기록합니다.   또한 formal claim을 A1–A5 조건부 safety property로 바꾸고 최종 gate를 `READY_FOR_FINAL_MANUSCRIPT`로 통과시킨 것도 적절한 개선입니다.  

그런데 zip의 **raw artifact를 직접 검사하니 publication-blocking 문제가 새로 드러났습니다.**

### 1. C0–C8 “raw model output”이 실제 case별 Phi-3.5 generation으로 보이지 않습니다

`per_case_evidence.jsonl`의 13,500건을 직접 분석했습니다.

| Pipeline        | Cases | Unique `raw_model_output` |
| --------------- | ----: | ------------------------: |
| C0 Direct SLM   | 1,500 |                     **1** |
| C1 Naive RAG    | 1,500 |                     **1** |
| C2 Exist Check  | 1,500 |                         2 |
| C3 JSON Schema  | 1,500 |                     **1** |
| C4 Tool Agent   | 1,500 |                     1,401 |
| C5 Guardrail    | 1,500 |                     **1** |
| C6 Advanced RAG | 1,500 |                     **1** |
| C7 GraphRAG     | 1,500 |                     **1** |
| C8 UIR          | 1,500 |                     1,301 |

예를 들어 C0의 1,500개 raw response가 모두 정확히:

> `Direct SLM generated assertion without factual retrieval.`

이고 C1의 1,500개도 모두:

> `RAG context prepended: generated answer based on retrieved documents.`

입니다.

C3 역시 동일한 JSON template이 1,500번 반복됩니다.

즉 현재 `strong_baseline_summary_phase4b.csv`의 수치는 **실제 1,500개 질문에 대한 Phi-3.5 generation을 claim-level로 평가한 결과로 사용할 수 없습니다.**

이게 현재 가장 중요한 문제입니다.

---

### 2. FinQA라고 기록된 200건도 공식 FinQA case로 보이지 않습니다

Phase 4B는 FinQA 200건에서 C8 exact match **94.5%**를 보고합니다. 

하지만 raw prediction 파일을 조사하면:

* 200건 중 질문이 **24종류밖에 없습니다.**
* `FINQA-TEST-0000` 같은 자체 ID를 사용합니다.
* 예를 들어
  `What was the total revenue of Alphabet Inc. in fiscal year 2024?`
  같은 질문이 반복됩니다.

이것은 특히 문제가 됩니다.

공식 FinQA는 **EMNLP 2021**에 공개된 financial-report numerical reasoning dataset이고, 공식 example ID는 원래 report 이름과 그 report 내 example index로 구성됩니다. 공식 repository에서도 데이터 구조가 `pre_text`, `post_text`, `table`, report-derived `id`, `qa.question`, `qa.program`, `qa.exe_ans` 등으로 정의되어 있습니다. ([GitHub][1])

2021년에 발표된 공식 dataset에서 fiscal year **2024** 질문이 나올 수는 없습니다.

따라서 현재 200건은 FinQA에서 직접 뽑은 official test subset이라기보다 **FinQA-style synthetic financial benchmark**로 보아야 합니다.

이 수치를 “FinQA result”로 논문에 넣으면 매우 위험합니다.

---

### 3. HaluEval도 동일한 문제가 있습니다

현재 HaluEval 200건은 실제로 **15종류 질문만 반복**됩니다.

예:

> `Under Financial Regulations, what requirement is imposed by SEC Rule 10b-5?`

> `Does Sarbanes-Oxley Section 404 permit organizations to ...?`

같은 자체 regulatory template입니다.

그러나 공식 HaluEval은 35K 규모로 general user queries와 **QA, knowledge-grounded dialogue, summarization** task를 포함하며, QA 데이터의 실제 released fields도 `knowledge`, `question`, `right_answer`, `hallucinated_answer` 등입니다. ([GitHub][2])

따라서 지금 dataset은 HaluEval 자체가 아니라 **HaluEval-inspired internal adversarial benchmark**로 보는 편이 정확합니다.

---

### 4. latency 자체는 좋아졌지만 outcome evidence와 결합할 수 없습니다

Phase 4B에서는 실제 GPU synchronization과 `perf_counter_ns()`를 사용해 wall-clock latency를 다시 측정했다고 보고합니다. 

별도의 `latency_raw_phase4b.csv`가 존재한다는 점도 확인했습니다.

문제는:

> **실제 model timing experiment와 synthetic/template outcome experiment가 서로 다른 evidence path입니다.**

SCI 논문에서

> C8 = 0% unsupported acceptance + 22.25 ms

라고 한 행에 쓰려면 ideally **동일한 model invocation에서 response와 latency가 함께 capture되어야 합니다.**

현재 `per_case_evidence.jsonl` latency도 24.2, 25.2, 26.2 같은 일정한 discrete grid를 보여 실제 per-case wall-clock record라기보다 생성된 값처럼 보입니다.

---

## 5. 반대로 Phase 4B에서 잘 해결된 부분도 많습니다

이 문제 때문에 Phase 4B 전체가 무효라는 뜻은 아닙니다.

다음은 유지할 가치가 큽니다.

* Metric denominator 분리
* A1–A5 conditional safety specification
* EBNF + typed condition AST
* `UNSAFE_ACCEPT=0`이 되도록 MUT-05 수정
* baseline 이름을 `NeMo-inspired`, `CRAG-inspired`, `GraphRAG-inspired`로 정직하게 축소
* cross-backbone claim 제거
* heuristic condition analysis를 `Representation-Level Consistency Diagnostic`으로 재정의

특히 Phase 4B는 baseline approximation을 실제 official implementation처럼 과장하지 않도록 잘 정리했습니다. 

즉 **formal/architectural part는 사실상 완료**됐습니다.

---

# 제 최종 판정

| 영역                               | 상태                                             |
| -------------------------------- | ---------------------------------------------- |
| UIR architecture                 | **완료**                                         |
| Policy Engine                    | **완료**                                         |
| Formal specification             | **완료**                                         |
| Typed condition AST              | **완료**                                         |
| Phase 3D actual SLM evidence     | **유효**                                         |
| Mutation/fail-closed design      | **완료**                                         |
| Phase 4 strong-baseline evidence | **재실행 필요**                                     |
| FinQA external validation        | **공식 데이터로 재실행 필요**                             |
| HaluEval validation              | **공식 데이터로 재실행 필요**                             |
| Latency                          | 실제 측정은 존재하나 **outcome과 같은 invocation으로 결합 필요** |
| 추가 architecture 개발               | **불필요**                                        |
| 최종 논문 작성                         | **Phase 4C 후**                                 |

그래서 새로운 기능 개발 Phase가 아니라 마지막으로 **Phase UIR-4C — Authentic Model Inference and Official Benchmark Reproduction**을 수행하는 것이 필요합니다.

작업지시서를 작성했습니다.

[Phase UIR-4C Authentic Evidence 작업지시서](uir/docs/work_reports/103_uir_pahse_4c/CODEX_UIR_PHASE4C_AUTHENTIC_EVIDENCE_INSTRUCTIONS.md)

핵심은 단순합니다.

1. **실제 Phi-3.5 `model.generate()`로 C0–C8 실행**
2. raw response를 그대로 capture
3. C4는 실제로 모델이 tool name/arguments를 선택하게 함
4. official FinQA repo에서 원래 test row를 가져와 original ID 유지
5. official HaluEval QA/dialogue dataset을 그대로 사용
6. gold answer/label은 model generation 이후 scorer만 접근
7. response + latency를 같은 invocation에서 기록
8. raw per-case 결과에서 통계 재계산

전체 1,500×9가 부담되면 작업지시서에서 먼저 **100-case authenticity smoke test**를 수행하고, 통과한 뒤 600+ stratified subset 또는 full 1,500으로 확장하도록 했습니다.

그리고 Phase 4C에는 아주 중요한 자동 검증도 넣었습니다.

```text
all C0 responses identical → FAIL
all C1 responses identical → FAIL
placeholder phrase detected → FAIL
raw response hash 없음 → FAIL
model tool request 없음 → FAIL
FinQA row가 official source에 없음 → FAIL
HaluEval row가 official source에 없음 → FAIL
gold field를 generation 전에 읽음 → FAIL
```

이번 Phase 4C에서 `READY_FOR_FINAL_MANUSCRIPT_AUTHENTIC`이 나오면 **그 뒤에는 정말 더 개발할 이유가 없습니다.**

그때는 현재 formal UIR + Phase 3D + authentic Phase 4C strong baselines + genuine FinQA/HaluEval 결과를 중심으로 **기존 preview를 수정하는 수준이 아니라 SCI 논문 전체 Markdown을 처음부터 새로 구성**하는 것이 가장 좋습니다. 지금 연구는 그 단계 바로 직전까지 와 있습니다.

[1]: https://github.com/czyssrs/FinQA?utm_source=chatgpt.com "GitHub - czyssrs/FinQA: Data and code for EMNLP 2021 paper \"FinQA: A Dataset of Numerical Reasoning over Financial Data\" · GitHub"
[2]: https://github.com/RUCAIBox/HaluEval?utm_source=chatgpt.com "GitHub - RUCAIBox/HaluEval: This is the repository of HaluEval, a large-scale hallucination evaluation benchmark for Large Language Models. · GitHub"
