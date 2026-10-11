# LAW-200 Dataset Card

## Summary

LAW-200 contains two bilingual, jurisdiction-specific query benchmarks. LAW-US-200 uses CourtListener U.S. case citations; LAW-KR-200 uses 대한민국 대법원 사건번호 from 국가법령정보 공동활용. Each stratum independently isolates citation existence and citation-to-case-name binding and independently uses the balance below.

| Split | A valid | B surface | C nonexistent | D mismatch | English | Korean | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Development | 10 | 10 | 10 | 10 | 20 | 20 | 40 |
| Test | 50 | 50 | 50 | 50 | 100 | 100 | 200 |

## Construction

Valid citations begin as hand-selected U.S. Reports candidates but receive no valid label until a live CourtListener v4 lookup returns status 200 with an unambiguous cluster. Hard negatives are small volume/page/digit mutations of a verified citation and are admitted only when the same endpoint parses the citation and returns status 404. Mismatch cases combine two independently verified real entities.

English and Korean members of a pair share the same underlying legal entity and intent. They are separate queries, not translations of authoritative legal text.

For LAW-KR-200, valid records are Supreme Court cases whose official decision date is not later than the retrieval date. Hard negatives are small serial-number mutations of a verified 사건번호. Because the Korean search API returns HTTP 200 for searches, a negative is admitted only when the official response contains no exact 사건번호 match; `lookup_status=404` is an internal normalized NOT_FOUND state. Persisted official responses redact the access credential before hashing and storage.

## Files and visibility

- Runtime: opaque ID and user query. Safe for pre-generation access.
- Gold: language, category, pair, authority identity, and expected safe behavior. Scoring-only.
- Registry: normalized source snapshot plus cryptographic bindings to raw API responses.
- Corpus: verified identity metadata shared by all retrieval pipelines.

## Intended use

The dataset supports controlled comparison of legal citation verification mechanisms and bilingual semantic canonicalization. It is not a substantive legal question-answering benchmark and must not be used to claim legal competence, hallucination elimination, or coverage of all U.S. reporters.

## Known limitations

- Each official snapshot defines only its own jurisdictional authority boundary.
- Answers are evaluated for case identity metadata, not holdings or legal reasoning.
- Korean-stratum mismatch names are official Korean case-name metadata even in English prompts; this is not an English translation benchmark.
- Parsing is intentionally scoped to `U.S.` reporter forms in LAW-US-200 and Supreme Court 사건번호 forms in LAW-KR-200.
- CourtListener status 404 means the citation was syntactically recognized but not found in that source at retrieval time; it is not a metaphysical proof that no decision exists anywhere.
- A local 3.8B model may have limited Korean instruction following.
- The 200 cases are controlled and do not imply universal deployment behavior.

## License and source terms

The benchmark code is distributed under the repository license. CourtListener and 국가법령정보 공동활용 records retain provenance pointers and must be used in accordance with source terms and applicable law. No API credential is stored.
