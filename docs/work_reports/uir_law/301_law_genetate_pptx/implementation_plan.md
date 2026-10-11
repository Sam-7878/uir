# KAIC 2026 발표자료(PPTX) 작성 계획: "UIR: 환각 저항형 법률 검색을 위한 범용 중간 표현"

## 1. 개요 및 배경

본 계획은 KAIC 2026(한국인공지능학회) 발표용 논문 초안(`2026-09-11_#0013_UIR_KAIC2026_kr_LAW200_KR_FINAL.docx`)과 관련 개발/검증 문서(`300_law_200_benchmark/`), 그리고 동결된 벤치마크 결과(`law200/results/kr/`)를 바탕으로 **약 15분 분량(16장 슬라이드)**의 학술대회 발표 슬라이드를 완성도 높은 `.pptx` 파일로 제작하기 위한 계획입니다.

---

## 2. 슬라이드 구성안 (총 16 슬라이드, 약 15분 발표)

| 번호 | 슬라이드 제목 | 핵심 내용 | 발표 예상 시간 |
|---|---|---|---|
| **01** | **표지 (Title)** | 논문 제목, 저자(박성수, 김기형 / 아주대 컴퓨터공학과), KAIC 2026 | 0.5분 |
| **02** | **연구 배경: LLM 법률 검색의 치명적 결함** | Legal LLM 활용 증대 vs 비존재 판례/허위 주장 생성(고위험) | 1.0분 |
| **03** | **문제의 본질: Prompt Context의 한계** | 자연어 프롬프트는 의도(Intent)와 사실 주장(Claimed Fact)을 미분리 | 1.0분 |
| **04** | **기존 접근법의 딜레마** | Naive RAG(환각 전파) vs Existence Check(불일치 취약) vs Agent(과도 거절) | 1.0분 |
| **05** | **핵심 철학: Prompt ≠ Authority** | 프롬프트는 맥락일 뿐 권위가 아님. 컴파일러 IR 기반 패러다임 전환 | 1.0분 |
| **06** | **UIR 시스템 아키텍처** | Semantic Canonicalization → Typed UIR → Authoritative Binding 파이프라인 | 1.5분 |
| **07** | **핵심 메커니즘 4단계** | 정규화, 생성 전 검증(Pre-generation), 안전한 기권(Abstention), 출력 계약 | 1.0분 |
| **08** | **LAW-KR-200 벤치마크 설계** | N=200(한/영 각 100), 4대 통제 범주(Valid, Variation, Hard Neg, Mismatch) | 1.5분 |
| **09** | **실험 환경 및 6대 비교 파이프라인** | C0 Direct, C1 Naive RAG, C2 Existence, C4 Agent, C5 Guardrail, C8 UIR | 1.0분 |
| **10** | **정량 평가 결과 (Main Results)** | 표 1 분석: AULCR 0.00%, Coverage 100.00%, FRR 0.00%의 압도적 성과 | 1.5분 |
| **11** | **핵심 성능 비교 시각화 (Charts)** | 안전성(AULCR ↓) vs 유용성(Coverage ↑) 2D 비교 및 파이프라인별 비교 | 1.0분 |
| **12** | **통계적 검증 및 심층 분석** | McNemar p=6.31e-30, Mismatch 탐지에서 C2(38%) vs UIR(100%) 차이 원인 | 1.0분 |
| **13** | **정성적 사례 분석 (Case Studies)** | Hard Negative(2026두30951) 및 Mismatch 사례의 Naive RAG vs UIR 비교 | 1.0분 |
| **14** | **다국어 정규화 및 언어 독립성** | 100개 KO-EN 질의쌍 100% 동일 UIR 사상, 언어 간 성능 편차 제로 | 0.5분 |
| **15** | **연구의 한계 및 향후 과제** | 식별자 바인딩 한정(실체적 추론 X), Wilson CI, CourtListener/RDB 연계 확장 | 1.0분 |
| **16** | **결론 및 Q&A** | 핵심 요약(Takeaway 3가지) 및 발표 마무리 질의응답 | 0.5분 |

---

## 3. 디자인 및 기술적 구현 방안

1. **와이드스크린 16:9 비율 (13.333" x 7.5")**: 최신 프로젝터 및 디스플레이에 최적화
2. **학술 발표 전용 컬러 시스템**:
   - Primary: Deep Navy (`#0F1E36`) - 안정감과 신뢰도
   - Secondary / Header: Midnight Slate (`#1E293B`)
   - Accent: High-contrast Electric Teal (`#008080` / `#0284C7`)
   - Alert / Status: Success Green (`#16A34A`), Danger Red (`#DC2626`), Warning Amber (`#D97706`)
   - Backgrounds: Clean White (`#FFFFFF`) 및 Soft Slate (`#F8FAFC`) 카드 레이아웃
3. **가독성 높은 타이포그래피 및 카드 레이아웃**:
   - Malgun Gothic / Arial 기반으로 계층화된 폰트 크기 및 굵기 적용
   - 텍스트 나열을 지양하고 **구조화된 카드(Container)**, **비교 테이블**, **지표 하이라이트 박스** 활용
4. **시각 차트 이미지 생성 및 삽입**:
   - `matplotlib`을 이용해 논문의 표 1을 직관적으로 보여주는 **고해상도 비교 차트(안전성 vs 유용성 비교, 파이프라인별 AULCR/Coverage)**를 생성하여 슬라이드에 직접 삽입
5. **완벽한 발표자 대본 (Speaker Notes)**:
   - 모든 슬라이드 하단 노트 영역에 15분 발표 호흡에 맞춘 **자연스러운 구어체 발표 대본**을 수록하여 슬라이드 쇼 발표자 보기(Presenter View)에서 바로 활용할 수 있도록 제작

---

## 4. 실행 단계

1. **차트 및 시각 자료 스크립트 작성**:
   - 표 1 데이터(`AULCR`, `Invalid FAR`, `Verified Coverage`, `FRR`) 및 비교 분석 차트 생성 (`.png`)
2. **PPTX 생성 자동화 스크립트(`build_presentation.py`) 작성**:
   - `python-pptx`를 활용하여 16개 슬라이드 템플릿, 박스, 표, 다이어그램, 텍스트, 차트 이미지, 슬라이드 노트 완벽 배치
3. **검증 및 산출물 생성**:
   - PPTX 파일 빌드 실행 및 레이아웃, 인코딩, 슬라이드 노트 검증
   - 생성 위치: `uir/docs/papers/_47_2_UIR_Law/UIR_KAIC2026_Oral_Presentation.pptx`

---

## 5. 사용자 피드백 요청

- 전체 16개 슬라이드 구성 및 15분 발표 배분에 대해 추가하거나 조정하고 싶은 강조 포인트가 있으신지 확인 부탁드립니다.
- 승인해 주시면 즉시 차트 생성 및 PPTX 빌드를 진행하겠습니다.
