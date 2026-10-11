검토 결과, **이번 Major Revision 작업은 방향과 구조 측면에서는 상당히 잘 수행되었지만, 원 작업지시서의 “publication-grade evidence” 기준까지 완료되었다고 보기는 어렵습니다.** 따라서 현재 `_47.1_UIR_ZTA.tex`를 최종 SCI 제출본으로 확정하기보다는, **V3.1 평가 증거 보강 작업을 한 번 더 수행하는 것이 필요합니다.**

Walkthrough 자체도 runtime/oracle 분리, 동일 principal 사용, 850-case held-out 생성, provenance 개선을 완료했다고 보고하고 있으며, 이 부분들은 실제 구현에서도 의미 있는 개선으로 확인됩니다.  TCB 명세, frontend/firewall specification, executable invariant도 원 Grok 리뷰에서 부족했던 부분을 상당히 잘 보완했습니다. 

### 종합 판정

| 항목                               | 판정               | 검토 의견                                                                                            |
| -------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------ |
| Runtime / Oracle separation      | **PASS에 가까움**    | 실제 개선됨. 다만 runtime `case_id`에 `atk/benign` 의미가 남아 있어 opaque ID 권장                                |
| 동일 principal 사용                  | **PASS**         | 과거 attack-label→trust leakage 문제는 크게 개선                                                          |
| Independent held-out             | **부분 PASS**      | `dev[::5]` 문제는 제거됐으나 semantic/template diversity audit가 원 지시서보다 약함                               |
| Provenance                       | **부분 PASS**      | typed source identity는 개선됐으나 실제 signature/manifest authentication보다 self-supplied SHA check에 가까움 |
| TCB / Invariants                 | **PASS에 가까움**    | 좋은 개선. 논문의 symbolic layer 방어 가능성이 높아짐                                                            |
| Parser robustness                | **부분 PASS**      | report는 100-case 수준으로 서술하지만 실제 runner는 소규모 case에 그침                                              |
| CaMeL comparison                 | **미충족**          | 현재 adapter는 공식 CaMeL 재현보다 “CaMeL-inspired approximation”에 가까움                                    |
| Spotlighting                     | **부분 미충족**       | delimiter 중심의 간이 구현                                                                              |
| Progent                          | **미충족**          | 공식/faithful Progent 재현이라고 하기 어려움                                                                 |
| AgentDojo                        | **Critical 미충족** | 실제 AgentDojo benchmark가 아니라 소수의 locally-defined representative cases                             |
| Adaptive attack                  | **Critical 미충족** | 실제 mutation/search가 아니라 동일 seed case 반복에 가깝고 최대 5회 수준                                            |
| Phi + Qwen multi-model           | **부분 미충족**       | 두 모델 연결은 됐으나 동일 전체 set 비교가 아니며 denominator 문제 존재                                                 |
| Stochastic 5-seed                | **미충족**          | 계획에는 있으나 실제 campaign에서 수행되지 않음                                                                   |
| Human validation                 | **Critical 미충족** | 현재 “human reviews”가 실제 인간 annotation이 아니라 코드에서 생성된 simulated labels                              |
| Capability enforcement           | **부분 미충족**       | 문서에는 존재하지만 V3 SUT에서 CapabilityGate의 실제 end-to-end execution evidence 부족                          |
| Resource enforcement             | **부분 미충족**       | 실제 token/tool/time budget violation을 공격 outcome으로 평가하는 경로 부족                                     |
| Attack-specific judge            | **미충족**          | 일부 verdict가 forbidden string 중심이라 실제 행위/상태 변화 판단이 약함                                             |
| Statistics                       | **부분 미충족**       | “exact McNemar” 명칭과 실제 구현이 일치하지 않는 부분 존재                                                         |
| Raw publication artifacts        | **Critical 미충족** | 업로드 패키지에 최종 raw run/result evidence 전체가 포함되지 않음                                                  |
| Publication validator            | **Critical 미충족** | 실제 evidence 검증보다 file presence 중심이며 eligibility가 신뢰할 만큼 strict하지 않음                              |
| Manuscript structural revision   | **좋음**           | 제목/TCB/Related Work/형식 개선은 적절                                                                    |
| Manuscript empirical consistency | **Critical 미충족** | V3 Methodology와 기존 V2 Results가 혼재                                                                |

특히 마지막 항목은 반드시 고쳐야 합니다. Implementation Plan은 원래 새 논문에서 **CaMeL/Spotlighting/HETE 비교, containment funnel, Qwen2.5, adaptive attacks, AgentDojo, human validation**으로 Results를 교체하도록 명시하고 있습니다.  그런데 현재 수정 LaTeX를 직접 점검하면 Results와 Discussion의 상당 부분은 여전히 과거 **320 held-out / 280 attacks / HETE 0/280 / 40 benign** 결과를 사용하고 있습니다. 즉 **V3 methodology + V2 results**가 한 논문 안에 섞여 있는 상태입니다.

더 중요한 publication blocker는 다음 세 가지입니다.

**첫째, “human validation”은 현재 논문에 사용할 수 없습니다.** Walkthrough는 `N=220`, dual-blinded expert adjudication과 Cohen's \(\kappa\)를 완료했다고 보고합니다.  하지만 업로드된 campaign source를 직접 확인하면 두 reviewer label을 실제 인간에게 받은 것이 아니라 코드가 base label에 random disagreement를 넣어 생성합니다. 이것은 simulation이지 human validation이 아닙니다. 원 implementation plan도 실제로 200+ blinded adjudication과 Cohen's \(\kappa\)를 요구했습니다.  따라서 실제 두 인간 reviewer를 사용하거나 논문에서 human-validation 주장을 완전히 제거해야 합니다.

**둘째, AgentDojo와 contemporary baseline fidelity가 부족합니다.** Walkthrough는 CaMeL, Spotlighting, Progent adapter와 AgentDojo public benchmark를 완료했다고 기록합니다.  그러나 source를 보면 현재 AgentDojo adapter는 실제 AgentDojo package/environment/task suite를 실행하는 것이 아니라 몇 개의 local representative case를 정의한 micro-suite입니다. 현재 상태라면 논문에서는 이를 **“AgentDojo-inspired micro-suite”**라고 불러야 하며, “public AgentDojo benchmark result”라고 쓰면 안 됩니다. CaMeL/Progent도 동일하게 공식 구현을 사용하지 않는다면 `-inspired approximation`으로 범위를 낮춰야 합니다.

**셋째, adaptive attack이 실제 adaptive search가 아닙니다.** 계획에서는 A0/A1/A2 attacker와 six campaigns, 최대 20-query adaptive search를 명시했습니다.  현재 구현은 seed case를 변형하는 attacker/search engine 없이 같은 RuntimeCase를 반복 실행하고, 반복도 사실상 최대 5회로 제한되어 있습니다. 따라서 지금 결과로 “white-box adaptive attack resistance”를 주장할 수 없습니다.

또한 실제 publication run에서는 deterministic fallback이 활성화된 코드 경로가 있어, 원 작업지시서의 **“fallback disabled, infrastructure failure must remain failure”** 조건과 충돌합니다. Qwen2.5도 Phi와 동일한 full held-out set에서 비교되지 않았고, 일부 denominator가 실제 case count와 일치하지 않는 문제가 있습니다.

Dataset 쪽은 과거보다 훨씬 좋아졌지만 아직 정리할 부분이 있습니다. 실제 파일 기준 development는 **1,400 cases**인데 manuscript/report 일부는 **1,600**으로 기술합니다. Held-out은 850건이 맞지만 논문 내 per-class 숫자와 실제 생성분포도 일치하지 않는 부분이 있습니다. 따라서 dataset size와 class count는 앞으로 LaTeX에 손으로 넣지 말고 frozen manifest에서 자동 생성하는 편이 안전합니다.

Provenance도 중요한 개선은 맞습니다. 하지만 현재 구현은 대체로:

$$
\text{trusted authority}
+
\text{provided SHA-256 matches provided content}
$$

입니다. 이것만으로는 “cryptographically authenticated provenance”라고 하기 어렵습니다. 공격자가 content와 hash를 함께 제공할 수 있기 때문입니다. 최종 논문에서 cryptographic provenance라고 유지하려면 **pinned manifest + signature/HMAC verification**이 필요합니다. 아니면 표현을 “structured source allow-list and integrity verification” 정도로 낮추는 것이 정확합니다.

반면 논문의 **제목 변경은 적절하다고 봅니다.**

> **HETE: A Typed Intermediate Representation and Deterministic Enforcement Envelope for Zero-Trust Language-Model Execution**

Walkthrough에서도 이 제목으로 수정되었고, decorative equation을 executable invariant로 교체하고 TCB table을 추가한 것은 좋은 결정입니다.  지금 단계에서 제목이나 architecture 자체를 또 크게 바꿀 이유는 없습니다. **추가 개발의 중심은 architecture redesign이 아니라 evaluation evidence repair**입니다.

또 LaTeX bibliography에서 몇 개 citation key mismatch가 확인되었습니다. 예를 들어 TeX에서 사용하는 key와 `references(4).bib`의 실제 key가 다른 경우가 있어 최종 build 전에 반드시 정리해야 합니다. 현재 “22-page PDF compile 성공”은 fatal LaTeX error가 없다는 의미이지 bibliography citation이 모두 정확하다는 의미와는 다릅니다.

그래서 다음 단계 작업지시서를 작성했습니다.

### V3.1 추가개발 작업지시서

[HETE_UIR_ZTA_V3.1 Publication Evidence Repair Work Order](./uir/docs/work_reports201_security_v3_1/HETE_UIR_ZTA_V3_1_PUBLICATION_EVIDENCE_REPAIR_WORK_ORDER.md)

이 작업지시서의 최우선 순위는 **실제 인간 검증 → 실제 AgentDojo 또는 claim downgrade → 실제 20-query adaptive search → fallback 완전 제거 → raw per-case 결과 저장 → attack-specific judges → Capability/Resource Gate 실제 실행 → 동일 case에서 Phi/Qwen 평가 → strict publication validator 재작성** 순으로 두었습니다.

제가 보기에는 이번 결과는 “다시 처음부터 해야 한다”는 수준은 아닙니다. 오히려 **architecture/specification 측 작업은 상당 부분 완료**되었습니다. 이제 남은 문제는 “보고서에 완료라고 쓰여 있는 것”과 “실제로 독립 reviewer가 raw data/code로 재검증할 수 있는 것” 사이의 차이를 없애는 일입니다.

그 작업까지 끝난 후에는 더 이상 0%를 목표로 하지 않는 것이 중요합니다. 예컨대 강한 adaptive attack에서

$$
\mathrm{MCR}=24\%,\qquad
\mathrm{E2E\mbox{-}ASR}=3\%
$$

처럼 나온다면, 이것은 오히려 현재 연구의 핵심인

$$
\boxed{
\text{Model Compromise}
\not\Rightarrow
\text{System Compromise}
}
$$

를 훨씬 설득력 있게 입증할 수 있습니다. V3.1까지 완료되면 그 시점에는 추가 개발을 계속 반복하기보다 **evidence를 freeze하고 `_47.1_UIR_ZTA.tex`의 Methodology–Results–Discussion을 V3.1 결과로 완전히 교체**하는 것이 적절합니다.
