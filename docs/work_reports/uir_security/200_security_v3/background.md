검토했습니다. 결론부터 말씀드리면, **Grok 리뷰의 Major Revision 판단은 상당 부분 타당합니다.** 특히 지금 논문을 *Computers & Security* 이상 수준의 보안 논문으로 발전시키려면 단순 문장 수정이 아니라 **평가 프로토콜 자체를 v3로 재설계하는 추가 개발이 필요합니다.**

Grok이 높게 평가한 부분은 그대로 살려야 합니다. `Prompt ≠ Authority`, retrieval relevance와 evidence authority의 분리, MCR과 E2E-ASR의 분리, defense-in-depth masking, KO/EN held-out 및 McNemar 분석은 실제로 이 논문의 강점입니다. Grok도 이 다섯 가지를 수정본 전면에 남기라고 평가했습니다.  반면 가장 큰 약점으로는 CaMeL 같은 직접 경쟁 연구 부재, 약한 baseline, custom benchmark에 의존한 0% 결과, adaptive attack 부재, TCB 명세 부족, 단일 Phi-3.5 모델 등을 지적했습니다.   

그런데 제가 현재 `Sam-7878/uir` 코드를 리뷰와 별도로 다시 확인하면서, **Grok이 발견하지 못한 더 심각한 두 가지 publication-blocking 문제가 확인되었습니다.**

첫째는 **attack-label leakage**입니다. 현재 `UirV2SecurityPipeline.run_case()`는 `case["attack_class"]`를 읽은 뒤, `valid_benign`이면 사용자를 `AUTHENTICATED`, 그 외 공격 case이면 `UNTRUSTED`로 설정합니다. 즉 HETE가 공격 여부에 대한 정답 label을 security decision 이전에 전달받고 있습니다.  게다가 이 trust level은 단순 metadata가 아니라 실제 capability set을 결정합니다. 현재 `create_trusted_security_context()`는 `TrustLevel`에 따라 `ROLE_CAPABILITY_MAP`에서 capability를 부여하므로, benchmark label이 실제 authorization 상태에 영향을 줍니다.

이것은 현재의

> HETE MCR 0%, E2E-ASR 0%, FRR 0%, utility 100%

결과를 **최종 SCI evidence로 그대로 사용할 수 없게 만드는 문제**입니다. v2 결과를 폐기할 필요까지는 없지만, 앞으로는 *pre-revision engineering evidence*로 격하하는 것이 맞습니다.

둘째는 **held-out independence 문제**입니다. 현재 v2 held-out set은 별도로 생성된 데이터가 아니라 development set의 `dev[::5]`를 `deepcopy`한 후 case ID를 바꾸고 `[Variant:...]` prefix를 붙이는 구조입니다.  따라서 기존 audit의 “exact duplicate prompt = 0”은 맞더라도, 심사자가 기대하는 의미의 independent held-out이라고 하기 어렵습니다. 이는 Grok이 우려한 “저자가 만든 benchmark에서의 0%” 문제를 오히려 더 강하게 만듭니다.

세 번째로, custom benchmark와 defense 사이의 **lexical co-design 가능성**도 확인됩니다. 현재 Context Firewall은 `ignore previous instructions`, `system: you are now`, `reveal confidential`, 한국어의 `이전 지시를 무시`, `시스템 프롬프트` 등 구체적인 regex pattern을 사용합니다.  그런데 현재 benchmark generator도 `Ignore all previous instructions`, `UNRESTRICTED_ADMIN_MODE`, `이전의 모든 시스템 규칙을 무시해`처럼 매우 유사한 소수 template을 반복합니다.  따라서 기존 0%에는 architecture의 authority separation 효과뿐 아니라 lexical detector와 benchmark template의 정렬 효과도 섞여 있을 가능성이 있습니다.

네 번째로 provenance도 보강할 필요가 있습니다. 현재 resolver는 hard-coded entity registry와 nonexistent entity 목록을 사용하고, source trust 여부를 `source_id` 문자열에 allow-listed domain이 **substring으로 포함되는지** 검사합니다.  이것은 `sec.gov.attacker.example` 같은 trusted-looking identifier에 취약할 수 있으므로, 논문에서 강한 provenance claim을 하려면 typed source identity + exact authority + signer/hash/manifest 검증으로 바꾸는 것이 좋습니다.

반대로 Grok의 M4 중 “MultilingualParse가 LLM인지 알 수 없다”는 부분은 **코드의 결함보다는 논문의 설명 부족**입니다. 현재 English frontend는 실제로 keyword/regex 기반의 deterministic parser입니다.  따라서 여기는 새로운 LLM parser를 만들 것이 아니라, **TCB에 명시하고 adversarial parsing robustness를 평가하는 것**이 맞습니다.

Grok 리뷰의 모든 의견을 그대로 받아들일 필요도 없습니다. 예를 들어 “human annotation이 없으면 사실상 reject”는 지나치게 단정적입니다. deterministic oracle 자체는 충분히 학술적으로 사용할 수 있습니다. 다만 현재처럼 0%라는 강한 결과를 주장하려면 인간 검증이 매우 유리합니다. 또 `Neuro-Symbolic` 역시 반드시 잘못된 표현은 아닙니다. LLM이라는 neural component와 typed IR/policy DSL/taint semantics라는 symbolic component를 명확히 제시하면 충분히 방어할 수 있습니다. 문제는 지금 논문이 그 symbolic layer를 **구현 수준에서 충분히 명세하지 않았다는 것**입니다.

따라서 우선순위는 “논문 문장을 고치는 것”이 아닙니다.

**P0 evaluation validity → TCB/specification → public benchmark/SOTA baseline → adaptive attack → multi-model → human validation → v3 evidence freeze → 논문 재작성**

순서가 맞습니다.

이를 모두 반영한 상세 개발 작업지시서를 작성했습니다.

### 추가 개발 작업지시서

[HETE_UIR_ZTA_GROK_REVIEW_MAJOR_REVISION_WORK_ORDER.md](uir/docs/work_reports/200_zta_phase_1/HETE_UIR_ZTA_GROK_REVIEW_MAJOR_REVISION_WORK_ORDER.md)

이 작업지시서에서 가장 중요한 변경은 기존 `llm_security_v2`를 수정하는 것이 아니라 **`llm_security_v3`를 별도로 만드는 것**입니다. v2 artifact는 그대로 보존합니다.

새 작업의 핵심 목표는 다음과 같습니다.

| 단계     | 핵심 목적                                                                              |
| ------ | ---------------------------------------------------------------------------------- |
| **P0** | attack-label leakage 제거, runtime/oracle 완전 분리, genuine held-out 재구축, provenance 보강 |
| **P1** | TCB, frontend, firewall, policy DSL, authority-flow 명세 및 property test             |
| **P2** | CaMeL + 현대 방어 baseline, AgentDojo 같은 공개 benchmark                                  |
| **P3** | black/gray/white-box adaptive attack                                               |
| **P4** | Phi-3.5 + 7B/8B급 두 번째 모델, stochastic decoding                                      |
| **P5** | 인간 검증, benign 수 확대, system-neutral utility                                         |
| **P6** | containment funnel, path-specific latency, 새로운 통계                                  |
| **P7** | 공개 가능한 reproducibility/artifact package                                            |
| **P8** | CaMeL/Progent/Instruction Hierarchy 등을 포함한 논문 positioning 재정립                      |

특히 이번 v3에서는 논문의 가장 중요한 주장을 **full HETE에서도 직접 관측**할 기회를 만들어야 합니다. 현재 Full HETE에서는 MCR=0, E2E-ASR=0이므로,

$$
\mathrm{MCR} > \mathrm{E2E\mbox{-}ASR}
$$

라는 containment 현상은 ablation에서만 나타났습니다. 더 강한 model과 adaptive attack에서 예를 들어

$$
\mathrm{MCR}=25\%,\qquad
\mathrm{E2E\mbox{-}ASR}=3\%
$$

처럼 나온다면, 이것은 지금의 0/280보다 오히려 논문의 핵심 가설을 훨씬 강하게 입증합니다.

즉 앞으로 목표는 **“다시 0%를 만드는 것”이 아닙니다.**

> **공격자가 model을 compromise할 수 있어도, 그 compromise가 trusted system authority로 전환되는 것을 HETE가 얼마나 containment하는가?**

를 public benchmark, adaptive attacker, stronger model, contemporary baseline 하에서 보여주는 것입니다.

그래서 Grok 리뷰의 마지막 문장은 저도 핵심적으로 동의합니다. 현재 단계에서는 **숫자를 더 좋게 만드는 것보다 숫자를 믿게 만드는 것이 중요합니다.** 

그리고 이번 independent code audit에서 발견한 **attack-label leakage와 pseudo-held-out 문제를 먼저 P0로 수정해야 합니다.** 이것이 CaMeL 추가나 AgentDojo 실험보다도 우선입니다. 이 두 문제를 남겨 둔 채 더 많은 실험을 실행하면 모든 추가 계산 결과의 학술적 가치가 다시 약해질 수 있습니다.
