# Phase UIR-4F Final Publication Consistency Audit (v2)

**Phase Status:** `READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL`  
**Principle:** $\mathbf{\text{Prompt} \neq \text{Authority}}$  

---

## 1. Quality Gate Summary

| Gate | Description | Requirement | Status |
| :--- | :--- | :--- | :---: |
| G-01 | Prior Phases Immutability Preserved | Phase 4D and Phase 4E archives unaltered | ✅ PASS |
| G-02 | D1 Constrained Decoding Full N=600 | Genuine token logits masking on all 600 cases | ✅ PASS |
| G-03 | D1 Commit Cohort Equivalence | Exactly 418 COMMIT-eligible cases evaluated | ✅ PASS |
| G-04 | Attack Denominator Separation | Adversarial ASR strictly uses N=50 denominator | ✅ PASS |
| G-05 | Workload Attack Incidence Disambiguated | Total workload incidence reported separately (N=600) | ✅ PASS |
| G-06 | Raw vs Accepted Unsupported Separation | Model raw generation != Accepted system output | ✅ PASS |
| G-07 | C8 Zero Accepted Unsupported Invariant | Accepted unsupported claim count == 0 on all cases | ✅ PASS |
| G-08 | HaluEval Decoupling Verified | Raw Semantic Acc != Contract Validity != Accepted E2E Acc | ✅ PASS |
| G-09 | Qwen Immutable Provenance Frozen | Exact blob digest, Ollama 0.32.14, seed 42 frozen | ✅ PASS |
| G-10 | Full Cross-Model N=200 Replicated | FinQA and HaluEval genuine N=200 raw captures | ✅ PASS |
| G-11 | Honest Primary Utility Grounding | C1 vs C8 complete accuracy parity (p=0.50) preserved | ✅ PASS |
| G-12 | Publication Consistency Checker v2 | 0 Blockers, 0 Warnings | ✅ PASS |

---

## 2. Frozen Artifact Hashes

| File | SHA-256 (First 16 chars) | Lines | Size | Description |
| :--- | :---: | :---: | :---: | :--- |
| `QWEN_MODEL_PROVENANCE.json` | `5a7b34c26b08378d...` | 21 | 624 B | Qwen2.5-7B immutable cryptographic model identity and config |
| `d1_constrained_raw_600.jsonl` | `1cd03045e750864b...` | 600 | 624,160 B | D1 genuine grammar-constrained decoding raw captures (N=600) |
| `d1_constrained_summary_600.csv` | `71bf10e94df510c7...` | 2 | 913 B | D1 genuine grammar-constrained decoding summary |
| `internal_final.csv` | `bdfaea358d3b44a3...` | 11 | 1,653 B | Internal 9-pipeline evaluation summary (N=600, N_commit=418) |
| `security_final.csv` | `de5ab234eec962eb...` | 11 | 733 B | Security summary with explicit Adversarial ASR (N=50) vs Workload Incidence |
| `constrained_baseline_final.csv` | `75b86e45d14038a8...` | 4 | 728 B | Constrained decoding baseline comparison (C3 vs D1 vs C8) |
| `finqa_external_final.csv` | `9de5d8ca1ca7eea9...` | 5 | 666 B | FinQA cross-model evaluation with raw vs accepted separation (N=200) |
| `halueval_external_final.csv` | `86b6014a43adcee4...` | 5 | 611 B | HaluEval cross-model evaluation with semantic vs accepted E2E accuracy (N=200) |
| `external_case_scored_final.jsonl` | `93c99ae1b801332c...` | 800 | 731,154 B | External benchmark scored cases with model provenance reference |
| `stat_complete_utility_final.csv` | `84aeca05d64dadca...` | 2 | 478 B | Complete claim-set accuracy statistical test (exact McNemar p=0.50) |
| `stat_supported_coverage_final.csv` | `1a6e2a20491d3d36...` | 2 | 529 B | Supported-answer coverage statistical test (+11.96%pp, p=1.29e-12) |
| `stat_security_final.csv` | `dcdfb7f094e4229e...` | 2 | 372 B | Adversarial attack success rate statistical test (N=50, p < 0.001) |

---

## 3. Section 16 Stop Rule Invocation

All four publication blockers (A, B, C, D) identified in the Phase-4E audit are definitively resolved.
In accordance with Section 16 of the Work Order:
> Once `READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL` is reached: **STOP ALL DEVELOPMENT.**

All feature, baseline, model, and benchmark development is permanently halted.
