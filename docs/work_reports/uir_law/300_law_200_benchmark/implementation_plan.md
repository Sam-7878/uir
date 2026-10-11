# LAW-200 Implementation Plan

작성일: 2026-09-11

## 목표

작업지시서의 독립 LAW-200 패키지를 `evaluation/uir_law/law200/`에 구현하고, LAW-KR-200(국가법령정보 공동활용)과 LAW-US-200(CourtListener)을 서로 독립된 N=200 법역 stratum으로 실행·보고한다. 한국 학회 원고에는 완료된 LAW-KR-200을 우선 반영하고, 미국 결과는 CourtListener token 확보 후 별도 replication으로 추가한다.

## 단계와 상태

1. **환경·범위 확인 — 완료**
   - Ubuntu 26.04.1 WSL2
   - 루트 `.venv` Python 3.12.13
   - Ollama `phi3.5:latest` 3.8B Q4_0 및 `qwen2.5:7b`
   - 기존 Phase-4E/4F와 `_47_UIR` evidence 미수정
2. **프로토콜·패키지 구현 — 완료**
   - CourtListener raw-response 보존 및 hash binding
   - 200 test / 40 dev freeze builder
   - runtime/gold 분리와 접근 audit
   - C0/C1/C2/C4/C5/C8 matched pipeline
   - deterministic scorer, Wilson CI, exact McNemar, Holm correction
   - strict publication validator, 보고서 및 DOCX updater
3. **개발 검증 — 완료**
   - LAW-200 단위시험 31건 통과
   - parser, cross-language equivalence, deterministic C8 output contract, credential redaction 회귀시험 포함
4. **LAW-KR-200 authoritative freeze — 완료**
   - 대법원 valid 60, exact-match NOT_FOUND mutation 30
   - test 200 / dev 40, category 및 KO/EN 균형
   - 공식 응답의 credential 제거 후 hash binding, artifact credential scan 0건
5. **LAW-KR-200 Dev-40 — 완료**
   - C0/C1/C2/C4/C5/C8 전면 실행 및 dev-only 결함 수정
6. **LAW-KR-200 Test-200 — 완료**
   - 6 pipelines × 200 = 1,200 raw rows
   - frozen test SHA-256 `e728fae81590f640e52e9174a72e238d00a550870c8cb6b0178b04e60d0efc21`
7. **통계·audit·publication validator — 완료**
   - `READY_FOR_KAIC_MANUSCRIPT_KR`, blocker 0
   - Wilson 95% CI, exact McNemar, Holm correction, risk difference 및 자동 표 재계산 통과
8. **KAIC 원고 반영 사본 — 완료**
   - 원본 보존, `_LAW200_KR.docx` 별도 생성
9. **LAW-US-200 — 외부 credential 대기**
   - CourtListener endpoint는 인증 없이는 HTTP 401
   - 미국 builder/baseline/scorer/validator는 구현됐으나 `COURTLISTENER_API_TOKEN` 없이 source freeze와 실행 불가

## 재개 조건

LAW-US-200을 재개하려면 사용자가 Ubuntu shell에 `COURTLISTENER_API_TOKEN`을 환경변수로 설정한다. 토큰 값은 채팅, 명령 출력, Git, 결과 artifact에 기록하지 않는다. 한국 stratum은 완료되어 이 조건과 독립적이다.
