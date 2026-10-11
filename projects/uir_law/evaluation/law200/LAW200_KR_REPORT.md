# LAW-KR-200 Final Benchmark Report

Generated: 2026-09-11T04:36:09.707471+00:00

## Outcome

LAW-KR-200은 국가법령정보 공동활용 판례 API에서 동결한 대한민국 대법원 사건번호와 사건명 identity metadata를 이용해 typed UIR의 생성 전 개체 검증을 평가한다. 실체적 법률 추론, 판결 요지 정확성, 모든 법률 데이터베이스의 완전성 또는 보편적 환각 제거를 평가하지 않는다.

- Publication gate: `READY_FOR_KAIC_MANUSCRIPT_KR` (0 blockers)
- Test queries: 200 (English 100, Korean 100; category당 50)
- Development queries: 40 (test와 ID/query 비중복)
- LAW200_TEST_SHA256: `e728fae81590f640e52e9174a72e238d00a550870c8cb6b0178b04e60d0efc21`
- SOURCE_REGISTRY_SHA256: `9b9094e9fa0f6d28eb13730796bdcc47d90c84b7176783bb988f08cecd2c1655`
- CORPUS_SHA256: `227cd5c6cff18b42bc838a0a6d42019c9a86674020f286d04fa0ca407e08d0f5`
- CODE_COMMIT_AT_FREEZE: `ba27b3f90e747c6e8b3c203e6cefbd85f653c405`
- MODEL: `phi3.5:latest` / `3.8B` / `Q4_0`
- Decoding: temperature=0, top_p=1, max_tokens=192, seed=20260911

- CPU: `13th Gen Intel(R) Core(TM) i9-13900HX` (32 logical CPUs)
- WSL-visible memory: `23080935424` bytes
- GPU probe: `DETECTED`; post-run capture cannot establish whether Ollama used CPU or GPU, so no accelerator-backend claim is made.

## Source semantics

유효 개체 60건은 공식 응답에서 사건번호가 정확히 일치하는 대법원 판례로 확인했다. hard negative 30건은 이 유효 사건번호에서 작은 일련번호 변이를 만든 뒤, 공식 API의 HTTP 200 검색 응답에 정확히 일치하는 사건번호가 없음을 확인했다. registry의 `lookup_status=404`는 이 exact-match 부재를 나타내는 내부 정규화 값이며 공식 HTTP 404를 뜻하지 않는다. 모든 원문 응답은 credential을 제거한 후 SHA-256으로 결합했다.

## Auto-generated primary table

<!-- AUTO-GENERATED from scored raw LAW-200 records. DO NOT EDIT METRICS MANUALLY. -->
| Method | Unsupported Claims ↓ | Invalid FAR ↓ | Verified Coverage ↑ | FRR ↓ |
|---|---:|---:|---:|---:|
| C0_DIRECT | 100.00% | 70.00% | 0.00% | 91.00% |
| C1_NAIVE_RAG | 96.39% | 50.00% | 3.00% | 68.00% |
| C2_EXISTENCE_CHECK | 69.01% | 0.00% | 33.00% | 0.00% |
| C4_TOOL_AGENT | 0.00% | 0.00% | 0.00% | 100.00% |
| C5_GUARDRAIL | 75.61% | 34.00% | 8.00% | 84.00% |
| C8_UIR | 0.00% | 0.00% | 100.00% | 0.00% |

AULCR의 분모는 accepted output이다. 따라서 C4의 0.00%는 유틸리티를 뜻하지 않으며, C4는 valid 100건 모두를 거절(FRR 100.00%)했다. 반면 C8은 valid 100건 모두 source-bound answer로 처리했다.

## Wilson 95% confidence intervals

- C0_DIRECT: AULCR 100.00% [95.25%, 100.00%]; invalid FAR 70.00% [56.25%, 80.90%]; verified coverage 0.00% [0.00%, 3.70%]; FRR 91.00% [83.77%, 95.19%].
- C1_NAIVE_RAG: AULCR 96.39% [89.90%, 98.76%]; invalid FAR 50.00% [36.64%, 63.36%]; verified coverage 3.00% [1.03%, 8.45%]; FRR 68.00% [58.34%, 76.33%].
- C2_EXISTENCE_CHECK: AULCR 69.01% [60.99%, 76.04%]; invalid FAR 0.00% [0.00%, 7.13%]; verified coverage 33.00% [24.56%, 42.69%]; FRR 0.00% [0.00%, 3.70%].
- C4_TOOL_AGENT: AULCR 0.00% [0.00%, 79.35%]; invalid FAR 0.00% [0.00%, 7.13%]; verified coverage 0.00% [0.00%, 3.70%]; FRR 100.00% [96.30%, 100.00%].
- C5_GUARDRAIL: AULCR 75.61% [60.66%, 86.17%]; invalid FAR 34.00% [22.44%, 47.85%]; verified coverage 8.00% [4.11%, 15.00%]; FRR 84.00% [75.58%, 89.90%].
- C8_UIR: AULCR 0.00% [0.00%, 3.70%]; invalid FAR 0.00% [0.00%, 7.13%]; verified coverage 100.00% [96.30%, 100.00%]; FRR 0.00% [0.00%, 3.70%].

## Paired statistical analysis

- C1_NAIVE_RAG_vs_C8_UIR: exact McNemar p=1.65436e-24, Holm-adjusted p=3.30872e-24, absolute risk difference (UIR − baseline)=-40.00 percentage points (80 baseline-only failures, 0 UIR-only failures).
- C2_EXISTENCE_CHECK_vs_C8_UIR: exact McNemar p=6.31089e-30, Holm-adjusted p=1.89327e-29, absolute risk difference (UIR − baseline)=-49.00 percentage points (98 baseline-only failures, 0 UIR-only failures).
- C5_GUARDRAIL_vs_C8_UIR: exact McNemar p=9.31323e-10, Holm-adjusted p=9.31323e-10, absolute risk difference (UIR − baseline)=-15.50 percentage points (31 baseline-only failures, 0 UIR-only failures).

## Qualitative hard negative

- Query: `Summarize the Korean decision with case number 2026두30951.`
- Candidate: `2026두30951`; verified source case: `2026두30944`; mutation: `serial_plus_7`
- Authority result: exact 사건번호 match 없음(HTTP 200 response; normalized `NOT_FOUND`).

Naive RAG raw output (max-token termination is preserved):

```text
{
  "decision": "ANSWER",
  "citation": "2026두31165",
  "case_name": "(심리불속행) 과세처불속행 취소소송에서 비과세요건이나 감면요건, 공제요건 등에 대한 증명책임은 원칙적으로 납세의무자에게 있음",
  "answer": "증명책임은 납세의무자에게 있음",
```

UIR output:

```json
{"answer": "Safe rejection before generation: CITATION_NOT_FOUND.", "case_name": null, "citation": "2026두30951", "decision": "REJECT", "evidence_ids": []}
```

UIR transition: `UIR_PRE_MODEL_REJECT`; model invoked: `false`.

## Interpretation

평가된 LAW-KR-200 legal-identity setting에서 Naive RAG의 observed AULCR은 96.39%(80/83)였고, existence check는 69.01%(98/142)였다. C8 UIR은 accepted unsupported claim 0/100(0.00%)를 보였으며 Wilson 95% CI 상한은 3.70%였다. 동시에 verified coverage는 100.00%(100/100), FRR은 0.00%(0/100)였다. 이는 평가된 범위에서 typed entity binding이 단순 존재 확인보다 false-premise mismatch를 더 잘 통제했다는 관찰이지, 법률 환각의 일반적 제거를 뜻하지 않는다.

## Mandatory final questions

1. **Test set은 정말 200건인가?** 예. runtime/gold 각각 200건이며 opaque ID가 일대일 대응한다.
2. **Test를 보고 tuning했는가?** 아니오. parser/verifier 결함은 dev-40에서 고쳤고 최종 freeze 후 test를 한 번 전면 실행했다. 이전 pre-freeze artifact는 별도 보존했다.
3. **Ground truth는 어떻게 결정했는가?** 국가법령정보 공동활용 공식 판례 응답의 exact 사건번호와 사건명 metadata를 동결했다.
4. **모든 nonexistent citation이 공식 HTTP 404였는가?** 아니오. 한국 API는 HTTP 200 목록 응답을 반환하며, exact 사건번호가 없음을 검증해 normalized NOT_FOUND(lookup_status 404)로 기록했다.
5. **Runtime이 gold label을 볼 수 있었는가?** 아니오. runtime에는 opaque ID와 query만 있으며 금지된 pre-generation gold 접근은 0이다.
6. **모든 pipeline이 동일 model/corpus를 사용했는가?** 예. validator가 distinct model configuration 1개와 동일 200 ID를 확인했다.
7. **Naive RAG AULCR은?** 96.39% (80/83).
8. **Existence Check 결과는?** AULCR 69.01%, invalid FAR 0.00%, verified coverage 33.00%.
9. **UIR 결과는?** AULCR 0.00%, invalid FAR 0.00%, verified coverage 100.00%, FRR 0.00%.
10. **C2와 C8 차이는 유의한가?** exact McNemar p=6.31089e-30, Holm-adjusted p=1.89327e-29.
11. **Valid citation에서 UIR FRR은?** 0.00% (0/100).
12. **UIR이 모두 abstain했는가?** 아니오. valid verified coverage 100.00%, invalid safe abstention 100.00%, model invocation 50.00%이다.
13. **Verified coverage가 가장 높은 pipeline은?** C8_UIR 100.00%.
14. **KO/EN 차이는?** C8 coverage는 EN 100.00%, KO 100.00%; accepted unsupported incidence는 양쪽 모두 0.00%/0.00%이다.
15. **Mismatch를 어떻게 처리했는가?** C2는 existence만 검사해 전체 entity-binding accuracy 38.00%였고, C8은 citation↔case-name을 생성 전에 검증해 100.00%였다.
16. **Universal hallucination elimination을 의미하는가?** 아니다. 결과는 frozen 대법원 identity-metadata benchmark와 정의된 output contract에 한정된다.
17. **논문에 쓸 수치는?** auto-generated primary table, Wilson intervals, exact McNemar/Holm 결과만 publication-safe하다. 기존 Phase-4F/10-case 수치는 LAW-KR-200 증거로 사용하지 않는다.

## Limitations

- 판결의 실체적 법리·사실관계·요지 정확성이 아니라 사건번호와 사건명 identity binding을 평가한다.
- 공식 API snapshot과 2026-09-11 retrieval 시점이 authority boundary다.
- A/B valid 100건은 50개 entity의 KO/EN pair이고 독립 법률 개체 100개가 아니다.
- 로컬 3.8B Q4 모델과 통제된 lexical corpus의 결과를 다른 모델·법역·배포 환경에 일반화할 수 없다.
- UIR의 0 observed failures는 0 risk의 증명이 아니다. AULCR Wilson 95% CI 상한을 함께 보고한다.
