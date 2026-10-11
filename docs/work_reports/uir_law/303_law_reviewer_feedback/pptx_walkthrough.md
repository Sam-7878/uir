# KAIC 2026 발표자료(PPTX) 제작 완료 보고서 및 발표 가이드

## 1. 산출물 요약

- **생성 파일**: [`uir/docs/papers/_47_2_UIR_Law/UIR_KAIC2026_Oral_Presentation.pptx`](file:///d:/_Work/goat_bank/uir/docs/papers/_47_2_UIR_Law/UIR_KAIC2026_Oral_Presentation.pptx)
- **빌드 스크립트**: [`uir/docs/papers/_47_2_UIR_Law/build_presentation.py`](file:///d:/_Work/goat_bank/uir/docs/papers/_47_2_UIR_Law/build_presentation.py)
- **고해상도 차트 이미지**:
  - [`uir/evaluation/uir_law/law200/results/figures/law200_safety_utility_tradeoff.png`](file:///d:/_Work/goat_bank/uir/evaluation/uir_law/law200/results/figures/law200_safety_utility_tradeoff.png)
  - [`uir/evaluation/uir_law/law200/results/figures/law200_pipeline_comparison_bar.png`](file:///d:/_Work/goat_bank/uir/evaluation/uir_law/law200/results/figures/law200_pipeline_comparison_bar.png)
- **전체 분량**: 총 16개 슬라이드 (16:9 Widescreen), 전 슬라이드 발표자 대본(Speaker Notes) 완비
- **권장 발표 시간**: 약 12~13분 구두 발표 + 2~3분 Q&A (총 15분 배분)

---

## 2. 슬라이드별 구성 및 시간 배분 요약

| 슬라이드 | 제목 | 주요 내용 및 시각 요소 | 배분 시간 |
|---|---|---|---|
| **01** | **표지 (Title)** | 논문 제목, 저자(박성수, 김기형 / 아주대 컴퓨터공학과), 학술대회명(KAIC 2026) | 0.5분 |
| **02** | **연구 배경: LLM 법률 검색의 결함** | Legal LLM 활용 증대 vs 법률 환각의 고위험성(변호사 징계, 사법 신뢰 훼손) | 1.0분 |
| **03** | **문제의 본질: 자연어 프롬프트 한계** | 자연어 프롬프트의 이중 구조(요청 의도 vs 주장된 사실 미분리)와 토큰 전제 결함 | 1.0분 |
| **04** | **기존 접근법의 딜레마** | Naive RAG(96% 비근거 수용) vs Existence Check(불일치 취약) vs Agent(과도 거절 100%) | 1.0분 |
| **05** | **핵심 철학: Prompt ≠ Authority** | 프롬프트의 의도와 공식 정보원의 사실적 권위 분리, 컴파일러 IR 패러다임 전환 | 1.0분 |
| **06** | **UIR 시스템 아키텍처** | 전체 파이프라인 흐름도 (Language Frontend → Typed UIR → Binding → Branch) | 1.5분 |
| **07** | **UIR의 4대 핵심 메커니즘** | 의미 정규화, 생성 전 권위 검증, 런타임 경계/안전한 기권, 엄격한 출력 계약 | 1.0분 |
| **08** | **독립 벤치마크: LAW-KR-200** | N=200(한/영 각 100), 4대 균등 범주(Valid, Variation, Hard Neg, Mismatch), 통제 프로토콜 | 1.5분 |
| **09** | **4대 평가 지표 및 6개 비교군** | AULCR(주지표), Invalid FAR, Coverage, FRR 정의 및 C0, C1, C2, C4, C5, C8 구성 | 1.0분 |
| **10** | **정량적 평가 결과 (표 1)** | 표 1 렌더링 및 C8 UIR 압도적 성과(AULCR 0.00%, Coverage 100.00%, FRR 0.00%) | 1.5분 |
| **11** | **핵심 성능 시각화 차트** | 안전성 vs 유용성 트레이드오프 산점도(Ideal Zone 안착) 및 파이프라인 막대 차트 | 1.0분 |
| **12** | **통계적 검증 및 C2 우위 분석** | exact McNemar (p < 10⁻²⁴), Category D Mismatch에서 C2(38%) vs UIR(100%) 원인 규명 | 1.0분 |
| **13** | **정성적 사례 분석** | Hard Negative(2026두30951) 및 Mismatch 질의의 실제 모델 Raw Output 비교 | 1.0분 |
| **14** | **다국어 정규화 검증** | 100개 KO-EN 질의쌍 100% 동일 UIR 사상, 언어 간 성능 편차 제로(Zero-Gap) | 0.5분 |
| **15** | **연구의 한계 및 향후 과제** | 식별자 바인딩 한정(실체적 법리 X), Wilson CI 상한(3.70%), CourtListener/RDB 연계 | 1.0분 |
| **16** | **결론 및 질의응답 (Q&A)** | 핵심 요약(Takeaway 3가지), 과기정통부/IITP 사의 표기, 질의응답 안내 | 0.5분 |

---

## 3. 디자인 및 스타일 특징

1. **학술 발표 전용 컬러 시스템**:
   - Primary: Deep Midnight Navy (`#0F1E36`, 안정감과 신뢰도)
   - Secondary / Containers: Clean White Card & Light Slate (`#F8FAFC`, 시각적 피로도 최소화)
   - Accent: High-Contrast Electric Cyan/Teal (`#0284C7`, 핵심 키워드 강조)
   - Status: Success Green (`#16A34A`), Danger Red (`#DC2626`), Warning Amber (`#D97706`)
2. **반응형 컨테이너 레이아웃**: 단순 텍스트 나열을 피하고, 2열/3열 카드 UI와 배지(Badge), 플로우 박스로 계층화
3. **완전한 발표 대본 수록**:
   - 슬라이드 쇼의 **발표자 보기(Presenter View)**에서 별도의 대본 출력 없이 자연스럽게 읽으며 시간을 조절할 수 있도록 구어체 발표 스크립트를 전 슬라이드 하단 노트에 삽입

---

## 4. 발표 팁 및 예상 질문 대비 (Q&A Guide)

- **Q1. 데이터베이스에서 사건번호가 있는지만 SQL(`SELECT EXISTS`)로 확인하면 되는 것 아닌가? (슬라이드 12 참조)**
  - **답변 요령**: "아주 중요한 지적입니다. 그러나 사건번호만 확인하는 방식(C2)은 실존 사건번호 뒤에 가짜 사건명이 붙은 'Category D Mismatch' 질의를 전혀 잡아내지 못해 개체 바인딩 정확도가 38%로 추락했습니다. UIR은 강타입 스키마를 통해 사건번호와 사건명의 identity 결합 무결성을 검증하기 때문에 100% 정확하게 불일치를 탐지해 낼 수 있었습니다."
- **Q2. AULCR 0%는 모델이 모든 질의를 거절(Reject)해서 나온 꼼수 아닌가? (슬라이드 10, 11 참조)**
  - **답변 요령**: "그렇지 않습니다. C4 Tool Agent의 경우 정상 질의를 100% 거절(FRR 100%)하여 실용 가치가 없었지만, C8 UIR은 정상 질의 100건에 대해 정답 커버리지(Verified Coverage) 100.00%를 유지하면서 비존재/불일치 질의만을 정밀하게 사전에 걸러냈습니다."
- **Q3. 이 결과가 모든 법률 환각의 종식을 뜻하는가? (슬라이드 15 참조)**
  - **답변 요령**: "솔직하게 말씀드리면 그렇지 않습니다. 본 연구는 사건번호와 사건명이라는 '법률 식별자 결합'의 무결성에 집중한 것이며, 복잡한 실체적 법리 해석이나 판결 요지 추론의 절대적 정확성을 보증하는 것은 아닙니다. 또한 통계적으로 Wilson 95% 신뢰구간 상한인 3.70%의 잠재 위험을 함께 고려해야 합니다."

---

## 5. 수정 이력 (2026-09-21)

- **대상 파일**: [`uir/docs/papers/_47_2_UIR_Law/2026-09-19_#0024_UIR_KAIC2026_Oral_Presentation_updated.pptx`](file:///d:/_Work/goat_bank/uir/docs/papers/_47_2_UIR_Law/2026-09-19_#0024_UIR_KAIC2026_Oral_Presentation_updated.pptx)
- **수정 사항**:
  - 11페이지 좌측 산점도 차트([`law200_safety_utility_tradeoff.png`](file:///d:/_Work/goat_bank/uir/evaluation/uir_law/law200/results/figures/law200_safety_utility_tradeoff.png))에서 `(Zero Unsupported, Max Coverage)` 텍스트가 `C8 UIR (Ours)` 및 마커와 겹치던 문제를 해결.
  - `C8 UIR (Ours)` 라벨을 상단 우측(`xytext=(8, 4)`)으로 분리 배치.
  - `IDEAL ZONE\n(Zero Unsupported,\nMax Coverage)` 텍스트를 이상적 영역의 하단 중앙(`X=9.5, Y=83`)으로 이동하고, 고대비 소프트 그린 배지 박스(`facecolor='#EAFAF1', edgecolor='#27AE60'`)를 적용하여 시인성과 가독성을 대폭 개선(수직 간격 140px 이상 확보 및 전 라벨 무충돌 검증 완료).
  - 프레젠테이션 내 다른 슬라이드, 서식, 발표자 대본의 변경 없이 해당 차트 이미지만 안전하게 업데이트 완료.

