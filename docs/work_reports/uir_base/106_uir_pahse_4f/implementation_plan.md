# Implementation Plan — Phase UIR-4F: Final Metric Closure & Complete Baseline Evidence

Phase UIR-4F is a **final metric and evidence closure phase**. It introduces **no new UIR architectures, policy features, model backbones, languages, or domains**. Its objective is to resolve the four final empirical discrepancies identified in the Phase-4E archive, execute the genuine grammar-constrained decoding baseline (D1) on all 600 internal cases, formally decouple model generation behavior from accepted system output behavior, and produce the definitive manuscript evidence package.

---

## User Review Required

> [!IMPORTANT]
> **D1 Genuine Grammar-Constrained Decoding on All 600 Cases:**
> In Phase 4E, D1 (`lm-format-enforcer v0.11.3` + Ollama GBNF) was only piloted on 2 cases. Phase 4F executes D1 on the **entire frozen 600 internal cases** (418 COMMIT-eligible) using Phi-3.5 with token-level logits masking. This will provide the rigorous, peer-review-defensible proof that grammar constraints guarantee syntax (100% schema validity) but fail on evidence grounding (high unsupported rate on ungrounded prompts).

> [!IMPORTANT]
> **Separation of Denominators for Security (Attack Success):**
> - **Primary Security Metric:** `Adversarial ASR (N=50)` = successful attacks / 50 adversarial cases (C0=66%, C1=92%, C2=84%, C8=0%).
> - **Secondary Workload Metric:** `Workload Attack Incidence (N=600)` = successful attacks / 600 total cases (C0=5.50%, C1=7.67%, C2=7.00%, C8=0.00%).
> The primary manuscript table will strictly report `Adversarial ASR (N=50)`.

> [!IMPORTANT]
> **Decoupling Model Behavior from System Acceptance:**
> 1. `raw_unsupported_generation_rate` (model behavior) vs `accepted_unsupported_claim_rate` (system safety).
>    - In Qwen FinQA C8, the 9 cases with raw unregistered numbers are confirmed to be rejected or safe partials; `accepted_unsupported_claim_count_C8 == 0`.
> 2. In HaluEval, `raw_semantic_accuracy` (Qwen C8 = 50.0%) is separated from `contract_validity_rate` (0.0%), `accepted_e2e_accuracy` (0.0%), and `safe_rejection_rate` (100.0%).

---

## Proposed Changes

### 1. Immutability & Workspace Setup
- Treat `results/uir_phase3d/`, `results/uir_phase4/`, `results/uir_phase4b/`, `results/uir_phase4c/`, `results/uir_phase4d/`, `results/uir_phase4e/` as strictly immutable.
- Establish clean directories:
  - `uir/results/uir_phase4f/`
  - `uir/evaluation/uir_phase4f/`
  - `uir/docs/work_reports/uir_phase4f/`
  - `uir/docs/work_reports/106_uir_pahse_4f/` (reports will be mirrored here)

---

### 2. Metric Contract & Provenance Specifications

#### [NEW] [`uir/evaluation/uir_phase4f/METRIC_CONTRACT_PUBLICATION_FINAL.yaml`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4f/METRIC_CONTRACT_PUBLICATION_FINAL.yaml)
Formal YAML specification defining all primary and secondary endpoints, numerators, denominators, eligible cohorts, mathematical formulas, and scientific meanings:
- `complete_claim_set_accuracy` (Primary Complete Utility: full claim set / 418 COMMIT-eligible)
- `supported_answer_coverage` (Secondary Partial Utility: $\ge 1$ verified claim / 418 COMMIT-eligible)
- `safe_partial_answer_rate` & `no_verified_answer_rate`
- `adversarial_attack_success_rate` ($N=50$) vs `workload_attack_incidence_rate` ($N=600$)
- `raw_unsupported_generation_rate` vs `accepted_unsupported_claim_rate`
- `raw_semantic_accuracy`, `contract_validity_rate`, `accepted_e2e_accuracy`, `safe_rejection_rate`
- `finqa_execution_accuracy`, `finqa_safe_execution_rate`

#### [NEW] [`uir/results/uir_phase4f/QWEN_MODEL_PROVENANCE.json`](file:///d:/_Work/goat_bank/uir/results/uir_phase4f/QWEN_MODEL_PROVENANCE.json)
Immutable cryptographic provenance for Qwen2.5-7B-Instruct:
- Tag: `qwen2.5:7b`
- Blob SHA-256: `2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730`
- Ollama runtime version, 16 threads, context length 4096, seed 42, temperature 0.0.

---

### 3. Execution of Genuine Grammar-Constrained Decoding Baseline (D1) on All 600 Cases

#### [NEW] [`uir/evaluation/uir_phase4f/run_constrained_decoding_600.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4f/run_constrained_decoding_600.py)
- Runs `D1_EXTERNAL_CONSTRAINED_DECODING` on the exact frozen 600 internal cases using Phi-3.5 with `lm-format-enforcer v0.11.3` / Ollama GBNF token logits masking.
- Generates:
  - [`results/uir_phase4f/d1_constrained_raw_600.jsonl`](file:///d:/_Work/goat_bank/uir/results/uir_phase4f/d1_constrained_raw_600.jsonl) (600 rows with prompt hash, raw response, response SHA-256, schema validity, parsed claims, scoring)
  - [`results/uir_phase4f/d1_constrained_summary_600.csv`](file:///d:/_Work/goat_bank/uir/results/uir_phase4f/d1_constrained_summary_600.csv)

---

### 4. Rescoring & Metric Disaggregation Engine

#### [NEW] [`uir/evaluation/uir_phase4f/rescore_publication_final.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4f/rescore_publication_final.py)
Reads frozen raw captures from Phase 4D/4E (Phi internal 600, Phi external, Qwen external 200 each) and Phase 4F D1 600 raw:
1. **Internal Safety & Security:**
   - Evaluates `Adversarial ASR (N=50)` and `Workload Incidence (N=600)` across C0–C8 and D1.
   - Computes Wilson 95% score intervals for accepted unsupported claim rates.
2. **Internal Complete & Partial Utility:**
   - Re-verifies exact McNemar test for C1 vs C8 complete accuracy ($p = 0.50$).
   - Calculates binary McNemar test for C1 vs C8 supported-answer coverage.
3. **External Benchmark Disaggregation:**
   - **FinQA:** Separates raw parse success, contract validity, safe execution success, official execution accuracy, raw unsupported generation, and accepted unsupported claim rate.
   - For Qwen FinQA C8: inspects the 9 raw unsupported cases, categorizes each (REJECTED / SAFE_PARTIAL / ACCEPTED), and verifies `accepted_unsupported_claim_count_C8 == 0`.
   - **HaluEval:** Separates `raw_semantic_accuracy` from `contract_validity_rate` and `accepted_e2e_accuracy`.
4. Outputs:
   - `results/uir_phase4f/internal_final.csv`
   - `results/uir_phase4f/security_final.csv`
   - `results/uir_phase4f/finqa_external_final.csv`
   - `results/uir_phase4f/halueval_external_final.csv`
   - `results/uir_phase4f/constrained_baseline_final.csv`
   - `results/uir_phase4f/external_case_scored_final.jsonl`
   - `results/uir_phase4f/stat_complete_utility_final.csv`
   - `results/uir_phase4f/stat_supported_coverage_final.csv`
   - `results/uir_phase4f/stat_security_final.csv`

---

### 5. Automated Publication Table Generation

#### [NEW] [`uir/evaluation/uir_phase4f/generate_final_tables.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4f/generate_final_tables.py)
Reads exclusively from Phase 4F final CSVs and generates:
- `docs/work_reports/uir_phase4f/generated_tables_final.md`
- `docs/work_reports/uir_phase4f/generated_tables_final.tex`
- Tables generated:
  - **Table 1: Internal Safety & Security** (Accepted Unsupported Claims, Adversarial ASR $N=50$, Invalid Entity FAR, Policy Bypass)
  - **Table 2: Internal Utility** (Complete Accuracy, Supported Coverage, Safe Partial, No Answer, Conditional Precision, Macro Recall)
  - **Table 3: Constrained Decoding Comparison** (D1 $N=600$ vs C3 vs C8)
  - **Table 4: FinQA Cross-Model Evaluation** (Raw Model Generation vs Accepted E2E Accuracy)
  - **Table 5: HaluEval Cross-Model Evaluation** (Raw Semantic Accuracy, Contract Validity, Accepted E2E Accuracy, Raw Unsupported Generation, Accepted Unsupported Claims, Safe Rejection)

---

### 6. Publication Consistency Checker v2 & Quality Gate

#### [NEW] [`uir/evaluation/uir_phase4f/check_publication_consistency_v2.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4f/check_publication_consistency_v2.py)
Enforces all Phase 4F gate assertions:
- `d1_full_600_complete`: D1 `total_cases == 600`, `commit_eligible_cases == 418`
- `attack_denominator_separated`: Table 1 uses $N=50$ for primary ASR
- `raw_vs_accepted_unsupported_metrics_separated`: Raw model generation $\ne$ Accepted unsupported claims
- `c8_accepted_unsupported_claim_count == 0`
- `halueval_semantic_vs_accepted_accuracy_separated`: When contract validity is 0%, accepted E2E accuracy must be 0%
- `qwen_model_provenance_frozen`: All 800 external rows reference immutable model digest
- `qwen_raw_rows == 200` per pipeline
- `report_values_match_csvs`: Exact match across CSV, tables, and reports
- Emits: `RESULT: READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL` (0 blockers, 0 warnings).

---

### 7. Final Manifest & Closure Reports

#### [NEW] [`uir/evaluation/uir_phase4f/finalize_manifest_v2.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4f/finalize_manifest_v2.py)
- Computes SHA-256 digests and row counts for all Phase 4F artifacts.
- Emits:
  - `results/uir_phase4f/PHASE4F_FINAL_MANIFEST.json`
  - `results/uir_phase4f/FINAL_PUBLICATION_CONSISTENCY_V2.md`
  - `docs/work_reports/uir_phase4f/REPORT_PHASE4F_FINAL_METRIC_CLOSURE.md` (mirrored in `uir/docs/work_reports/106_uir_pahse_4f/`)

---

## Verification Plan

### Automated Verification
1. **D1 N=600 Generation:**
   ```bash
   wsl -d Ubuntu bash -c "cd /mnt/d/_Work/goat_bank && source .venv/bin/activate && PYTHONPATH=uir python uir/evaluation/uir_phase4f/run_constrained_decoding_600.py"
   ```
   *Verify:* `wc -l results/uir_phase4f/d1_constrained_raw_600.jsonl` yields 600 lines.
2. **Rescore & Disaggregation:**
   ```bash
   wsl -d Ubuntu bash -c "cd /mnt/d/_Work/goat_bank && source .venv/bin/activate && PYTHONPATH=uir python uir/evaluation/uir_phase4f/rescore_publication_final.py"
   ```
   *Verify:* All 9 summary CSVs generated, `c8_accepted_unsupported_count == 0`.
3. **Table Generation:**
   ```bash
   wsl -d Ubuntu bash -c "cd /mnt/d/_Work/goat_bank && source .venv/bin/activate && PYTHONPATH=uir python uir/evaluation/uir_phase4f/generate_final_tables.py"
   ```
   *Verify:* Tables 1–5 populated with consistent numbers.
4. **Consistency Audit (Gate 10 v2):**
   ```bash
   wsl -d Ubuntu bash -c "cd /mnt/d/_Work/goat_bank && source .venv/bin/activate && PYTHONPATH=uir python uir/evaluation/uir_phase4f/check_publication_consistency_v2.py"
   ```
   *Expected Output:* `BLOCKERS: 0`, `WARNINGS: 0`, `RESULT: READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL`.
5. **Manifest & Report Freeze:**
   ```bash
   wsl -d Ubuntu bash -c "cd /mnt/d/_Work/goat_bank && source .venv/bin/activate && PYTHONPATH=uir python uir/evaluation/uir_phase4f/finalize_manifest_v2.py"
   ```
   *Verify:* `PHASE4F_FINAL_MANIFEST.json` and `FINAL_PUBLICATION_CONSISTENCY_V2.md` created with cryptographic verification.
