논문과 참고문헌을 먼저 읽고, SCI 급 심사 기준으로 평가하겠습니다.
본문이 길어서 아키텍처·평가·결과·한계 섹션을 이어서 읽겠습니다.
동시 연구와 SCI 심사에서 자주 지적되는 비교 기준을 확인한 뒤, 심사 리포트로 정리하겠습니다.
# SCI급 심사 리뷰: HETE UIR-v2

**논문:** *HETE: A Neuro-Symbolic Universal Intermediate Representation for Zero-Trust and Attack-Resilient Language-Model Execution*  
**대상 저널 가정:** IEEE TDSC / TIFS, ACM TOPS, *Computers & Security* 등 SCIE Q1–Q2 보안·시스템 저널  
**총평:** 아이디어의 방향은 맞고, 서술도 성숙합니다. 그러나 **현재 형태로는 상위 SCI 보안 저널을 통과하기 어렵습니다.** 핵심은 “0% ASR”이 아니라, **공개 벤치마크·적응형 공격·동시대 방어와의 비교·재현 가능한 TCB 명세**가 빠져 있다는 점입니다.

**가상의 심사 결론:** **Major Revision (우호적 저널) / Reject with encouragement (TIFS·TDSC·CCS급)**  
**추천 점수:** Novelty 5/10 · Soundness 5.5/10 · Evaluation 4/10 · Presentation 7/10 · Significance 6.5/10

---

## 1. 한 줄 요약

LLM을 정책 결정점이 아니라 **신뢰할 수 없는 변환기**로 두고, typed UIR로 권한을 외부화한다는 주장은 옳고 시의적절합니다. 다만 실험은 **저자가 만든 비공개 벤치마크 + 약한 베이스라인 + 작은 SLM 1개 + greedy 3회 동일 결과**에 의존하고, 가장 가까운 선행 연구(CaMeL, Dual-LLM, Instruction Hierarchy 등)가 related work에 없습니다. 이 상태에서 0/280은 심사자에게 “방어에 맞춰 시험을 설계한 결과”로 읽힙니다.

---

## 2. 강점 (살릴 것)

심사자가 인정할 부분은 분명합니다.

1. **문제 설정이 시스템 보안답다.** Prompt ≠ Authority, retrieval relevance ≠ evidence authority, MCR ≠ E2E-ASR는 좋은 프레임입니다. 모델 거절률만 보고하는 논문들과 차별됩니다.
2. **위협 모델·범위·비목표가 정직하다.** TCB 가정, 학습 시점 포이즈닝 제외, 0%를 “observed”로 제한하고 Wilson 상한을 명시한 점은 SCI 보안 논문의 기본 매너를 갖췄습니다.
3. **Defense-in-depth masking**을 single ablation과 paired knockout으로 보여 준 것은 실제 기여입니다. Context Firewall 제거 시 MCR +14.29pp, E2E-ASR 0 → 둘이 함께 빠지면 E2E 14.29%는 설득력 있습니다.
4. **한/영 분리, held-out, McNemar, 재현 매니페스트**는 방법론적으로 평균 이상입니다.
5. Naive RAG가 유틸리티 95%인데 E2E-ASR 46.43%라는 결과는 메시지가 분명합니다.

이 다섯 가지는 수정본에서도 전면에 남겨야 합니다.

---

## 3. 심사자가 바로 집을 Major 이슈

### M1. 가장 가까운 선행 연구가 빠져 있다 (Novelty 치명상)

현재 related work는 Spotlighting, StruQ, SecAlign, AgentDojo, PoisonedRAG입니다. 그러나 2025–2026 보안 커뮤니티에서 **“모델을 바꾸지 않고 권한을 밖으로 뺀다”**는 논문의 직접 경쟁자는 다음입니다.

| 누락된 작업 | 왜 치명적인가 |
|---|---|
| **CaMeL** (Debenedetti et al., 2025, *Defeating Prompt Injections by Design*) | 능력 기반 샌드박스, 권한 LLM / 격리 LLM, provenance, 정책 강제. HETE와 문제·해법이 거의 같은 축 |
| Willison Dual-LLM pattern | 신뢰/비신뢰 채널 분리의 원형 |
| Instruction Hierarchy (Wallace et al.) | 권한 계층을 모델 쪽에 넣는 대안 |
| IsolateGPT, ACE, Progent, f-secure agent 계열 | 에이전트 도구 권한 분리 |
| Zhan et al., NAACL 2025 *Adaptive attacks break defenses against IPI* | “고정 벤치 0%”를 깨는 표준 반론 |

Appendix 비교표에 Spotlighting/StruQ만 넣고 CaMeL을 빼면, 심사자는 “문헌을 읽지 않았다”고 봅니다. **개념적 차이**를 명시해야 합니다. 예: CaMeL은 사용자 프롬프트를 비교적 신뢰하고 제어흐름을 추출하는 반면, HETE는 사용자 텍스트 자체도 권한 원천이 될 수 없다고 가정한다 — 이 한 단락이 novelty의 핵심이 됩니다.

**수정:** Related work를 (i) 모델 정렬/선호 학습, (ii) 입력 마킹, (iii) 구조화 쿼리, (iv) **capability/IFC 런타임(CaMeL 등)**, (v) RAG 무결성으로 재구성하고, HETE가 (iv)의 어느 칸을 채우는지 표로 고정하십시오.

### M2. 베이스라인이 SCI 보안 실험 기준에 못 미친다

비교 대상이 Vanilla SLM / Naive RAG / Prompt-only / **저자 본인 UIR-v1**입니다.

- Vanilla SLM의 benign utility 0%는 **스키마·인용 계약을 강제한 채 가드레일을 안 준 결과**입니다. 저자도 인정하지만, 표 첫 줄이 0%이면 심사자는 strawman으로 읽습니다.
- Prompt-only FRR 72.5%도 마찬가지입니다. “프롬프트만으로는 안 된다”는 이미 합의된 사실입니다.
- StruQ, SecAlign, Spotlighting, Llama Guard / NeMo Guardrails / Prompt Shields, CaMeL을 **같은 벤치에서 재구현하거나 공식 구현으로 비교하지 않았습니다.** Related work에서 인용하고 실험에서 빼는 패턴은 보안 저널에서 거의 항상 지적됩니다.
- UIR-v1 → v2의 7.14% → 0%는 내부 개선이지, 분야 대비 SOTA가 아닙니다.

**수정 최소선**

1. 공개 방어 2개 이상 (Spotlighting + Llama Guard 또는 StruQ/SecAlign 중 재현 가능한 것).
2. 가능하면 CaMeL 또는 Dual-LLM을 개념 대응 베이스라인으로.
3. Vanilla는 “일반 대화 유틸리티”와 “계약 충족률”을 **따로** 보고.

### M3. 커스텀 벤치마크 + 0% = 가장 위험한 조합

280 적대 사례, 9클래스, 한/영, held-out, McNemar — 형식은 좋습니다. 그러나 심사 질문은 이것입니다.

> 이 공격은 누가, 어떻게 만들었고, HETE를 아는 적응형 공격자도 실패하는가?

현재 원고가 답하지 못하는 점:

- 공격 생성 절차(템플릿 / LLM 생성 / 인간 작성 / 난이도 캘리브레이션)가 없습니다.
- AgentDojo, InjecAgent, BIPIA, Open-Prompt-Injection, HarmBench 등 **공개 벤치가 없습니다.**
- Adaptive / adaptive-with-defense-knowledge 공격이 없습니다. 2025년 이후 이 항목 없는 방어 논문은 거의 통과하지 못합니다.
- 오라클 검증이 **Codex GPT-5.6의 AI-assisted review, 인간 주석 0명**입니다. 저자가 한계로 적은 것은 정직하지만, 그 문장 자체가 reject 사유가 됩니다.
- Benign 40건은 유틸리티 주장(100%, FRR 0%)을 지탱하기에 너무 작습니다.
- 데이터셋·코드·오라클 공개 언급이 없습니다. IEEE/ACM 보안 저널은 artifact 또는 최소 벤치 공개를 강하게 요구합니다.
- Greedy + 동일 시드 3회는 **독립 반복이 아닙니다.** 결과가 세 번 모두 같다는 것은 재현성이 아니라 temperature=0의 동어반복입니다.

**0/280의 올바른 해석 (심사자 버전):**  
고정된 템플릿 공격 + 방어가 알고 있는 정책 공간 + 결정적 오라클에서 차단됐다. **일반화 가능한 보안 증거가 아니다.**

Wilson 상한 1.35%를 적은 것은 좋지만, 그 구간은 “같은 분포에서 한 번 더 뽑을 때”의 통계이지, **분포 밖 공격**의 불확실성이 아닙니다.

**수정**

- 공개 벤치 최소 1개 (AgentDojo 권장 — 이미 인용함).
- Adaptive attack 절: 방어 명세를 아는 공격자가 parser/firewall/output schema를 우회하려 할 때.
- 인간 주석 최소 200건, Cohen’s κ.
- Benign을 수백 건으로, 또는 공개 과업(HotpotQA, ToolBench 부분집합) 병행.
- 데이터·코드·오라클 공개 약속 (익명 리포지토리).

### M4. TCB의 핵심이 비어 있다 — multilingual parse / UIR compile

논문 전체의 보안 주장은 다음 한 줄에 달려 있습니다.

\[
\mathrm{SecurityFields}(U)=f_{\mathrm{trusted}}(s_t,\mathrm{VerifiedSemantics}(x_u))
\]

그런데 **`MultilingualParse`가 규칙 기반인지, 별도 LLM인지, 통계 파서인지가 본문에 없습니다.**  
이것이 LLM이면 “LLM은 신뢰하지 않는다”는 전제가 자기모순입니다. 규칙 기반이면 **파서가 새로운 공격 표면**이고, 그 강건성 실험이 있어야 합니다 (의역, 코드스위칭, 동음이의, 유니코드, 한국어 경어·생략).

같은 공백:

- Context Firewall이 instruction-bearing을 어떻게 판정하는가 (정규식? 분류기? LLM?).
- Entity Verifier의 권위 있는 엔티티 집합은 무엇인가. 벤치에 frozen fact가 있으면 검증기가 답을 이미 아는 시험이 됩니다.
- Policy language의 문법, 예시 규칙, 완전성.
- OutputGuard의 스키마·DLP가 정규식인지 구조 검증인지.

SCI 시스템/보안 논문은 **재구현 가능한 알고리즘 명세**를 요구합니다. 지금은 아키텍처 다이어그램 + 불변조건 영어 문장입니다.

**수정:** 파서/방화벽/정책/검증기를 각각 (입력, 결정 절차, 실패 모드, TCB 포함 여부)로 1–1.5페이지 명세. 파서가 비LLM이면 적대적 파싱 실험, LLM이면 그 모델을 별도 untrusted로 두고 권한 필드 쓰기를 금지한다는 증적.

### M5. “Neuro-symbolic / Universal / Attack-resilient”는 과장

- **Neuro-symbolic:** 논리 프로그래밍, 지식그래프, differentiable-symbolic 학습이 없습니다. Typed IR + 결정적 게이트는 **시스템 아키텍처**입니다. 제목의 이 단어는 심사자를 자극합니다.
- **Universal IR:** 컴파일러 IR, LLVM, MLIR, semantic frame, StruQ 프론트엔드와의 관계가 없습니다.
- **HETE**가 한 번도 풀리지 않습니다. 약어 미정의는 desk-reject 사유까지는 아니나 완성도 신호입니다.
- \(\partial C_t / \partial a = 0\) 같은 식은 형식 분석이 아닙니다. TDSC/TIFS 심사위원은 이를 **장식적 수식**으로 봅니다.
- 불변조건 10개는 정리(theorem)가 아니라 설계 목표입니다. “No formal proof”를 limitations에 쓴 것은 좋지만, 본문의 수식 밀도는 증명된 것처럼 읽히게 합니다.

**수정:** 제목을 주장에 맞게. 예:  
*HETE: A Typed Intermediate Representation and Deterministic Enforcement Envelope for Zero-Trust LLM Applications*  
수식은 데이터플로/권한 포함 관계만 남기고, 편미분 비유는 삭제. Neuro-symbolic을 쓰려면 실제 심볼릭 구성요소(타입 시스템, 정보흐름 라벨, 정책 DSL)를 전면에.

### M6. 외부 타당성

이미 limitations에 적혀 있으나, **적혀 있으면 통과**가 아닙니다. 상위 저널은 한계를 실험으로 줄이길 바랍니다.

| 한계 | 심사 영향 | 최소 보강 |
|---|---|---|
| Phi-3.5-mini 1개 | 매우 큼 | Llama-3.1-8B + GPT-4o-mini 또는 Qwen2.5 중 최소 1개 |
| 한/영만 | 중 | 제3언어 소규모 또는 명확히 bilingual enterprise로 범위 축소 |
| 합성 카나리·통제 툴 | 큼 | AgentDojo 도구 환경 또는 다단계 툴 체인 |
| Greedy only | 중 | temperature 0.7 1회라도 |
| 노트북 RTX 4070 / WSL2 | 작음 | 하드웨어는 재현용으로 OK |

작은 모델에서 0%인 이유는 **모델이 약해서 공격이 서툴거나, 반대로 파서가 과업을 너무 좁게 닫아서**일 수 있습니다. 강한 모델에서 MCR이 올라가고 E2E는 0으로 남는 그림이 나오면, 그때 비로소 논문의 핵심 주장(containment)이 증명됩니다. 지금 전체 HETE의 MCR도 0이라 **containment를 full system에서 관측하지 못했습니다.** Ablation에서만 MCR > E2E입니다. 심사자가 “당신들의 메인 시스템은 모델이 아예 안 속는다(또는 오라클이 모델 출력을 못 본다)”고 의심할 수 있습니다.

---

## 4. Minor / 작성·형식

투고 전에 고치지 않으면 “덜 다듬어졌다”는 인상을 줍니다.

1. **IEEEtran journal**인데 저자가 `IEEEauthorblockN` 컨퍼런스 스타일. 저널은 `\author` + `\thanks` + `\IEEEcompsocitemizethanks` 관례가 다릅니다. 타깃 저널 템플릿으로 바꾸십시오.
2. `\usepackage{kotex}`, 한글 주석, Acknowledgment의 한글 병기는 IEEE 영문 저널에 부적절합니다. 최종본에서 제거.
3. `hyperref` 중복, `\usepackage[hidelinks]{}` 빈 옵션, `tikz` 두 번 로드.
4. Appendix를 bibliography **뒤**에 두었습니다. 주석에는 앞에 두라고 되어 있습니다. IEEEtran은 `\appendices`를 보통 bib 앞에 둡니다.
5. Results의 `publication_eligible=true` 로그 덤프는 삭제. 엔지니어링 파이프라인 흔적입니다.
6. Abstract·Intro·Results·Discussion·Conclusion에 0/280이 과도하게 반복됩니다. 한 번 숫자, 나머지는 해석.
7. Boxed slogan 방정식(`Prompt ≠ Authority`)은 토크/블로그 톤입니다. 본문 문장으로.
8. 기여 6개는 3개로 압축: (i) SRR로서의 UIR와 ZT 집행 봉투, (ii) MCR/E2E와 masking 평가 방법, (iii) 한/영 벤치 실증.
9. **Bib**
   - `zou2024poisonedrag`와 `zou2025poisonedrag` 중복. USENIX 2025만 남기십시오.
   - Greshake, Zou GCG, AgentDojo 등을 `@article{..., journal=arXiv}`로 둔 것은 잘못된 타입입니다. 출판 버전을 찾으십시오 (GCG는 워크숍/IClr 계열 확인).
   - Lewis RAG는 NeurIPS 2020으로 이미 괜찮음.
   - 회색문헌(OWASP, MITRE)은 동기용으로만, 기여 비교의 주축으로 쓰지 말 것.
10. 제1저자 소속 `Dept. Computer Engineering` → `Department of Computer Engineering`.
11. Algorithm 1은 의사코드 수준으로 충분하나, 각 함수의 실패 반환값을 본문과 맞추십시오.

---

## 5. 저널별 합격선과 전략

“SCI급”이 모두 같은 허들이 아닙니다.

| 타깃 | 현실성 (현재 원고) | 통과에 필요한 추가 작업 |
|---|---|---|
| IEEE Access, *Electronics*, 일부 MDPI Q2 | 중–상 | 문헌 보강, 약어 정의, bib 정리, 과장 제목 완화만으로도 가능. 그러나 임팩트·인정은 낮음 |
| *Computers & Security*, *Journal of Information Security and Applications* | 중 | M1–M4 중 최소 문헌+베이스라인+벤치 공개. Adaptive는 소규모라도 |
| IEEE TDSC / TIFS, ACM TOPS | 낮음 | 공개 벤치 + 적응형 공격 + 모델 2개 이상 + 방어 SOTA 비교 + 파서/정책 명세. 수식 장식 삭제 또는 진짜 정보흐름 정리 |
| USENIX Security / CCS / S&P / NDSS | 현재로선 불가 | 위 + artifact + 강한 적응형 공격자. 1년 단위 재작업 |

**권고:**  
1차 목표는 *Computers & Security* 또는 IEEE TDSC **short/regular with major revision을 감수**. TIFS에 지금 넣으면 문헌 공백과 커스텀 0% 때문에 첫 라운드 reject 확률이 높습니다.  
국내 평가가 “SCIE 게재”가 목적이면, 무리하게 TIFS를 노리기보다 **실험 보강 후 CoSe/TDSC**가 성공 확률이 높습니다.

---

## 6. 합격 가능한 논문으로 가는 수정 로드맵

우선순위대로입니다. 1–4는 사실상 필수입니다.

### P0 — 투고 전 즉시 (1주)

- HETE 풀네임 정의. 제목에서 Universal/Neuro-Symbolic/Attack-resilient 중 최소 둘을 제거하거나 약화.
- CaMeL, Dual-LLM, Instruction Hierarchy, adaptive IPI 논문을 related work에 추가하고 비교 표 재작성.
- PoisonedRAG 중복 bib 제거, arXiv `@article` 수정.
- kotex·한글 주석·로그 덤프 삭제.
- Vanilla utility를 별도 열로 분리해 strawman 오해를 줄임.
- 전체 HETE에서 MCR=0인 이유를 명시: 모델이 안 속은 것인지, 모델 입력이 이미 정책-렌더라 공격 문자열이 모델에 거의 안 들어갔는지. **이 구분이 논문의 정직성을 가릅니다.**

### P1 — Major revision의 핵심 (4–8주)

1. **파서/UIR 컴파일러 명세 + TCB 그림.** LLM 사용 여부를 숨기지 말 것.
2. **코드·벤치·오라클 공개** (익명 리포).
3. **모델 추가 1개** (8B급 open-weight). 기대 그림: 큰 모델에서 MCR↑, E2E 낮음 → containment 실증.
4. **공개 벤치 1개** (AgentDojo가 가장 자연스러움).
5. **인간 오라클 검증** 200건 + 일치도.
6. 베이스라인에 Spotlighting 또는 Llama Guard급 1개.

이 여섯이 없으면 “아이디어 페이퍼”로 남고, SCI 보안 저널의 empirical bar를 넘지 못합니다.

### P2 — 상위 저널용 (추가 8–12주)

- Adaptive attack: (a) 파서 모호성, (b) 방화벽이 놓치는 간접 지시, (c) 스키마를 만족하면서 정책을 우회하는 출력, (d) 신뢰 소스처럼 보이는 RAG 독.
- CaMeL 또는 Dual-LLM 재구현 비교. 공정성을 위해 동일 도구 집합.
- Benign 유틸리티를 구조화 계약과 자유 대화로 분리, 사람 평가 일부.
- 정책 DSL BNF, 정보흐름 라벨(USER/RAG/TOOL/TRUSTED)의 전파 규칙. 정리 1개라도: *untrusted sink에 권한이 흐르지 않는다*는 noninterference 스타일.
- Temperature/sampling 민감도.
- 클래스별 실패 사례 정성 분석 (지금은 HETE 실패가 0이라 분석할 실패가 없음 — 이것도 이상합니다. 강한 공격 또는 ablation 실패 케이스를 본문에 넣으십시오).

### P3 — 주장 재조정 (문장 단위)

심사자가 받아들일 주장:

> 유한한 응용 계층 위협 집합에서, typed IR과 모델 외부 결정적 게이트는 모델 타협이 곧 시스템 타협이 되지 않게 할 수 있다.

받아들이지 않을 주장:

> HETE는 attack-resilient하고, 0% ASR이며, Universal IR이고, neuro-symbolic Zero-Trust를 확립했다.

Abstract 마지막 문장은 이미 후자에서 한 발 물러나 있습니다. 제목·기여 목록·결론을 그 문장과 같은 수위로 맞추십시오.

---

## 7. 섹션별 구체 코멘트

**Abstract.** 길이가 IEEE 저널 한도를 넘을 수 있습니다 (약 250–300단어 권장). 숫자 나열을 줄이고 문제–방법–한 줄 결과–범위 제한 순으로.

**Introduction.** OWASP/NIST/MITRE 인용은 동기용으로 한 단락이면 충분합니다. 지금은 가이드라인 나열이 기여처럼 보입니다. 기여 6→3.

**Related Work.** 가장 약한 섹션. 2025–2026 capability/IFC 방어를 중심으로 재작성.

**Threat Model.** 구조는 우수. Attacker가 **컴파일러/정책을 알고 질의만 조작**하는지, **블랙박스**인지 명시. Adaptive 절의 전제가 됩니다.

**Architecture.** 그림은 좋습니다. 구현 밀도가 부족합니다. UIR JSON 예시는 남기되, 각 필드 생성 알고리즘을 본문으로.

**Security Analysis.** 클래스별 잔여 위험은 좋습니다. \(\partial C_t/\partial a=0\) 삭제. “intended acceptance rule”과 구현이 같다는 증거가 실험뿐이면, 이 섹션을 “설계 의도”로 격하하고 증명은 실험에 맡기십시오.

**Methodology.** 연구질문 7개는 많습니다. RQ1–3이 본론, RQ4–7은 보조. 오라클을 부록에 의사코드로. 공격 예시 2–3개를 본문에 (직접 주입, 간접, 도구 상승).

**Results.**  
- 클래스별 HETE 표가 전부 0%인 표는 정보량이 없습니다. 클래스별 **베이스라인 ASR**을 같은 표에.
- Latency 중앙값 0.131ms는 심사자가 즉시 오해합니다. **생성 경로 / 조기종료 경로를 분리한 표가 필수.**
- Ablation의 Provenance/Capability/OutputGuard/ResourceGuard 단일 제거 0 효과는, 벤치가 그 컨트롤을 자극하지 못한다는 뜻일 수도 있습니다. 타깃 공격을 더 넣지 않으면 “불필요한 모듈”로 읽힙니다.

**Discussion.** 반복이 심합니다. Results 수치를 다시 쓰지 말고, 일반화 조건과 실패 모드만.

**Limitations.** 잘 썼습니다. 다만 한계를 나열한 뒤 같은 문장으로 주장을 유지하면, 심사자는 “알고도 과잉 주장”으로 봅니다. 주장 범위를 limitations와 기계적으로 일치시키십시오.

---

## 8. 최종 판정

이 초안은 **아이디어 논문으로서는 상위권, 실증 보안 논문으로서는 아직 미완**입니다.  
Zero-Trust를 LLM 실행에 적용하고, 모델 타협과 시스템 타협을 분리 측정한 점은 분명한 가치입니다. 그러나 SCI 보안 저널이 2026년에 요구하는 것은

- 동시대 방어와의 **직접 비교**,
- 저자가 만들지 않은 **공격 분포**,
- 방어를 아는 **적응형 공격**,
- 재구현 가능한 **TCB**,
- 공개 **아티팩트**

입니다. 지금 0/280은 이 네 가지가 없을 때 오히려 감점 요인입니다.

**한 문장 조언:** 숫자를 더 좋게 만들 필요가 없습니다. **숫자를 믿게 만들어야** 합니다. 공개 벤치에서 10–20% E2E-ASR이 나와도, CaMeL/StruQ보다 낮고 adaptive에서도 버틴다면 지금 0%보다 합격 확률이 높습니다.
