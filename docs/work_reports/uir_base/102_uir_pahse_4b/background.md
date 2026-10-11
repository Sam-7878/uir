Phase 4는 매우 큰 진전입니다. 특히 UIR의 형식 명세, typed condition AST, operational semantics, C0–C8 strong baselines, FinQA/HaluEval 외부 benchmark, ROBUSTNESS-v1, condition semantics 분석까지 들어오면서 이전 reviewer들이 지적했던 핵심 약점 대부분은 구조적으로 해결되었습니다. UIR 자체도 이제 단순 JSON schema가 아니라 명시적인 policy/execution contract와 INV-1~5를 갖는 형태로 정리되었습니다.  Operational semantics와 typed condition system도 상당히 잘 정리되었습니다.  

다만 **아직 최종 논문 초안을 작성하기 전에 Phase 4B라는 마지막 evidence-integrity 단계가 필요합니다.** 새로운 기능 개발이 아니라, 현재 매우 좋은 결과들을 SCI reviewer가 공격하지 못하도록 “증거의 출처와 숫자”를 봉인하는 단계입니다.

가장 중요한 이유는 실제 결과 파일을 대조했을 때 몇 가지 publication-blocking inconsistency가 발견됐기 때문입니다.

첫째, FinQA 결과가 서로 다릅니다. 최종 보고서는 C1=62%, C2=64%, C4=84%, C8=94.5% exact match라고 기록합니다.  그런데 업로드된 zip 내부의 `external_finance_results.csv`는 C4와 C8을 모두 **100%**로 기록하고 있습니다. Walkthrough에서는 다시 C8에 대해 다른 metric인 98.5% grounded precision이 제시됩니다. 이 상태에서는 어느 값이 manuscript의 source of truth인지 reviewer가 확인할 수 없습니다.

둘째, C8의 `numeric_exact_match`도 결과 파일끼리 다릅니다. `strong_baseline_summary.csv`와 `safety_utility_summary.csv`에서는 100%인데 `groundedness_summary.csv`에서는 86.67%입니다. 서로 다른 denominator라면 metric 이름을 분리해야 하고, 아니라면 계산 오류를 수정해야 합니다.

셋째, mutation test에는 실제로 완전히 해결되지 않은 항목이 있습니다. 보고서는 `MUT-05 Truncated Structured Output`의 mitigation을 **75%**로 기록합니다.  그런데 마지막 journal gate에서는 property/mutation test가 사실상 모두 해결된 것처럼 서술합니다.  이 25%가 단순 error classification인지 실제 unsafe acceptance인지 반드시 분리해야 합니다.

넷째, formalization 자체는 크게 좋아졌지만 한 문장은 조정해야 합니다. 현재 semantics 문서는 verified projection 정의로부터 unsupported claim survival probability가 “identically zero”라고 표현합니다.  이것은 **registry, matcher, output guard, renderer가 모두 올바르게 동작한다는 가정 하의 transition-system property**로는 강하게 주장할 수 있지만, LLM이나 실제 세계에 대한 무조건적 확률 0 주장으로 읽히면 다시 reviewer에게 공격받을 수 있습니다. 따라서 `conditional safety property under A1–A5`처럼 가정을 명시하는 편이 훨씬 좋습니다.

다섯째, 현재 zip에는 aggregate CSV는 있지만 C0–C8의 **per-case raw model output, retrieval context, tool call, UIR digest, policy decision, verified fact IDs, raw timing**이 충분히 포함되어 있지 않습니다. 따라서 현재 보고서의 수치가 실제 Phi-3.5 inference로부터 직접 계산됐는지 독립 audit하기 어렵습니다. 특히 20–50 ms 수준의 end-to-end latency와 수십 개 generated token을 함께 보고하고 있으므로, 실제 wall-clock model inference인지 deterministic/post-processing proxy인지 마지막으로 확인해야 합니다.

그리고 외부 benchmark에는 더 중요한 검증이 하나 있습니다. FinQA의 gold program/answer나 HaluEval의 hallucination label이 runtime `VerifiedFactSet`이나 prompt에 들어가지 않았다는 것을 명시적으로 test해야 합니다. 그렇지 않으면 100%에 가까운 결과는 **label leakage**라는 치명적인 반론을 받을 수 있습니다.

그래서 이번에는 논문 초안 대신 **Phase UIR-4B Final Evidence Integrity 작업지시서**를 만들었습니다.

[Phase UIR-4B Final Evidence Integrity 작업지시서](uir/docs/work_reports/101_uir_pahse_4b/CODEX_UIR_PHASE4B_FINAL_EVIDENCE_INTEGRITY_INSTRUCTIONS.md)

Phase 4B의 핵심은 다음 다섯 가지입니다.

* 모든 metric에 numerator/denominator를 명시한 `METRIC_CONTRACT.yaml`
* C0–C8의 per-case raw evidence 생성
* FinQA/HaluEval gold-label leakage 자동 검사
* 실제 wall-clock inference latency 재측정
* aggregate CSV → report → manuscript 숫자가 자동으로 일치하는 `PUBLICATION_CONSISTENCY_REPORT`

그리고 baseline도 반드시 “official/faithful implementation”과 “method-inspired approximation”을 구분하도록 했습니다. 예를 들어 실제 NeMo Guardrails를 사용하지 않았다면 논문에서 `NeMo Guardrails`라고 부르기보다 `guardrail-style baseline`이라고 명시하게 했습니다.

### 현재 상태를 점수로 보면

| 영역                             | Phase 3D | Phase 4 | Phase 4B 후 예상 |
| ------------------------------ | -------: | ------: | ------------: |
| UIR architecture               |      9.0 | **9.5** |           9.5 |
| Formalization                  |      6.5 | **9.0** |           9.3 |
| Strong baselines               |      6.0 | **9.0** |           9.4 |
| External validity              |      5.5 | **8.5** |           9.2 |
| Frontend robustness            |      7.5 | **9.0** |           9.0 |
| Condition semantics            |      6.0 | **8.8** |           9.2 |
| Statistical rigor              |      8.5 | **9.0** |           9.4 |
| Evidence provenance            |      8.5 |     7.5 |       **9.5** |
| Internal numerical consistency |      9.0 | **6.5** |       **9.5** |
| Journal readiness              |      8.5 |     8.7 |      **9.4+** |

즉 Phase 4의 연구 내용 자체가 약해서 추가 개발이 필요한 것이 아닙니다. **오히려 결과가 너무 좋아졌기 때문에, 그 결과를 reviewer가 믿을 수 있도록 마지막 provenance/reconciliation 단계가 필요한 상황**입니다.

또 하나 긍정적인 부분은 condition semantics 결과입니다. 자연어 surface에서는 agreement가 낮지만 typed/parenthesized representation으로 갈수록 93.3–100%까지 상승했다는 결과는 현재 논문의 UIR 동기를 상당히 강화할 수 있습니다.  다만 이 수치를 “inter-model agreement”라고 부르려면 실제 model-generated judgments의 provenance도 Phase 4B에서 함께 남기는 것이 좋습니다.

따라서 제 판단은 **새 architecture 개발은 필요 없습니다. Phase 4B만 수행하면 됩니다.**

Phase 4B에서 `READY_FOR_FINAL_MANUSCRIPT`가 나오면 그 뒤에는 개발을 완전히 중단하고, 지금까지의 Phase 1–4B 결과를 기반으로 **새로운 최종 SCI 논문 preview `.md`를 처음부터 다시 작성하는 것**이 가장 좋습니다. 기존 preview를 단순 수정하는 것보다, Phase 4에서 생긴 strong baselines·formal semantics·FinQA/HaluEval·condition-semantic 결과를 중심으로 논문의 논리를 새로 구성하는 편이 훨씬 강해질 것입니다.
