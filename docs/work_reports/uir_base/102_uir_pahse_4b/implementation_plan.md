# Implementation Plan — Phase UIR-4B: Final Evidence Integrity, Baseline Fidelity, and Leakage Audit

This plan establishes an end-to-end, auditable single source of truth for the primary journal manuscript:
**"A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents"**
strictly following the work order in [`CODEX_UIR_PHASE4B_FINAL_EVIDENCE_INTEGRITY_INSTRUCTIONS.md`](file:///d:/_Work/goat_bank/uir/docs/work_reports/101_uir_pahse_4b/CODEX_UIR_PHASE4B_FINAL_EVIDENCE_INTEGRITY_INSTRUCTIONS.md).

---

## User Review Required

> [!IMPORTANT]
> **Phase-4 Evidence Preservation Guarantee**:  
> `results/uir_phase3d/` and `results/uir_phase4/` will remain completely unmodified as immutable historical records. All new Phase 4B artifacts will be written to `results/uir_phase4b/`, `evaluation/uir_phase4b/`, and `docs/work_reports/uir_phase4b/`.

> [!NOTE]
> **Cross-Backbone Scoping (Option B Selected)**:  
> As recommended by the work order when not running a full secondary LLM training/eval run, we explicitly adopt **Option B**:
> - We remove empirical claims implying cross-backbone multi-model replication.
> - We explicitly state: *"The UIR architecture is model-agnostic by interface contract, but empirical SLM results in this paper were evaluated on Microsoft Phi-3.5-mini-instruct."*

---

## Proposed Changes & Execution Modules

### Component 1: Metric Contract & Invariant Preservation
Establish a rigid, auditable metric definition file so no metric names collide or use ambiguous denominators.

#### [NEW] [`evaluation/uir_phase4b/METRIC_CONTRACT.yaml`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4b/METRIC_CONTRACT.yaml)
- Define every metric formally with: `definition`, `numerator`, `denominator`, `eligibility`, `unit`, `higher_is_better`, `undefined_behavior`, `source_fields`.
- Explicitly resolve the denominator conflict (Issue 2):
  - `numeric_exact_match_all_cases`: Denominator = all $N=1,500$ benchmark cases (yields 86.67% for C8 due to rejection of invalid/adversarial queries).
  - `numeric_exact_match_numeric_eligible`: Denominator = only valid, benign cases where numeric calculation was requested (yields 100.0% for C8).
- Disambiguate `unsupported_claim_acceptance_rate`, `attack_success_rate`, `policy_bypass_rate`, `useful_answer_rate`, `false_rejection_rate`, `claim_precision`, `claim_recall`, `provenance_coverage`, `provenance_correctness`, `execution_accuracy`, `condition_ast_exact_match`, `parse_success_rate`.

---

### Component 2: External Benchmark Audit & Leakage Tests (FinQA & HaluEval)
Resolve conflicting FinQA numbers (Issue 1) and guarantee zero gold label leakage (Issue 5).

#### [NEW] [`results/uir_phase4b/external_benchmark_audit.json`](file:///d:/_Work/goat_bank/uir/results/uir_phase4b/external_benchmark_audit.json)
- Record official repository URLs, commit hashes, licenses, dataset SHA-256 hashes, subset sizes ($N=200$ each).
- Explicitly partition schema fields into:
  - **Runtime Input Fields**: (FinQA: `case_id`, `question`, `text_context`, `table_context`; HaluEval: `case_id`, `dialogue_history`, `user_query`, `retrieved_documents`).
  - **Scoring-Only Fields (Prohibited from Runtime)**: (FinQA: `official_ground_truth`, `gold_program`, `gold_reasoning_chain`; HaluEval: `is_adversarial_query`, `hallucinated_foil`, `ground_truth_answer`).

#### [NEW] [`evaluation/uir_phase4b/test_benchmark_leakage.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4b/test_benchmark_leakage.py)
- Implement automated leakage unit tests:
  - `test_finqa_gold_answer_not_in_runtime_prompt`
  - `test_finqa_gold_program_not_in_verified_factset`
  - `test_finqa_gold_label_scoring_only`
  - `test_halueval_label_not_in_runtime_prompt`
  - `test_halueval_gold_decision_scoring_only`

#### [NEW] Raw Prediction Records & Frozen Scoring
- Execute each pipeline (C1, C2, C4, C8) and output raw predictions:
  - `results/uir_phase4b/finqa_predictions_C1.jsonl`
  - `results/uir_phase4b/finqa_predictions_C2.jsonl`
  - `results/uir_phase4b/finqa_predictions_C4.jsonl`
  - `results/uir_phase4b/finqa_predictions_C8.jsonl`
  - `results/uir_phase4b/halueval_predictions_C1.jsonl`
  - `results/uir_phase4b/halueval_predictions_C2.jsonl`
  - `results/uir_phase4b/halueval_predictions_C4.jsonl`
  - `results/uir_phase4b/halueval_predictions_C8.jsonl`
- Execute frozen scorer to generate:
  - `results/uir_phase4b/external_finance_results_phase4b.csv`
  - `results/uir_phase4b/external_groundedness_results_phase4b.csv`
  - *Fix the C4/C8 prediction variance bug from Phase 4 so the reported exact match numbers match the true prediction outputs (e.g. C1=62.0%, C2=64.0%, C4=84.0%, C8=94.5%).*

---

### Component 3: Strong Baseline Fidelity Audit & Model Execution Manifest
Clarify what each baseline actually implements (Issue 6) and record complete SLM runtime provenance (Issue 7).

#### [NEW] [`results/uir_phase4b/BASELINE_FIDELITY.md`](file:///d:/_Work/goat_bank/uir/results/uir_phase4b/BASELINE_FIDELITY.md)
- Document C0 through C8:
  - Claimed label, actual implementation, underlying packages/libraries, configuration parameters, and exact differences from published papers.
  - Adopt publication-safe designations for approximations:
    - C5: `guardrail-style baseline (inspired by NeMo Guardrails)`
    - C6: `corrective-retrieval baseline (CRAG-inspired)`
    - C7: `graph-structured RAG baseline (GraphRAG-inspired)`

#### [NEW] [`results/uir_phase4b/MODEL_EXECUTION_MANIFEST.json`](file:///d:/_Work/goat_bank/uir/results/uir_phase4b/MODEL_EXECUTION_MANIFEST.json)
- Record model selector (`microsoft/Phi-3.5-mini-instruct`), HuggingFace commit hash, tokenizer config, BitsAndBytes NF4 4-bit quantization config, generation config (`do_sample=False`, `temperature=0.0`, `max_new_tokens=128`), PyTorch 2.5.1+cu121, CUDA version, GPU device (NVIDIA GeForce RTX 4070 Laptop GPU, 8GB VRAM), git commit hash, and worktree status.

---

### Component 4: Real Wall-Clock Latency & Resource Instrumentation
Measure true GPU execution times with synchronization (Issue 7).

#### [NEW] [`evaluation/uir_phase4b/measure_latency.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4b/measure_latency.py)
- Benchmark with `time.perf_counter_ns()` and `torch.cuda.synchronize()` before and after GPU execution.
- Record warm-up vs steady-state runs over multiple seeds.
- Measure separate stages:
  - `retrieval_ms`, `prefill_ms`, `generation_ms`, `uir_compile_ms`, `policy_ms`, `output_validation_ms`, `end_to_end_ms`, `output_tokens`, `tokens_per_sec`.
- Output:
  - `results/uir_phase4b/latency_raw_phase4b.csv`
  - `results/uir_phase4b/latency_summary_phase4b.csv`
  - `results/uir_phase4b/resource_raw_phase4b.csv`

---

### Component 5: Corrected Mutation Fault-Injection Suite (MUT-05 Resolution)
Resolve the 75% MUT-05 contradiction (Issue 3).

#### [NEW] [`evaluation/uir_phase4b/mutation_fault_injection_phase4b.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4b/mutation_fault_injection_phase4b.py)
- Inspect and classify all truncated structured outputs into:
  - `SAFE_REJECT`: malformed syntax or unverified fact ref caught and rejected.
  - `SAFE_PARTIAL_RECOVERY`: valid prefix extracted with only verified fact refs.
  - `UNSAFE_ACCEPT`: invalid or unverified claim emitted to user.
  - `TEST_HARNESS_ERROR`: test artifact.
- Ensure `OutputSchemaValidator` checks both JSON validity and fact-reference registry membership.
- Enforce publication gate: **`UNSAFE_ACCEPT = 0`**.
- Output: `results/uir_phase4b/mutation_test_report_phase4b.csv`.

---

### Component 6: Per-Case Evidence Records & True Paired Statistics
Generate full per-case JSONL rows (Issue 4) and recompute paired statistics (Issue 14).

#### [NEW] [`results/uir_phase4b/per_case_evidence.jsonl`](file:///d:/_Work/goat_bank/uir/results/uir_phase4b/per_case_evidence.jsonl)
- Emit 1,500 cases $\times$ 9 pipelines = 13,500 rows adhering strictly to the JSON schema in Section 3 of the work order:
  - `case_id`, `dataset`, `split`, `pipeline`, `model`, `model_config_hash`, `input_hash`, `retrieval`, `tool_calls`, `uir` (semantic_digest, policy_decision, verified_fact_ids), `raw_model_output`, `raw_model_output_sha256`, `final_output`, `accepted_claims`, `rejected_claims`, `gold_scoring_fields`, `metrics`, `timing`, `resource`.

#### [NEW] Derived Summary CSVs & Paired Statistics
- Recompute directly from `per_case_evidence.jsonl`:
  - `results/uir_phase4b/strong_baseline_summary_phase4b.csv`
  - `results/uir_phase4b/groundedness_summary_phase4b.csv`
  - `results/uir_phase4b/safety_utility_summary_phase4b.csv`
  - `results/uir_phase4b/condition_semantics_summary_phase4b.csv`
- Recompute true paired tests using matched case outcomes:
  - `results/uir_phase4b/stat_safety_phase4b.csv` (McNemar exact test on discordant pairs, risk differences, 95% Wilson CIs).
  - `results/uir_phase4b/stat_utility_phase4b.csv` (Paired Wilcoxon signed-rank test, Holm-Bonferroni correction).
  - `results/uir_phase4b/stat_latency_phase4b.csv` (Paired Wilcoxon signed-rank test on latency differences).

---

### Component 7: Condition-Semantics Provenance & Human Diagnostic Audit
Audit condition agreement provenance (Issue 11).

#### [NEW] Condition Semantics Audit Records
- Create `results/uir_phase4b/condition_audit_raw_R1.jsonl`, `R2.jsonl`, `R3.jsonl`.
- Create `results/uir_phase4b/condition_audit_manifest.json`.
- Accurately label results as a **"representation-level consistency diagnostic"** rather than unanchored "inter-model agreement", noting human-in-the-loop limits.

---

### Component 8: Automatic Publication Consistency Checker
Verify all numbers across raw evidence, aggregate CSVs, work report, and LaTeX paper (Issue 13).

#### [NEW] [`evaluation/uir_phase4b/check_publication_consistency.py`](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4b/check_publication_consistency.py)
- Cross-validate:
  1. Raw evidence (`per_case_evidence.jsonl`) $\iff$ Aggregate CSVs (`strong_baseline_summary_phase4b.csv`, etc.).
  2. Sample counts and denominators match `METRIC_CONTRACT.yaml`.
  3. External benchmark predictions match external benchmark results CSVs.
  4. LaTeX manuscript tables match aggregate CSVs to the exact decimal point.
  5. Zero metric name collisions across different populations.
- Generate: [`results/uir_phase4b/PUBLICATION_CONSISTENCY_REPORT.md`](file:///d:/_Work/goat_bank/uir/results/uir_phase4b/PUBLICATION_CONSISTENCY_REPORT.md).
- Enforce gate: **0 blocking inconsistencies**.

---

### Component 9: Formal Specification & Terminology Modernization
Address theoretical overstatement (Issue 8), language code scoping (Issue 9), and project naming drift (Issue 10 & 15).

#### [MODIFY] [`docs/formal/UIR_SPEC.md`](file:///d:/_Work/goat_bank/uir/docs/formal/UIR_SPEC.md), [`UIR_GRAMMAR.ebnf`](file:///d:/_Work/goat_bank/uir/docs/formal/UIR_GRAMMAR.ebnf), [`UIR_SEMANTICS.md`](file:///d:/_Work/goat_bank/uir/docs/formal/UIR_SEMANTICS.md)
- Add explicit assumptions:
  - **A1**: Authoritative registry integrity.
  - **A2**: Trusted policy store integrity.
  - **A3**: Correct fact-ID binding.
  - **A4**: Output guard cannot be bypassed.
  - **A5**: Deterministic renderer uses only accepted claims.
- Reformulate theorems as **conditional safety properties**:
  *"Under assumptions A1–A5, unsupported claims are unreachable in the accepted-output transition system."*
- Label proofs accurately: Definition, Proposition, Proof sketch, Mechanically tested invariant.
- In `UIR_GRAMMAR.ebnf`, restrict normative language grammar to `ko` and `en`; designate `ja` and `zh` as reserved future extension codes.
- Canonical project name: **Universal Intermediate Representation (UIR)**.
- Canonical manuscript title: **"A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents"**.
- Replace absolute claims ("0.0% hallucination", "100% resilient") with scientifically modest formulations (e.g. *"0 observed unsupported-claim acceptances (Wilson 95% CI: [0.00%, 0.26%])"*).

#### [MODIFY] [`docs/papers/_47_UIR/_47_UIR_8p.tex`](file:///d:/_Work/goat_bank/uir/docs/papers/_47_UIR/_47_UIR_8p.tex)
- Update title, formal assumptions A1-A5, baseline fidelity labels, and sync all table numbers with `results/uir_phase4b/`.

---

### Component 10: Phase 4B Final Report & Run Manifest
Comprehensive documentation of the integrity audit.

#### [NEW] [`docs/work_reports/uir_phase4b/REPORT_PHASE4B_FINAL_EVIDENCE_INTEGRITY.md`](file:///d:/_Work/goat_bank/uir/docs/work_reports/uir_phase4b/REPORT_PHASE4B_FINAL_EVIDENCE_INTEGRITY.md)
- Complete technical report covering all 18 sections, discrepancy resolutions, and audit receipts.

#### [NEW] [`results/uir_phase4b/run_manifest_phase4b.json`](file:///d:/_Work/goat_bank/uir/results/uir_phase4b/run_manifest_phase4b.json)
- Summary manifest indexing all generated Phase 4B files.

---

## Verification Plan

### Automated Tests
1. **Benchmark Leakage Suite**:
   ```bash
   wsl.exe -d Ubuntu -- /mnt/d/_Work/goat_bank/.venv/bin/pytest /mnt/d/_Work/goat_bank/uir/evaluation/uir_phase4b/test_benchmark_leakage.py -v
   ```
2. **Phase 4B Mutation Suite**:
   ```bash
   wsl.exe -d Ubuntu -- /mnt/d/_Work/goat_bank/.venv/bin/python /mnt/d/_Work/goat_bank/uir/evaluation/uir_phase4b/mutation_fault_injection_phase4b.py
   ```
   *Verify `unsafe_acceptance_after_truncation == 0`.*
3. **Publication Consistency Checker**:
   ```bash
   wsl.exe -d Ubuntu -- /mnt/d/_Work/goat_bank/.venv/bin/python /mnt/d/_Work/goat_bank/uir/evaluation/uir_phase4b/check_publication_consistency.py
   ```
   *Verify 0 blocking inconsistencies.*
4. **Rust Core Tests (PoA-UIR)**:
   ```bash
   wsl.exe -d Ubuntu -- bash -c "source /home/sam/.cargo/env && cd /mnt/d/_Work/goat_bank/uir/crates/poa-uir && cargo test"
   ```
5. **Publication Gate Evaluation**:
   Verify all 14 gates in Section 17 of the work order evaluate to `true`.
