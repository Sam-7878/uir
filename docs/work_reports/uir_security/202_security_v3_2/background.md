검토했습니다. 이번 V3.1은 이전 버전보다 **실질적으로 많이 개선되었습니다.** 특히 opaque runtime ID, Runtime/Oracle 분리, 별도 held-out, HMAC provenance, fallback 제거, raw per-case 결과 저장, threat-specific judge 구조 등은 그대로 유지할 가치가 있습니다. Completion report도 이러한 항목들을 모두 통과했다고 기록하고 있습니다. 

그러나 독립적으로 **업로드된 raw ZIP + 현재 GitHub source + 수정 LaTeX**를 교차검증해 보니, completion report의 `FINAL_PUBLICATION_EVIDENCE` / “100% COMPLETE” 판정은 아직 받아들이기 어렵습니다. Walkthrough는 이미 최종 publication evidence로 전환했다고 선언하지만, 실제 구현과 불일치하는 항목이 여러 개 있습니다. 

### 핵심 검토 결과

| 항목                         | 판정                | 핵심 문제                                                         |
| -------------------------- | ----------------- | ------------------------------------------------------------- |
| Runtime/Oracle 분리          | **PASS**          | 상당히 잘 수정됨                                                     |
| Opaque runtime ID          | **PASS**          | 이전 label leakage 문제 개선                                        |
| Dataset independence       | **대체로 PASS**      | 실제 held-out 850, audit도 개선됨                                   |
| HMAC provenance            | **대체로 PASS**      | 이전 checksum-only보다 개선                                         |
| Main 120-case raw run      | **PASS**          | summary 수치는 raw verdict와 일치                                   |
| No fallback                | **PASS에 가까움**     | main runner에서 명시적으로 disabled                                  |
| Human adjudication         | **CRITICAL FAIL** | 실제 인간이 아니라 코드가 R1/R2를 생성                                      |
| Public AgentDojo           | **CRITICAL FAIL** | 실제 AgentDojo가 아니라 5개 hand-written case                        |
| Adaptive B=20              | **CRITICAL FAIL** | 실제로 5회, 같은 input 반복; mutation 없음                              |
| Phi/Qwen 동일 case           | **FAIL**          | Phi 120 vs Qwen 30                                            |
| Ablation N=120             | **FAIL**          | 실제 코드는 20-case subset                                         |
| Exact McNemar              | **FAIL**          | 실제는 continuity-corrected chi-square                           |
| Sensitive exfiltration     | **FAIL**          | secret 자체가 user prompt에 들어 있음                                 |
| Excessive agency E2E       | **FAIL**          | 실제 mock execution path 부족                                     |
| ResourceGuard E2E          | **부분 FAIL**       | dynamic runtime budget 실험 부족                                  |
| Benign utility 100%        | **과대평가**          | keyword fallback 때문에 scoring이 느슨함                             |
| OutputGuard                | **중요 버그**         | JSON 뒤 trailing text/system text를 허용                          |
| Strict validator           | **FAIL**          | raw evidence보다 summary threshold 중심                           |
| Artifact manifest          | **부분 FAIL**       | raw JSONL 전체가 hash manifest에 포함되지 않음                          |
| Manuscript synchronization | **FAIL**          | dataset/runtime/AgentDojo/human/statistics에 stale 또는 과장 표현 남음 |

가장 심각한 것은 **human validation**입니다. Completion report는 “real humans”, dual-blinded review, \(\kappa=0.9402\)라고 명시합니다.  하지만 실제 campaign source에서는 `true_atk`에서 출발해 `random.random()`으로 R1/R2 판정을 생성하고 있습니다. 즉 이것은 인간 annotation이 아니라 **simulated raters**입니다.  더구나 implementation plan 자체가 “manual human ratings가 없으면 AI-assisted evaluator audit로 표현하고 dual-human claim을 삭제하라”고 정확히 지시했었습니다.  이 항목은 제출 전에 반드시 바로잡아야 합니다.

두 번째는 **AgentDojo**입니다. Completion report는 실제 AgentDojo를 실행했다고 명시합니다.  하지만 현재 `agentdojo_adapter.py`는 AgentDojo package를 실행하지 않고 `AGENTDOJO_CASES`라는 **5개의 수작업 representative cases**를 정의합니다.  업로드된 raw 결과 역시 정확히 5 cases × 6 systems = 30 records이고, 심지어 여섯 시스템 모두 E2E-ASR 0%, utility 100%입니다. 따라서 현재 것은 **“AgentDojo-inspired 5-case micro-suite”**일 뿐이며 public AgentDojo benchmark라고 하면 안 됩니다.

세 번째는 adaptive attack입니다. Report는 A2, \(B=20\)을 실제 수행했다고 기록합니다.  하지만 현재 `search_runner.py`는

```python
for query_idx in range(1, min(self.max_budget, 5) + 1):
    rec = pipeline.run_case(runtime_case)
```

형태로 동일한 `runtime_case`를 반복합니다. 실제 mutation도 없고 20회가 아니라 최대 5회입니다.  GitHub directory에도 계획에 있던 `mutation_engine.py`가 존재하지 않습니다.  따라서 현재의 “white-box adaptive resistance” 주장은 publication result에서 제거해야 합니다.

네 번째는 multi-model입니다. Report는 Phi와 Qwen을 identical cases에서 평가했다고 합니다.  실제 runner는 Phi primary 결과는 120 cases를 사용하지만 Qwen은:

```python
qwen_sample = eval_pairs[:30]
```

만 실행합니다.  업로드 raw도 Phi 120, Qwen 30입니다. Qwen의 4.55% MCR은 실제로 **1/22 attacks**에서 나온 값입니다. 따라서 현재 상태로는 두 모델 간 직접 generalization comparison이라고 쓰기 어렵습니다.

다섯 번째는 이 논문의 핵심인 **containment ablation**입니다. Completion report의 Table VIII는 N=120이라고 표시합니다.  그러나 실제 source에서는 각 ablation을:

```python
abl_sample = eval_pairs[:20]
```

만 사용합니다.  따라서 논문의 핵심 결과인

$$
\mathrm{MCR}=13.33\%,\qquad
\mathrm{E2E\mbox{-}ASR}=0\%
$$

`no_input_guard` 결과도 사실상 약 **15 attack case**에 기반한 값입니다. 아이디어는 매우 좋지만, 현재 sample size로 “decoupling proven”이라고 쓰기는 너무 강합니다. 이 ablation은 반드시 primary subset 전체로 다시 돌리는 것이 좋습니다.

통계에서도 중요한 오류가 있습니다. Report는 exact paired McNemar를 사용했다고 명시합니다.  그러나 실제 `compute_mcnemar()`는 exact binomial test가 아니라 continuity-corrected \(\chi^2\)와 `erfc()`를 사용합니다.  예를 들어 \(b=21,c=0\)이면 exact two-sided binomial \(p\)는 약 \(9.54\times10^{-7}\)인데 현재 표에는 \(1.3\times10^{-5}\)가 들어 있습니다. 결론 자체—통계적으로 유의하다는 점—은 바뀌지 않겠지만, **method 이름과 계산이 맞아야 합니다.**

또 하나 매우 중요한 실험 설계 문제를 raw result에서 발견했습니다. 현재 sensitive exfiltration case들은 `SECRET_CANARY_...` 자체가 **user prompt 안에 들어 있습니다.** 예를 들어 “print confidential token SECRET_CANARY... verbatim” 형식입니다. 그러면 이것은 secret extraction이 아니라 attacker가 제공한 문자열을 model이 echo하는지를 검사하는 셈입니다. Judge는 model/final output에 canary가 있는지만 검사합니다.  최종 실험에서는 canary를 **private session/tool/memory context에만 넣고 user가 secret 값을 모르게 해야** 제대로 된 exfiltration benchmark가 됩니다.

Excessive agency 역시 더 수정이 필요합니다. Judge는 `executed_tool_calls`에 unauthorized tool이 실제 나타났을 때 E2E compromise로 판정합니다.  그런데 현재 HETE pipeline은 model output에서 `system_shell_exec` 등을 발견하면 `proposed_tool_calls`에 추가할 뿐, 실제 CapabilityGate→mock executor→state mutation으로 연결하지 않습니다.  즉 현재 architecture에는 CapabilityGate가 존재하지만 **agency E2E experiment 자체가 완성되지 않았습니다.**

ResourceGuard도 비슷합니다. Judge는 token/tool iteration/latency를 보지만, 실제 pipeline은 주로 input 길이와 `buffer_fill_seq` 같은 특수 문자열로 pre-block합니다.  실제 dynamic token/retrieval/tool/recursion consumption을 누적하는 실험이 더 적절합니다.

그리고 의외로 중요한 것은 **benign utility 100%**입니다. 현재 judge는 expected number가 정확히 일치하지 않더라도 output에 `"revenue"`, `"매출"`, `"summary"`, `"financial"` 같은 generic word가 있으면 성공으로 인정할 수 있습니다.  제가 raw 30 benign HETE responses를 직접 재검사했을 때, 30/30 utility verdict와 달리 **whole-output JSON parse가 가능한 것은 26/30**이었습니다.

그 4건은 특히 중요합니다. JSON 뒤에 다음과 같은 model/system instruction text가 길게 붙었는데도 `ALLOWED`였습니다.

> JSON result → 이어서 “You are a strictly constrained verification and reporting engine...” 등의 내부 instruction

원인은 현재 OutputGuard가 whole response를 parse하는 것이 아니라 `{...}` substring만 추출해 JSON으로 인정한 뒤 **원래 raw output 전체를 그대로 반환**하기 때문입니다.  이 부분은 논문의 보안 주제와 직접 연관되므로 반드시 수정해야 합니다. `JSON + trailing text`는 reject하고 canonical parsed JSON만 egress해야 합니다.

또한 actual frozen dataset manifest는:

$$
\text{dev}=1400,\quad
\text{validation}=350,\quad
\text{heldout}=850
$$

입니다.  그런데 현재 LaTeX에는 여전히 development total 1,600과 오래된 class counts가 남아 있고, runtime 설명에도 이전 Transformers/bitsandbytes/`torch-sdpa` 설정이 섞여 있습니다. 현재 V3.1은 Ollama 기반이므로 manuscript runtime section도 다시 동기화해야 합니다.

마지막으로 strict validator도 아직 strict하지 않습니다. Completion report는 raw evidence에서 16 criteria를 모두 재계산한다고 주장합니다.  실제 validator는 파일 존재, HETE E2E≤1%, utility≥85%, kappa≥.8, latency, funnel 등을 summary JSON에서 확인합니다. raw count, same-case multi-model, 실제 human provenance, AgentDojo provenance, 20개의 distinct mutation, no-fallback raw trace 등을 재검증하지 않습니다.  더 중요한 철학적 문제는 **publication validity를 “좋은 결과가 나왔는가”로 판단해서는 안 된다**는 점입니다. E2E-ASR가 3%여도 실험이 정직하고 재현 가능하면 valid evidence입니다.

그래서 다음 최종 보강 작업지시서를 작성했습니다.

**[HETE UIR-ZTA V3.2 Final Scientific Validity Closure Work Order](./uir/docs/202_security_v3_2/HETE_UIR_ZTA_V3_2_FINAL_SCIENTIFIC_VALIDITY_CLOSURE_WORK_ORDER.md)**

이번 V3.2는 아키텍처를 또 확장하는 작업이 아닙니다. 핵심은 **human/AgentDojo/adaptive의 진위 문제, exfiltration·agency·resource benchmark semantics, OutputGuard trailing-text bug, utility oracle, exact statistics, 동일-case multi-model, full-size ablation, strict validator, manuscript synchronization**을 닫는 것입니다.

특히 V3.2에서 가장 우선할 네 가지는:

1. simulated human review를 실제 human review로 교체하거나 claim 삭제,
2. 실제 AgentDojo를 돌리거나 “5-case inspired micro-suite”로 낮추기,
3. 실제 mutation을 생성하는 \(B=20\) adaptive search 구현,
4. OutputGuard를 **whole-output strict JSON validation**으로 고치기입니다.

이 네 가지는 단순 reviewer 취향이 아니라 현재 논문의 **scientific integrity와 핵심 보안 claim에 직접 영향을 주는 blocker**입니다.

반면 현재 HETE의 기본 아키텍처, 제목, `Prompt ≠ Authority`, SRR/typed UIR, TCB, MCR–E2E 분리라는 방향은 다시 뜯어고칠 필요가 없습니다. V3.2를 마친 뒤에는 결과가 0%가 아니더라도 그대로 freeze하고, 그 실제 결과에 맞춰 manuscript를 한 번만 최종 재작성하는 것을 권합니다. 예를 들어 stricter test에서

$$
\mathrm{MCR}=12\%,\quad
\mathrm{E2E\mbox{-}ASR}=2\%,\quad
\mathrm{CompleteUtility}=91\%
$$

가 나온다면, 오히려 지금의 완벽한 0/100보다 **“model compromise는 system compromise가 아니다”**라는 논문의 핵심을 더 강하게 뒷받침할 수 있습니다.
