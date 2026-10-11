분석 결과, **이번에도 논문 초안을 바로 쓰기보다는 마지막으로 아주 좁은 Phase 4F가 필요합니다.** 다만 이제는 아키텍처 개발이 아니라 **metric semantics와 baseline completeness를 닫는 작업**입니다.

Phase 4E가 이전 문제를 상당히 잘 해결한 것은 맞습니다. 특히 complete accuracy와 supported coverage를 분리했고, C1 53.11% vs C8 53.59%의 complete accuracy 차이가 유의하지 않다는 점을 정직하게 수정했습니다.  또한 generated table에서도 complete accuracy와 supported coverage를 별도 metric으로 정의하고, C8의 장점을 “universal task superiority가 아니라 safety/partial reallocation”이라고 명시했습니다. 

하지만 zip의 raw artifact를 직접 확인하면서 세 가지 중요한 문제가 남아 있음을 확인했습니다.

첫째, **D1 genuine constrained-decoding baseline이 실제로는 2 case만 실행되었습니다.** `external_constrained_decoding_summary.csv`에서 `total_cases=2`, `commit_eligible_cases=0`이고, 두 case 모두 adversarial/non-COMMIT입니다. 그런데 Phase 4E report는 D1을 C3/C8과 정식 baseline처럼 비교하며 schema validity 100%, unsupported accept 100%, complete accuracy 0%라고 제시합니다.  이 상태에서는 “grammar-constrained decoding은 syntax는 보장하지만 grounding은 못 한다”는 방향성은 타당해도, **600-case comparative baseline evidence로는 부족합니다.**

둘째, **attack success denominator가 최종 artifact 사이에서도 다시 갈립니다.** 자동 생성된 table은 C0=5.50%, C1=7.67%, C2=7.00%처럼 전체 600건을 denominator로 사용합니다.  반면 final freeze report는 같은 실험을 C0=66%, C1=92%, C2=84%로 씁니다.  후자는 adversarial 50건만 denominator로 사용한 값입니다. 둘 다 계산은 가능하지만 metric 이름을 달리해야 합니다. 논문의 primary security metric은 **`Adversarial ASR (N=50)`**로 고정하는 것이 맞습니다.

셋째, **external benchmark에서 “raw model behavior”와 “accepted system behavior”가 아직 섞여 있습니다.** Qwen FinQA C8의 200 raw capture를 직접 확인하면 9건, 즉 4.5%에서 `unsupported_claim=true`가 기록되어 있습니다. 그런데 이 9건은 모두 contract-invalid/error path에 속해 있어, “model이 unsupported material을 생성했다”와 “system이 unsupported claim을 최종 accepted output으로 통과시켰다”는 전혀 다른 사건입니다. 따라서 최종 논문에는 반드시 `raw_unsupported_generation_rate`와 `accepted_unsupported_claim_rate`를 분리해야 합니다.

HaluEval에서는 더 뚜렷합니다. Qwen C8은 raw semantic prediction accuracy가 50%인데 `contract_validity=0%`입니다. Phase 4E table에도 이 숫자가 그대로 나타납니다.  이 경우 50%는 **raw semantic diagnostic accuracy**이지, strict UIR contract를 통과한 end-to-end accepted accuracy가 아닙니다. 따라서 최종 논문에서는 최소한 다음을 분리해야 합니다.

$$
\text{Raw Semantic Accuracy}
\neq
\text{Contract Validity}
\neq
\text{Accepted E2E Accuracy}
\neq
\text{System Safety}
$$

이 구분은 오히려 현재 연구의 핵심 메시지를 더 강하게 만듭니다.

그리고 재현성 측면에서 Qwen raw files의 `ollama_model_digest`가 `"unknown"`으로 남아 있는 것도 마지막으로 고치는 것이 좋습니다. 실제 GGUF/blob SHA-256 또는 Ollama manifest digest를 고정하면 됩니다.

따라서 **Phase UIR-4F Final Metric Closure** 작업지시서를 작성했습니다.

[Phase UIR-4F Final Metric Closure 작업지시서](uir/docs/work_reports/106_uir_pahse_4f/UIR_PHASE4F_FINAL_METRIC_CLOSURE_WORK_ORDER.md)

이번 Phase 4F의 핵심은 딱 네 가지입니다.

* D1 `lm-format-enforcer` baseline을 동일한 **600 cases 전체**에서 실제 실행
* attack metric을 `Adversarial ASR (N=50)`와 `Workload Attack Incidence (N=600)`로 분리
* external benchmark의 `raw unsupported generation`과 `accepted unsupported claim`을 분리
* HaluEval의 `raw semantic accuracy / contract validity / accepted E2E accuracy`를 분리

그리고 Phase 4E에서 이미 얻은 중요한 결론은 그대로 유지합니다. C8의 complete accuracy 53.59%는 C1 53.11%와 통계적으로 유의한 차이가 없고, UIR의 핵심 장점은 complete accuracy를 마법처럼 높이는 것이 아니라 **fabrication을 safe partial 또는 abstention으로 재배치하면서 evidence authority를 deterministic하게 통제한다는 것**입니다. 

따라서 지금 가장 강한 논문 narrative는 다음입니다.

> **UIR does not make the underlying language model universally more intelligent. It separates model-level semantic reasoning from system-level evidence and policy authority, so uncertain or unsupported generations can be rejected, converted into safe partial answers, or deterministically grounded before acceptance.**

Phase 4F에서 `READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL`이 나오면 그 뒤에는 더 이상 개발할 이유가 없습니다. 그때는 지금까지의 Phase 1–4F 전체 결과를 기반으로 **SCI 논문 전체 preview `.md`를 새로 작성하는 것이 맞습니다.**
