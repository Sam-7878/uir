# LAW-200 Registered Evaluation Protocol

## Research question

Can typed semantic canonicalization and authoritative legal-entity verification through UIR reduce accepted unsupported legal claims compared with conventional LLM/RAG pipelines?

This protocol measures case-citation extraction, entity binding, verified metadata retrieval, and safe rejection in two independently reported jurisdiction strata. LAW-US-200 uses U.S. citations and CourtListener; LAW-KR-200 uses 대한민국 대법원 사건번호 and 국가법령정보 공동활용. The strata share the same scientific contract but are not pooled. Neither evaluates the wider HETE security architecture nor supports a claim of general hallucination elimination.

## Jurisdiction-specific authority semantics

- LAW-US-200 Category C requires CourtListener citation-lookup HTTP/citation status 404.
- LAW-KR-200 Category C starts from a verified case number, applies a small serial-number mutation, and requires that the official HTTP 200 search response contain no exact 사건번호 match. The registry normalizes that evidence to `lookup_status=404` and `verification_outcome=NOT_FOUND_EXACT_CASE_NUMBER`; publications must not call it an official HTTP 404.
- Each stratum independently contains test 200 and dev 40. Cross-jurisdiction aggregate rates are prohibited unless a future protocol registers them in advance.

## Frozen population

The test set has exactly 200 queries: 50 in each of four categories and 100 in each language. Each category uses 25 underlying entities expressed once in English and once in Korean.

1. A — authoritative valid citation.
2. B — authoritative valid citation with punctuation or surface variation.
3. C — a reporter-preserving mutation of a real citation retained only after CourtListener returns citation-level status 404.
4. D — a real citation combined with the canonical name of a different real case.

The separate 40-query development set has 10 cases per category. Test queries are not inspected to change parsing, verification, prompting, thresholds, or scoring after freeze.

## Authority and provenance

Dataset construction uses `POST https://www.courtlistener.com/api/rest/v4/citation-lookup/`. Only unambiguous status-200 records with a case name and cluster ID become valid entities. Only syntactically parsed status-404 results derived by an allowed small mutation become Category C entities. Status 300, 400, 429, and all transport failures are excluded.

For LAW-US-200, every CourtListener HTTP response body is stored byte-for-byte under `data/source_responses/`. For LAW-KR-200, official JSON is stored under `data/kr/source_responses/` after the OC credential embedded in response links is deterministically replaced with `[REDACTED_OC]`; the sanitized response and canonical entries are hash-bound into the registry. Final evaluation uses frozen snapshots and performs no network lookup.

The shared corpus contains citation, canonical case name, court, filing date, source ID, and provenance pointer. It does not add a model-written holding or syllabus. All retrieval-capable methods use precisely this corpus.

## Runtime/oracle separation

The runtime file contains only `case_id` and `query`. Category, validity, expected action, gold name/citation, mutation type, and oracle outcome exist only in the scoring file. The execution program reads and records hashes for only the runtime set, registry, and shared corpus before generation. Scoring is a separate command.

## Matched pipelines

- C0 Direct: model only, no retrieval or verification.
- C1 Naive RAG: deterministic lexical top-3 retrieval, no entity verification.
- C2 Existence Check: deterministic citation extraction and existence lookup; no citation/name binding.
- C4 Tool Agent: the model chooses whether and how to call `lookup_citation`, then produces a final answer from its tool result.
- C5 Guardrail: naive retrieval plus a post-generation evidence/citation/name allow-list.
- C8 UIR: language frontend, typed canonical citation, pre-generation citation/name binding, exact verified retrieval, model, and output contract.

All primary generations use `phi3.5:latest`, temperature 0, top-p 1, max 192 output tokens, seed 20260911, the same Ollama endpoint, hardware, query set, and corpus. The tool agent requires two calls by design, but both use the same configuration. An optional Qwen2.5-7B replication is not substituted for the primary experiment.

## Outcome contract

Accepted decisions are `ANSWER` and `CORRECT`. `REJECT` and `CLARIFY` are safe non-acceptance decisions. A verified answer must contain exactly the authoritative citation, a matching case name, and the frozen source ID. No LLM judge is used.

Primary metrics:

- Accepted Unsupported Legal Claim Rate: unsupported accepted outputs / accepted outputs.
- Invalid Citation FAR: accepted Category C outputs / Category C outputs.
- Verified Answer Coverage: source-bound answers / valid A+B requests.
- False Rejection Rate: REJECT or CLARIFY / valid A+B requests.

The case-level accepted-unsupported indicator is also retained for paired analysis and to avoid hiding abstention effects. Secondary metrics include entity-binding accuracy, safe abstention, model invocation, KO/EN strata, tokens, and latency.

## Statistics

Wilson 95% intervals accompany rates. Exact paired McNemar tests compare C1/C2/C5 with C8 on accepted unsupported claims. Holm correction is applied across these three comparisons. The effect size is C8 minus baseline absolute risk difference. Null or negative results are retained.

## Stop and correction rule

Feature development stops after the frozen 200-case test, all required raw results, statistics, audits, generated tables, and publication validator pass. A genuine software defect requires a written bug note, preserved prior outputs, and a complete rerun. Results may not be used to tune the test pipeline.
