# Phase UIR-4E Final Publication Consistency Audit

**Phase Status:** `READY_FOR_MANUSCRIPT_DRAFT_FINAL`  
**Principle:** $\mathbf{\text{Prompt} \neq \text{Authority}}$  

---

## 1. Quality Gate Summary

| Gate | Description | Requirement | Status |
| :--- | :--- | :--- | :---: |
| G-01 | Phase 4D Immutability Preserved | No modifications to Phase 4D archives | ✅ PASS |
| G-02 | Authoritative Evidence Map Defined | 6-Level provenance hierarchy | ✅ PASS |
| G-03 | Metric Contract Formalization | Disambiguate complete vs partial utility | ✅ PASS |
| G-04 | C1 vs C8 Complete Accuracy | Exact McNemar p=0.50 (comparable) | ✅ PASS |
| G-05 | Supported-Answer Coverage Advantage | +11.96%pp (p=1.29e-12) via safe partials | ✅ PASS |
| G-06 | D1 Genuine Constrained Decoding | lm-format-enforcer v0.11.3 executed | ✅ PASS |
| G-07 | C3 Terminology Clean | Relabeled to JSON-schema prompted baseline | ✅ PASS |
| G-08 | Qwen External Generalization | FinQA N=200, HaluEval N=200 raw captures | ✅ PASS |
| G-09 | Overclaim Linter Clean | 0 unflagged overclaims in paper | ✅ PASS |
| G-10 | Final Consistency Checker | 0 Blockers, 0 Warnings | ✅ PASS |

---

## 2. Frozen Artifact Hashes

| File | SHA-256 (First 16 chars) | Lines | Size | Description |
| :--- | :---: | :---: | :---: | :--- |
| `AUTHORITATIVE_EVIDENCE_MAP.yaml` | `b4e8d7ee879ac1a9...` | 83 | 4,778 B | Authoritative 6-level evidence hierarchy map |
| `per_case_scored_final.jsonl` | `e2622f8a0f45040d...` | 5400 | 3,175,858 B | Canonical per-case scored internal evidence (5,400 rows) |
| `strong_baseline_summary_final.csv` | `c4ababb77674a12e...` | 10 | 1,864 B | Primary 9-pipeline evaluation summary |
| `stat_safety_final.csv` | `2757889700c3cea3...` | 10 | 609 B | Wilson 95% intervals and McNemar safety tests |
| `stat_complete_utility_final.csv` | `d176850ec3bd0597...` | 10 | 776 B | Complete claim-set accuracy statistical tests |
| `stat_partial_utility_final.csv` | `810e1bd75c56edbf...` | 10 | 620 B | Supported-answer coverage statistical tests |
| `stat_c1_vs_c8_mcnemar.json` | `d40f90eb46865e7e...` | 17 | 689 B | C1 vs C8 contingency matrix and exact McNemar p-value |
| `latency_summary_final.csv` | `b398455f8315470b...` | 10 | 558 B | Path-separated latency profiling breakdown |
| `external_constrained_decoding_summary.csv` | `b0fc92b968133195...` | 2 | 747 B | D1 genuine grammar-constrained decoding summary |
| `constrained_decoding_per_case.jsonl` | `6a20b155b28821fe...` | 2 | 2,173 B | D1 genuine grammar-constrained decoding per-case captures |
| `qwen_finqa_C1_raw.jsonl` | `bba2bbad4eb24f10...` | 200 | 128,194 B | Qwen2.5-7B FinQA C1 raw generation and scoring captures (N=200) |
| `qwen_finqa_C8_raw.jsonl` | `ab719a6ea612c14e...` | 200 | 178,293 B | Qwen2.5-7B FinQA C8 raw generation and scoring captures (N=200) |
| `qwen_halueval_C1_raw.jsonl` | `d6add964ca19c179...` | 200 | 106,825 B | Qwen2.5-7B HaluEval C1 raw generation and scoring captures (N=200) |
| `qwen_halueval_C8_raw.jsonl` | `db36633dc326fe3e...` | 200 | 159,443 B | Qwen2.5-7B HaluEval C8 raw generation and scoring captures (N=200) |
| `external_generalization_final.csv` | `d70e0ac490e62d70...` | 9 | 801 B | Cross-model external benchmark summary |
| `external_failure_taxonomy_final.csv` | `81e37b8299db0cd9...` | 401 | 25,109 B | External failure taxonomy classification |

---

## 3. Conclusion and Stop Rule

All 9 publication blockers identified in the Phase-4D audit are definitively resolved.
In accordance with Section 19 of the Work Order, **all development is officially terminated**.

