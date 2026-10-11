# LAW-200 Development Walkthrough

## 구현 결과

독립 evaluation package를 `uir/evaluation/uir_law/law200/`에 만들었다. 기존 Phase-4E/4F 및 `_47_UIR` 결과는 수정하지 않았다. 동일 scientific contract를 LAW-KR-200과 LAW-US-200 두 법역 stratum에 적용하되 결과는 합산하지 않는다.

핵심 구현은 다음과 같다.

- `courtlistener.py`: 인증된 v4 citation lookup, 60 citations/minute throttle 대응, raw HTTP body 무수정 보존, batch/entry SHA-256 결합
- `builders/`: valid 200 record 선별, reporter-preserving hard negative 생성, mismatch pair 생성, 200/40 split freeze
- `legal_ir.py`: `U.S.` citation surface canonicalization, typed LAW/CASE/SUMMARIZE UIR, citation↔case-name binding
- `baselines/`: C0 Direct, C1 Naive RAG, C2 Existence Check, C4 Tool Agent, C5 Guardrail, C8 UIR
- `run_law200.py`: gold 파일을 읽지 않는 resumable Ollama execution과 pre-generation access log
- `scoring/`: case-level authoritative identity scoring, AULCR/FAR/coverage/FRR, Wilson 95% CI, exact McNemar, Holm correction, risk difference
- `audits/` 및 `validate_publication_results.py`: 작업지시서의 publication gate 14개 조건 검증
- `generate_report.py`: raw evidence 기반 보고서, 17개 mandatory question, KAIC update note 생성
- `update_kaic_docx.py`: validator 통과 후에만 기존 원고를 보존하고 `_LAW200.docx` 사본 생성
- `kr/`: 국가법령정보 공동활용 client, credential-redacted source freeze, Korean publication validator/report/DOCX updater

## 현재 검증

```text
Ubuntu: 26.04.1 LTS (WSL2)
Python: 3.12.13 (/mnt/d/_Work/goat_bank/.venv)
LAW-200 unit tests: 31 passed
Ollama primary: phi3.5:latest, 3.8B, Q4_0
LAW-KR-200: 200 cases × 6 pipelines = 1,200 test raw rows
Publication gate: READY_FOR_KAIC_MANUSCRIPT_KR (0 blockers)
Credential scan: 0 leaked files
```

## LAW-KR-200 관찰 결과

| Pipeline | AULCR ↓ | Invalid FAR ↓ | Verified Coverage ↑ | FRR ↓ |
|---|---:|---:|---:|---:|
| C0 Direct | 100.00% | 70.00% | 0.00% | 91.00% |
| C1 Naive RAG | 96.39% | 50.00% | 3.00% | 68.00% |
| C2 Existence Check | 69.01% | 0.00% | 33.00% | 0.00% |
| C4 Tool Agent | 0.00% | 0.00% | 0.00% | 100.00% |
| C5 Guardrail | 75.61% | 34.00% | 8.00% | 84.00% |
| C8 UIR | 0.00% | 0.00% | 100.00% | 0.00% |

C4의 낮은 AULCR은 valid 100건 전부를 거절한 결과이므로 utility preservation을 만족하지 않는다. C8은 accepted unsupported 0/100(Wilson 95% CI 0.00–3.70%), verified valid answers 100/100, false rejection 0/100으로 관찰됐다. C2 대비 accepted-unsupported case endpoint의 exact McNemar p=6.31e-30, Holm-adjusted p=1.89e-29였다. 이는 통제된 사건번호–사건명 identity evaluation의 결과이며 실체적 법률 추론이나 보편적 환각 제거를 의미하지 않는다.

한국 API의 Category C는 공식 HTTP 404가 아니다. HTTP 200 검색 응답에 exact 사건번호가 없음을 확인하고 내부 `lookup_status=404`/`NOT_FOUND_EXACT_CASE_NUMBER`로 정규화했다.

## 생성 산출물

- `evaluation/uir_law/law200/LAW200_KR_REPORT.md`
- `evaluation/uir_law/law200/LAW200_KR_AUDIT_REPORT.md`
- `evaluation/uir_law/law200/KAIC_MANUSCRIPT_UPDATE_KR.md`
- `docs/papers/_47_2_UIR_Law/2026-09-11_#0011_UIR_KAIC2026_kr_LAW200_KR.docx`

## 남은 외부 의존성

CourtListener endpoint는 2026-09-11 현재 인증 없이 HTTP 401을 반환했다. Ubuntu 환경에 `COURTLISTENER_API_TOKEN`이 설정되면 LAW-US-200 builder부터 순서대로 재개한다. 국가법령정보센터 키는 미국 CourtListener ground truth를 대신하지 않으며 두 credential은 교차 전송하지 않는다.

LAW-US-200 authoritative freeze 이전에는 미국 dataset 수, 404 ground truth, baseline 결과, statistical significance, 또는 `READY_FOR_KAIC_MANUSCRIPT`를 주장하지 않는다. 완료된 한국 결과는 반드시 `LAW-KR-200`으로 식별한다.
