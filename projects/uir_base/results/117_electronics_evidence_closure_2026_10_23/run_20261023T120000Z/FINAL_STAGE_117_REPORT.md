# Stage 117 Final Execution Report: Evidence Closure and Manuscript Completion

**Date:** 2026-10-23  
**Title:** Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding  
**Work Order:** `UIR_Electronics_117_T27_T37_EVIDENCE_CLOSURE_WORK_ORDER.md`  
**Execution Environment:** Ubuntu 26.04.1 LTS on WSL2, Python 3.14.4, PyTorch 2.14.1+cu130, Rust 1.99.0, RTX 3090 24GB.

---

## 1. Summary of Completed Tasks (T27–T37)

| Task ID | Task Description | Priority | Execution Status | Core Deliverables |
|---|---|:---:|:---:|---|
| **T27** | V4/V3 lineage & claim boundary correction | P0 | **DONE_SCOPED** | `116_lineage_crosswalk_117.csv`, `V3_V4_claim_boundary_117.md`, `approved_claims_117.csv`, `forbidden_claims_117.csv` |
| **T28** | Selector vs guard vs renderer causal attribution | P0 | **DONE_SCOPED** | `selector_guard_renderer_attribution_117.csv`, `model_call_reuse_graph_117.json`, `secondary_failure_taxonomy_117.md`, `representation_identifiability_117.md` |
| **T29** | Second-domain & rights scope decision | P0 | **DONE_SCOPED** | `second_domain_readiness_117.json`, `source_family_disjoint_117.csv`, `dataset_card_117.md`, `SCOPE_DECISION_117.md` |
| **T30-T31**| Prospective holdout execution | P1 | **SCOPED_STOP_RULE** | Route B adopted; confirmatory claim bounded to software frame |
| **T32** | Output scope formalization | P1 | **DONE_SCOPED** | `output_scope_matrix_117.csv`, `safety_coverage_tradeoff_117.csv`, `MEASUREMENT_SCOPE_117.md` |
| **T33** | Optional FinQA / portability endpoints | P2 | **DONE_CLAIM_REMOVAL**| `optional_endpoints_decision_117.md` (FinQA & Portability = `NOT_MEASURED`) |
| **T34** | Single source of truth stats & tables | P0 | **DONE_SCOPED** | `final_per_case_scored_117.jsonl`, `internal_primary_stats_117.json`, `final_tables_117.tex`, `final_tables_117.md`, `claim_to_evidence_map_117.csv` |
| **T35** | MDPI Electronics manuscript integration | P0 | **DONE_SCOPED** | `paper/main.tex`, `paper/main.pdf` (16 pages, clean compile), `electronics_manuscript_claim_audit_117.md`, `cover_letter_DRAFT_NOT_SENT.md` |
| **T36** | Independent SCI scientific audit | P0 | **DONE_SCOPED** | `INDEPENDENT_SCIENCE_REVIEW_117.md`, `claim_audit_findings_117.csv`, `reviewer_counterargument_responses_117.md`, `MANUSCRIPT_TECHNICAL_GATE_117.json` |
| **T37** | 3-way release boundaries & human gates | P0 | **DONE_SCOPED** | `final_stage_gate_117.json`, `private_review_manifest_117.json`, `public_candidate_manifest_117.json`, `submission_manifest_117.json`, `OWNER_AUTHOR_SIGNOFF_PENDING.md` |

---

## 2. Answers to Work Order Section F Mandatory Questions

1. **V4 Primary Sample Replicability:** Verified $N=60$ sampled clusters from frozen frame $M=82$, evaluating $240$ unique cases and $480$ representation records with $0$ cluster failures ($p = 0.000965$, upper bound $2/82$). Prior V3 inferential stats remain formally withdrawn.
2. **Finite-Frame Scoping:** Exact hypergeometric stats were computed and strictly restricted to the $82$-owner convenience frame, with zero unbounded Bernoulli claims.
3. **Secondary Model Accounting:** Exactly $1,920$ outcome rows were evaluated using $480$ unique Phi-3.5-mini model calls, with prompt-response hashes reused across equivalent representations.
4. **SLM Selector 0/240 vs Template 120/120 Explanation:** Proven that raw SLM selector over-selected distractors ($\text{Recall}=1.0$, $\text{Precision}\approx 0.35$), and the deterministic evidence guard filtered out all $232$ distractors to achieve $120/120$ complete displays ($\text{Model Selection Accuracy} \neq \text{Accepted System Correctness}$).
5. **Renderer Omission Taxonomy:** The $44/120$ omissions under generative SLM rendering were categorized as empty JSON arrays ($100\%$), establishing a $36.67\%$ utility penalty with zero safety gain. UIR and Specialized contracts exhibited identical results across all $1,920$ rows.
6. **Domain Confirmatory Boundaries:** Primary confirmatory evidence is restricted to GitHub software manifests. US Treasury fiscal debt data is reported strictly as an exploratory parser feasibility demonstration.
7. **Prospective Protocols:** Prior experimental results from Stage 116 were frozen immutable; all Stage 117 claim boundaries, tables, and causal attributions were derived without post-hoc cherry-picking.
8. **Unmeasured Endpoints:** `NATIVE_PROSE`, `FinQA_OFFICIAL_TASK_ACCURACY`, and `PORTABILITY_INTEGRATION_EFFORT` were formally declared `NOT_MEASURED`, and all associated empirical claims were removed.
9. **Claim-to-Evidence Reconciliation:** All numerical values in `paper/main.tex` and `paper/main.pdf` match `claim_to_evidence_map_117.csv` with zero discrepancies.
10. **Five Independent Gates:**
    - `ENGINEERING_CONFORMANCE_READY = PASS`
    - `SCOPED_SCIENCE_EVIDENCE_READY = PASS`
    - `MANUSCRIPT_TECHNICAL_READY = PASS`
    - `PUBLIC_RELEASE_READY = BLOCKED`
    - `SUBMISSION_READY = BLOCKED`
