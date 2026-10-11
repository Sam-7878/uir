# KAIC reviewer feedback 반영 결과

## 산출물

- 입력 원고: `../../../papers/_47_2_UIR_Law/2026-09-19_#0025_UIR_KAIC2026_kr_LAW200_updated.docx`
- 수정 원고: `../../../papers/_47_2_UIR_Law/2026-09-19_#0026_UIR_KAIC2026_kr_LAW200_REVIEWER_REVISED.docx`
- 재현 스크립트: `apply_reviewer_feedback.py`
- QA PDF: `qa/revised/2026-09-19_#0026_UIR_KAIC2026_kr_LAW200_REVIEWER_REVISED.pdf`

입력 원고와 frozen LAW-KR-200 결과는 수정하지 않았다. 새로운 실험이나 수치 재해석도 수행하지 않았다.

## 심사 의견 반영

1. McNemar 및 Holm-adjusted p-value 문장을 삭제했다.
2. 논문의 실증 중심을 `AULCR 0%` 단독 결과에서 다음 조합으로 옮겼다.
   - KO–EN canonical equivalence 100/100
   - A/B valid query의 verified routing 100/100
   - C/D invalid query의 safe outcome 100/100
   - valid-query FRR 0/100
3. NOT_FOUND/MISMATCH 경로의 모델 미호출은 설계상 구조적 특성임을 명시했다. 평가의 핵심을 자연어 질의의 올바른 UIR 상태·verification branch routing과 valid coverage 보존으로 한정했다.
4. 표 2 제목을 semantic canonicalization 및 identity binding과 직접 연결하고, Existence Check의 B 25/50 및 D 19/50을 본문에서 해석했다.
5. 결론을 “생성 차단 효과”보다 typed canonicalization, branch routing 및 coverage 보존 중심으로 수정했다.
6. Future Work에 다음을 추가했다.
   - Qwen3 등 다양한 공개 LLM에서 model independence 검증
   - UIR semantic representation과 모델 내부 표현 결합 및 sample/parameter efficiency 평가
   - 미국 판례, code generation, biomedical entity grounding 확장
   - multi-authority 및 legacy RDB 연계

## QA

- LibreOffice 렌더링: A4 2쪽
- 두 페이지 모두 시각 점검: 표·그림·참고문헌 overflow 또는 clipping 없음
- DOCX ZIP/OOXML 무결성 및 원본과 package member 구성 일치 확인
- `exact McNemar`, `Holm-adjusted`, `accepted-unsupported event` 등 삭제 대상 문구 부재 확인
- 필수 routing, B/D breakdown 및 multi-model/domain future-work 문구 존재 확인
- hidden invalid glyph(`U+FFFE`, `U+FFFD`) 부재 확인

제출 전 학회에서 사용하는 Microsoft Word 환경에서도 최종 페이지 나눔과 글꼴 대체 여부를 한 번 확인하는 것이 좋다.
