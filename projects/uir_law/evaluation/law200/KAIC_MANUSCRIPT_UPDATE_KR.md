# KAIC Manuscript Update — LAW-KR-200

이 문서는 strict publication validator를 통과한 frozen LAW-KR-200 결과에서 자동 생성되었다. 기존 Phase-4F 및 10-case 정량 주장은 아래 결과로 교체한다.

## 평가 문단

국가법령정보 공동활용 판례 API에서 동결한 대한민국 대법원 사건번호를 이용해 LAW-KR-200(N=200; 한국어 100, 영어 100)을 구성하였다. 동일한 `phi3.5:latest`와 frozen corpus 조건에서 Naive RAG의 accepted unsupported legal claim rate는 96.39%, 단순 existence check는 69.01%, UIR은 0.00%로 관찰되었다. UIR의 valid-case verified coverage는 100.00%, FRR은 0.00%였다. C2 대비 exact McNemar p=6.311e-30, Holm-adjusted p=1.893e-29였다.

## 자동 생성 표

<!-- AUTO-GENERATED from scored raw LAW-200 records. DO NOT EDIT METRICS MANUALLY. -->
| Method | Unsupported Claims ↓ | Invalid FAR ↓ | Verified Coverage ↑ | FRR ↓ |
|---|---:|---:|---:|---:|
| C0_DIRECT | 100.00% | 70.00% | 0.00% | 91.00% |
| C1_NAIVE_RAG | 96.39% | 50.00% | 3.00% | 68.00% |
| C2_EXISTENCE_CHECK | 69.01% | 0.00% | 33.00% | 0.00% |
| C4_TOOL_AGENT | 0.00% | 0.00% | 0.00% | 100.00% |
| C5_GUARDRAIL | 75.61% | 34.00% | 8.00% | 84.00% |
| C8_UIR | 0.00% | 0.00% | 100.00% | 0.00% |

## 안전한 결론

UIR은 자연어와 권위 있는 법률 개체 사이에 강타입 의미 경계를 제공하며, 평가된 LAW-KR-200 legal-identity setting에서 생성 전 사건번호·사건명 검증을 통해 허용된 비근거 법률 주장을 줄였다.

## 필수 제한

- 결과는 대법원 identity metadata와 frozen 국가법령정보 공동활용 snapshot에 한정된다.
- normalized NOT_FOUND는 HTTP 200 검색 결과의 exact 사건번호 부재이며 공식 HTTP 404가 아니다.
- 실체적 법률 추론 또는 보편적 환각 제거를 입증하지 않는다.
- 미국 LAW-US-200 replication은 별도 CourtListener credential로 수행하며 한국 결과와 합산하지 않는다.
