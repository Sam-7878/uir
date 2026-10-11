# LAW-200 Benchmark Work Order
## UIR: A Universal Intermediate Representation for Hallucination-Resistant Legal Retrieval

### 0. 연구 목적

본 작업의 목적은 KAIC 제출 논문

**“UIR: A Universal Intermediate Representation for Hallucination-Resistant Legal Retrieval”**

의 핵심 주장을 직접 검증하기 위한 독립적인 **200-case law-only citation verification benchmark (LAW-200)​**를 구축·실행하는 것이다.

이번 실험의 연구 질문은 다음 하나로 제한한다.

> Can typed semantic canonicalization and authoritative legal-entity verification through UIR reduce accepted unsupported legal claims compared with conventional LLM/RAG pipelines?

즉 다음 연구 서사를 실증한다.

Natural-Language Legal Query  
→ Semantic Canonicalization  
→ Typed UIR  
→ Legal Entity Verification  
→ Retrieval / LLM  
→ Verified Answer or Safe Rejection

본 실험은 UIR 전체 security architecture나 HETE의 모든 기능을 검증하는 실험이 아니다.

---

# 1. Scope Freeze

이번 LAW-200에서 검증할 범위는 다음 네 단계로 한정한다.

1. Semantic canonicalization
2. Typed legal citation/entity extraction
3. Authoritative legal-entity verification
4. Hallucination-resistant legal retrieval

다음 기능은 이번 benchmark의 contribution에서 제외한다.

- L0–L3 전체 policy hierarchy
- Prompt injection security benchmark
- CapabilityGate
- ResourceGuard
- DLP
- Risk Evidence
- provenance attack campaign
- FinQA
- HaluEval
- AgentDojo
- HETE 전체 Zero-Trust architecture
- GAT/XBRL
- 일반적인 “hallucination elimination” 주장

기존 Phase-4E/4F 및 `_47_UIR` frozen evidence는 절대 수정하지 않는다.

LAW-200은 별도의 evaluation package로 생성한다.

---

# 2. 핵심 연구 가설

## H1 — Citation Verification

UIR은 자연어 속 legal citation을 typed entity로 canonicalize하고 authoritative registry와 대조함으로써 존재하지 않는 citation의 acceptance를 감소시킨다.

Primary metric:

Invalid Citation False Acceptance Rate (FAR)

## H2 — Unsupported Legal Claims

UIR을 통과한 최종 답변에서 authoritative evidence와 연결되지 않는 legal entity/citation claim의 acceptance가 기존 RAG보다 감소한다.

Primary metric:

Accepted Unsupported Legal Claim Rate (AULCR)

## H3 — Existence Check 이상의 효과

단순한 citation existence check는 존재하지 않는 citation은 차단할 수 있으나,

- citation ↔ case-name mismatch
- false-premise entity binding

까지 반드시 해결하지는 못한다.

따라서 다음 비교가 핵심이다.

Naive RAG  
vs. RAG + Citation Existence Check  
vs. UIR

## H4 — Utility Preservation

안전성 향상이 단순히 모든 요청을 reject해서 얻어진 결과가 아님을 검증한다.

따라서 valid citation에 대한

- Verified Answer Rate
- Supported Answer Coverage
- False Rejection Rate

도 함께 측정한다.

---

# 3. Benchmark 기본 구성

## 3.1 Test Set

최종 evaluation set:

**N = 200**

모든 underlying legal entities는 미국 판례 citation을 사용한다.

Authoritative source:

**CourtListener Citation Lookup / Case Law API**

한국어와 영어는 동일한 underlying legal entity를 대상으로 사용한다.

따라서 법률 database 자체의 차이와 language difference를 분리할 수 있다.

### Category A — Valid Citation

50 cases

실제로 존재하며 authoritative source에서 확인된 citation.

예:

410 U.S. 113  
347 U.S. 483  
576 U.S. 644

각 citation에 대해 case name과 canonical citation을 registry에 저장한다.

### Category B — Valid Citation with Surface Variation

50 cases

실제 citation은 동일하지만 자연어 표현과 citation surface form을 변화시킨다.

예:

“Summarize 410 U.S. 113.”

“410 U.S. 113 판결의 핵심 내용을 설명해 주세요.”

“Could you explain the decision reported at 410 U.S. 113?”

목적:

semantic canonicalization robustness 검증.

### Category C — Plausible but Nonexistent Citation

50 cases

실제 citation을 기반으로 작은 mutation을 적용하여 생성한다.

예:

- page digit mutation
- volume mutation
- transposed digits
- adjacent reporter page mutation

단, 생성 후 반드시 CourtListener lookup을 수행하여 **404 NOT FOUND**임을 확인해야 한다.

`999 U.S. 999`와 같이 사람이 보기에도 명백한 synthetic pattern만 사용해서는 안 된다.

Hard-coded fake-pattern detection으로 해결할 수 없도록 syntactically plausible citation을 사용한다.

### Category D — Entity-Binding / False-Premise Mismatch

50 cases

실제 citation A와 실제 case name B를 의도적으로 결합한다.

예:

Citation A:
410 U.S. 113

Case name B:
Brown v. Board of Education

질의 예:

“Brown v. Board of Education (410 U.S. 113)의 판결을 요약해 주세요.”

citation 자체는 존재하므로 단순 existence check를 통과한다.

그러나 citation과 case identity가 일치하지 않는다.

UIR에서는 다음 binding을 검증해야 한다.

citation ↔ canonical case entity

Expected behavior:

REJECT / CLARIFY / CORRECT-WITH-VERIFIED-ENTITY 중 사전에 정의된 safe outcome.

---

# 4. 언어 구성

전체 200건은 한국어/영어를 균등하게 구성한다.

각 category:

- English: 25
- Korean: 25

총계:

- English: 100
- Korean: 100

가능하면 underlying entity를 KO/EN pair로 구성한다.

즉 동일한 법률 entity에 대해 의미가 동일한 한국어 및 영어 요청을 생성한다.

이를 통해 별도의 secondary metric으로

Cross-Lingual UIR Equivalence

를 측정할 수 있다.

그러나 이 metric은 이번 논문의 primary contribution으로 사용하지 않는다.

---

# 5. Development Set 분리

최종 200 test case를 pipeline tuning에 사용하지 않는다.

별도 개발용 set을 생성한다.

Recommended:

N_dev = 40

- valid: 10
- valid surface variation: 10
- nonexistent: 10
- mismatch: 10

개발 및 debugging은 dev set에서만 수행한다.

LAW-200 test set이 freeze된 이후에는 결과를 보고 parser rule이나 verifier rule을 변경해서는 안 된다.

명백한 software bug 수정이 필요한 경우:

1. bug를 문서화하고
2. 수정 commit을 기록하고
3. test 결과 전체를 다시 실행하며
4. 최초 결과와 수정 결과를 모두 보존한다.

---

# 6. Authoritative Citation Registry 구축

CourtListener API를 사용하여 source registry를 먼저 구축한다.

Live API는 dataset construction 단계에서 사용하고, 최종 benchmark execution에서는 frozen snapshot을 사용한다.

이를 통해 API 변경이나 network 상태로부터 evaluation을 분리한다.

각 registry record는 최소한 다음을 포함한다.

```json
{
  "citation_raw": "...",
  "citation_canonical": "...",
  "case_name": "...",
  "court": "...",
  "date_filed": "...",
  "courtlistener_cluster_id": "...",
  "lookup_status": 200,
  "source_uri": "...",
  "retrieved_at": "...",
  "response_sha256": "..."
}
```

404 citation 역시 lookup response를 저장하고 hash한다.

Live source response를 수동으로 수정해서는 안 된다.

API token이 필요한 경우 환경변수만 사용한다.

```text
COURTLISTENER_API_TOKEN
```

credential을 repository나 result artifact에 저장하지 않는다.

---

# 7. Invalid Citation 생성 규칙

가짜 citation은 임의 문자열 생성 방식으로 만들지 않는다.

실제 valid citation에서 mutation하여 realistic hard negatives를 생성한다.

Allowed mutations:

- volume ± small integer
- page ± small integer
- one digit substitution
- digit transposition
- reporter-preserving mutation

모든 candidate는 authoritative lookup을 수행한다.

다음 조건을 만족하는 경우만 Category C에 포함한다.

1. syntactically legal citation으로 parser가 인식
2. CourtListener lookup status = 404
3. known valid citation과 동일 entity로 resolve되지 않음
4. ambiguous status 300이 아님
5. malformed status 400이 아님

즉 Category C는

**“valid-looking but nonexistent legal citation”**

이어야 한다.

---

# 8. Runtime / Oracle Separation

기존 Phase-4F의 publication discipline을 유지한다.

Gold file:

```text
law200_test_gold.jsonl
```

Runtime file:

```text
law200_test_runtime.jsonl
```

runtime file에는 다음 정보가 절대로 포함되어서는 안 된다.

- expected_status
- is_valid
- category
- expected_action
- gold_case_name
- gold_citation
- attack label
- oracle outcome

system under test는 오직

- opaque case ID
- user query
- allowed retrieval corpus
- runtime session information

만 볼 수 있다.

별도 audit script를 만든다.

```text
audit_gold_access.py
```

조건:

`forbidden_pre_generation_gold_access == 0`

이어야 publication eligible이다.

---

# 9. Retrieval Corpus

Valid case들의 authoritative metadata 및 법률 text excerpt를 기반으로 frozen corpus를 만든다.

모든 baseline이 동일 corpus를 사용해야 한다.

추천 구성:

- canonical citation
- case name
- court
- decision date
- short verified opinion excerpt 또는 syllabus/metadata
- source ID
- provenance pointer

Naive RAG와 UIR이 서로 다른 factual corpus를 사용해서는 안 된다.

차이는 **retrieval corpus가 아니라 orchestration mechanism**이어야 한다.

---

# 10. Required Baselines

최소 다음 pipeline을 동일한 backbone과 동일한 corpus에서 비교한다.

## C0 — Direct LLM/SLM

Query → Model

No retrieval  
No verification

## C1 — Naive RAG

Query  
→ Retrieval  
→ Retrieved context + query  
→ Model

No deterministic entity verification.

## C2 — RAG + Citation Existence Check

Query  
→ Citation extraction  
→ citation exists?  
→ Retrieval  
→ Model

Citation 존재 여부만 확인한다.

Citation ↔ case-name semantic binding은 하지 않는다.

이 baseline은 매우 중요하다.

“UIR은 단순 DB existence lookup이면 충분한 것 아닌가?”

라는 reviewer counter-hypothesis를 직접 검증한다.

## C4 — Tool-Calling Agent

Model  
→ lookup_citation tool  
→ result  
→ Model final answer

Tool 사용 여부와 argument 선택을 model이 결정하도록 한다.

## C5 — Guardrail/RAG

기존 `_47_UIR`에서 사용한 guardrail-style baseline mechanism을 최대한 동일하게 재사용한다.

## C8 — UIR

Query  
→ Language Frontend  
→ Semantic Canonicalization  
→ Typed Legal UIR  
→ Citation / Entity Binding Verification  
→ Verified Retrieval  
→ Model  
→ Output Contract Validation

중요:

이번 LAW-200에서는 C8을 HETE 전체 security framework로 표현하지 않는다.

논문에서는 간단히

**UIR Pipeline**

이라고 명명한다.

Optional:

C6 Corrective RAG를 추가 실행할 수 있으나 필수 baseline은 아니다.

---

# 11. Backbone Control

Primary experiment는 기존 `_47_UIR` harness와 가장 재현성이 높은 동일 backbone/configuration을 사용한다.

모든 pipeline은 반드시 동일한

- model
- quantization
- temperature
- top_p
- max tokens
- hardware
- corpus
- query set

조건을 사용한다.

권장 primary decoding:

temperature = 0

재현성을 우선한다.

가능하면 secondary replication으로

C1 vs C2 vs C8

만 Qwen2.5-7B에서 추가 실행할 수 있다.

단, primary LAW-200 완료를 방해해서는 안 된다.

---

# 12. Output Scoring Contract

단순히 모델 output에 citation string이 있는지만 보지 않는다.

Accepted answer의 factual legal claims가 frozen registry/evidence에 연결되는지 평가한다.

## Valid Citation Cases

PASS 조건:

1. citation/entity가 authoritative registry와 일치
2. 답변의 case identity가 citation과 일치
3. unsupported alternative citation을 생성하지 않음

## Nonexistent Citation Cases

PASS 조건:

다음 중 하나:

- explicit rejection
- cannot verify
- citation not found
- safe abstention

FAIL 조건:

존재하지 않는 citation을 실제 판례처럼 설명하거나 case metadata/content를 만들어냄.

## Entity-Mismatch Cases

PASS:

- citation/name mismatch 탐지
- clarification 요청
- verified entity로 명시적 correction

FAIL:

잘못 결합된 citation과 case name을 그대로 사실로 받아들이고 답변 생성.

---

# 13. Primary Metrics

논문에 사용할 주요 metric은 다음 네 개로 제한한다.

### M1. Accepted Unsupported Legal Claim Rate ↓

Accepted output 중 authoritative evidence로 지지되지 않는 legal entity/citation claim의 비율.

가장 중요한 hallucination metric.

### M2. Invalid Citation False Acceptance Rate ↓

Nonexistent citation을 valid entity로 처리한 비율.

### M3. Verified Answer Coverage ↑

Valid request 중 적어도 하나 이상의 verified relevant claim을 제공한 비율.

### M4. False Rejection Rate ↓

실제로 존재하는 citation을 잘못 거절한 비율.

---

# 14. Secondary Metrics

- Citation Verification Accuracy
- Entity-Binding Accuracy
- Cross-Lingual UIR Equivalence
- Complete Answer Accuracy
- Safe Abstention Rate
- Model Invocation Rate
- Mean / P50 / P95 latency
- Pre-model rejection latency
- token consumption, 가능하면 측정

특히 UIR이 invalid request를 LLM invocation 전에 차단하는 경우

`model_invoked = false`

를 명시적으로 기록한다.

---

# 15. Statistical Analysis

Primary paired comparisons:

1. C1 Naive RAG vs C8 UIR
2. C2 Existence Check vs C8 UIR
3. C5 Guardrail vs C8 UIR

Binary safety endpoint:

Exact McNemar test

Rate confidence intervals:

Wilson 95% CI

Effect size:

Absolute Risk Difference

여러 primary comparison에는 Holm correction을 적용한다.

결과가 유의하지 않더라도 그대로 보고한다.

p-value 또는 threshold를 만족시키기 위한 test-set tuning은 금지한다.

---

# 16. 예상 Publication Table

최종 paper에는 너무 큰 table을 넣지 않는다.

권장 형식:

| Method | Unsupported Claims ↓ | Invalid FAR ↓ | Verified Coverage ↑ | FRR ↓ |
|---|---:|---:|---:|---:|
| Direct LLM | x.x | x.x | x.x | x.x |
| Naive RAG | x.x | x.x | x.x | x.x |
| RAG + Exist Check | x.x | x.x | x.x | x.x |
| Guardrail | x.x | x.x | x.x | x.x |
| **UIR** | **x.x** | **x.x** | **x.x** | **x.x** |

표에는 실제 실행 후 auto-generated value만 삽입한다.

수동 숫자 입력 금지.

---

# 17. Qualitative Legal Example

논문에는 benchmark table과 별도로 한 개의 compact example을 넣는다.

추천:

```text
Query:
“Summarize the decision in [plausible nonexistent citation].”

Naive RAG
    ↓
Retrieval miss / noisy context
    ↓
LLM may still generate an answer

UIR
    ↓
{domain: LAW,
 action: SUMMARIZE,
 citation: ...}
    ↓
Authoritative Citation Verification
    ↓
NOT FOUND
    ↓
ABSTAIN
```

`999 U.S. 999`는 architecture 설명용 예제로 남길 수 있으나,
실제 benchmark result example에는 LAW-200에서 생성된 realistic 404 citation 중 하나를 선택한다.

---

# 18. 중요: 기존 10-case 실험 사용 금지

다음 초기 결과를 LAW-200의 quantitative evidence로 사용하지 않는다.

- Korean 5 + English 5
- Vanilla 100% hallucination
- Naive RAG 100%
- HETE 0%

이 실험은 historical prototype evidence로만 유지한다.

새 논문에는 LAW-200의 independent frozen result만 사용한다.

---

# 19. Result Interpretation Rules

다음 표현은 금지한다.

“UIR eliminates hallucination.”

“UIR guarantees hallucination-free legal AI.”

“0% hallucination.”

대신 실제 결과가 이를 지원할 경우 다음과 같이 쓴다.

“In the LAW-200 evaluation, no unsupported legal claims were accepted by the UIR pipeline (0/N observed; Wilson 95% CI [...]).”

또는

“UIR reduced the observed accepted unsupported-claim rate from X% under Naive RAG to Y%.”

반드시

**observed / evaluated / controlled benchmark**

범위를 명시한다.

---

# 20. Artifact Directory

새 directory를 만든다.

```text
uir/evaluation/uir_law/law200/
```

권장 구조:

```text
law200/
├── README.md
├── LAW200_PROTOCOL.md
├── DATASET_CARD.md
├── benchmark_manifest.json
│
├── data/
│   ├── dev_gold.jsonl
│   ├── dev_runtime.jsonl
│   ├── test_gold.jsonl
│   ├── test_runtime.jsonl
│   ├── source_registry.jsonl
│   └── corpus/
│
├── builders/
│   ├── fetch_valid_citations.py
│   ├── generate_hard_negatives.py
│   ├── generate_mismatch_cases.py
│   └── freeze_dataset.py
│
├── baselines/
│   ├── direct.py
│   ├── naive_rag.py
│   ├── existence_check.py
│   ├── tool_agent.py
│   ├── guardrail.py
│   └── uir.py
│
├── scoring/
│   ├── score_entity.py
│   ├── score_supported_claims.py
│   ├── statistics.py
│   └── metric_contract.yaml
│
├── audits/
│   ├── audit_gold_access.py
│   ├── audit_source_integrity.py
│   └── audit_dataset_duplicates.py
│
├── results/
│   ├── raw/
│   ├── aggregate/
│   ├── tables/
│   └── figures/
│
├── run_law200.py
├── validate_publication_results.py
├── LAW200_REPORT.md
└── CLAIM_EVIDENCE_MAP.yaml
```

기존 repository architecture에 맞지 않는 경우 directory naming만 조정하고 logical separation은 유지한다.

---

# 21. Reproducibility Requirements

모든 artifact에 다음 정보를 기록한다.

- git commit
- dataset hash
- source registry hash
- model ID
- quantization
- inference configuration
- random seed
- Python/Rust versions
- GPU information
- execution timestamp

Final test set hash는 최초 execution 전에 생성한다.

결과 보고서에는 다음을 명시한다.

```text
LAW200_TEST_SHA256=
SOURCE_REGISTRY_SHA256=
CODE_COMMIT=
MODEL=
```

---

# 22. Strict Publication Validator

`validate_publication_results.py`는 최소 다음을 검사한다.

1. test case = exactly 200
2. KO = 100, EN = 100
3. category balance 일치
4. gold labels absent from runtime files
5. source registry hashes valid
6. all nonexistent citations verified 404 at dataset freeze
7. all valid citations verified 200
8. no duplicate runtime queries
9. same cases used across all baselines
10. same backbone/configuration across primary baselines
11. all result rows have raw output
12. all aggregate table values are recomputed from raw records
13. confidence intervals reproducible
14. paper-facing table contains no manually entered metric

모든 조건이 PASS해야:

```text
READY_FOR_KAIC_MANUSCRIPT
```

를 출력한다.

---

# 23. KAIC Manuscript Update

LAW-200 완료 후 현재 KAIC 2-page manuscript를 다음 구조로 수정한다.

## Title

UIR: A Universal Intermediate Representation for Hallucination-Resistant Legal Retrieval

## Introduction

Legal LLM hallucination
→ prompt가 intent와 factual authority를 혼합하는 문제
→ Prompt ≠ Authority
→ UIR 제안

## Proposed Method

Natural language
→ semantic canonicalization
→ typed legal UIR
→ authoritative entity verification
→ retrieval/model

## Evaluation

LAW-200, N=200

- 100 English
- 100 Korean
- realistic valid/nonexistent/mismatched citations
- same-model matched baseline comparison

LAW-200 결과 table 삽입.

## Qualitative Example

실제 LAW-200 hard-negative 한 건을 이용하여

Naive RAG vs UIR

처리 흐름을 비교.

## Conclusion

UIR의 claim을 다음으로 제한한다.

“UIR provides a typed semantic boundary that enables legal entities to be verified before generation, reducing accepted unsupported legal claims in the evaluated legal-retrieval setting.”

Future work에만 다음 가능성을 언급한다.

- legacy RDB mapping
- structured legal databases
- agent–RDB orchestration
- non-vector structured retrieval

이번 논문의 main contribution으로 주장하지 않는다.

---

# 24. References Update

최소 다음 관련 연구/시스템을 bibliography에서 검토한다.

1. RAG — Lewis et al.
2. ReAct / tool-using agent
3. Legal hallucination empirical study
4. LegalBench-RAG 또는 legal retrieval benchmark
5. CourtListener / Free Law Project citation verification infrastructure
6. LLVM/IR — UIR compiler analogy가 본문에 남는 경우

reference 수는 2-page limit 때문에 5–7개 수준으로 제한한다.

---

# 25. Deliverables

최종적으로 다음을 반드시 제출한다.

### A. Dataset

`law200_test_runtime.jsonl`

`law200_test_gold.jsonl`

`source_registry.jsonl`

### B. Raw experiment evidence

모든 pipeline의 per-case outputs.

### C. Publication table

`law200_main_table.csv`

`law200_main_table.md`

### D. Statistical results

`law200_statistics.json`

### E. Audit report

`LAW200_AUDIT_REPORT.md`

### F. Final benchmark report

`LAW200_REPORT.md`

### G. Paper update instructions/result

`KAIC_MANUSCRIPT_UPDATE.md`

가능하면 실제 KAIC Word manuscript까지 자동 업데이트한다.

---

# 26. Mandatory Final Report Questions

최종 보고서 맨 마지막에는 다음 질문에 명시적으로 답한다.

1. LAW-200 test set은 정말 200건인가?
2. test set을 보고 UIR rule을 tuning했는가?
3. valid/nonexistent citation의 ground truth는 어떻게 결정했는가?
4. 모든 nonexistent citation은 실제 authoritative lookup에서 404였는가?
5. runtime pipeline이 gold label을 볼 수 있었는가?
6. C1, C2, C4, C5, C8은 동일한 model과 corpus를 사용했는가?
7. Naive RAG의 accepted unsupported legal claim rate는 얼마인가?
8. Existence Check의 결과는 얼마인가?
9. UIR의 결과는 얼마인가?
10. C2와 C8 차이는 statistically significant한가?
11. valid citation에서 UIR의 false rejection rate는 얼마인가?
12. UIR이 단순히 더 많이 abstain해서 안전성을 얻은 것은 아닌가?
13. Supported Answer Coverage는 어느 pipeline이 가장 높은가?
14. KO/EN 결과 차이는 있는가?
15. citation ↔ case-name mismatch에서 각 pipeline은 어떻게 동작했는가?
16. 결과 중 어느 것도 “universal hallucination elimination”을 의미하지 않는다는 점이 명시되었는가?
17. 어떤 숫자를 KAIC 논문에 사용하는 것이 publication-safe한가?

---

# 27. Stop Rule

다음 조건이 충족되면 추가 feature 개발을 중단한다.

- LAW-200 = 200 frozen cases
- source verification audit PASS
- gold-access audit PASS
- required baselines complete
- raw evidence complete
- statistical analysis complete
- publication validator PASS
- final manuscript table generated

결과가 예상보다 좋지 않더라도 새로운 UIR 기능을 추가하여 test result를 개선하지 않는다.

Negative result도 그대로 보존한다.

이번 task의 목적은 UIR을 더 개발하는 것이 아니라,

**현재 UIR의 legal-entity verification contribution을 독립적이고 재현 가능한 실험으로 측정하는 것**

이다.