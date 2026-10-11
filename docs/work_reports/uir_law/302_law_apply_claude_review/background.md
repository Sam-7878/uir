Claude review는 전반적으로 유용하지만, **그대로 전부 반영하면 오히려 논문이 약해지는 항목도 있습니다.** 특히 2페이지 제한을 고려하면 “관련연구 독립 절”, “참고문헌 12+개”는 우선순위가 낮고, “0/100의 CI 상한 3.70%이므로 25배 이상 안전” 같은 표현은 통계적으로도 권하지 않습니다. 반면 AULCR 정의, 저자 표기 오류, category별 결과, baseline 구현 정의, 발표 슬라이드의 metric 오류는 반드시 수정하는 편이 좋습니다.

또 Claude가 놓친 더 중요한 문제도 있습니다. 현재 논문은 실제로 참고문헌 일부가 3페이지로 넘어가므로 **최종본은 다시 2페이지로 압축해야 합니다.**  그리고 슬라이드 9의 `Invalid FAR` 정의는 현재 Cat C와 D를 함께 묶고 있지만 등록 protocol에서 Invalid Citation FAR은 **Category C만** 대상으로 정의되어 있습니다.  또한 protocol상 C5는 단순 “시스템 프롬프트 guardrail”이 아니라 **naive retrieval + post-generation evidence/citation/name allow-list**입니다. 

아래 작업지시서로 진행하는 것을 권합니다.
UIR KAIC 2026 최종 수정 작업지시서
(uir/docs/work_reports/uir_law/302_law_apply_claude_review/apply_review_order.md)

이 작업에서 **가장 중요한 세 수정은** `Slide 10의 AULCR 오류`, `category별 metric을 올바르게 분리하는 것`, 그리고 `논문을 다시 2페이지로 맞추는 것`입니다. Claude review의 큰 방향은 타당하지만, 특히 category별 FRR은 그대로 받아들이기보다 위처럼 **카테고리의 expected outcome에 맞는 metric으로 재설계**하는 것이 학술적으로 더 정확합니다.
