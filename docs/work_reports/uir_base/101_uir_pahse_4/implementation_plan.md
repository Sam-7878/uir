# Implementation Plan — Phase UIR-4: Journal Strengthening of `_47_UIR`

Strengthen the academic rigor, empirical baselines, formal specification, and manuscript framing of the `_47_UIR` paper (Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents) based on AI reviewer evaluations (Grok 4.6, Claude 5, EXAONE 2) and the work instructions in `uir/docs/work_reports/101_uir_pahse_4/CODEX_UIR_PHASE4_JOURNAL_STRENGTHENING_INSTRUCTIONS.md`.

---

## User Review Required

> [!IMPORTANT]
> **WSL2 Ubuntu 24.04 & Python `.venv` Environment Active:**
> - Python 3.12.13 in `/mnt/d/_Work/goat_bank/.venv` with PyTorch 2.5.1 + CUDA (RTX 4070 Laptop GPU, 8GB VRAM) verified.
> - `microsoft/Phi-3.5-mini-instruct` loaded via `BitsAndBytesConfig` NF4 4-bit quantization directly from HuggingFace local cache (`/home/sam/.cache/huggingface/hub/...`).
> - Rust 1.96.0 verified (`cargo check` passes cleanly on `poa-uir`).

> [!IMPORTANT]
> **Preservation of Phase-3D Evidence:**
> - `results/uir_phase3b/` and `results/uir_phase3d/` will remain completely frozen and unmodified.
> - All new execution outputs, metrics, and manifests will be generated under `results/uir_phase4/`.

> [!IMPORTANT]
> **Manuscript Retraction of Legacy Claims in `_47_UIR_8p.tex`:**
> - Complete removal of GATv2 causal-attention claims ($\alpha = 0.7894$, "78.94% root-cause impact", "mathematical causality").
> - Elimination of "0.0% hallucination / 100.0% fact-consistency" hyperbole; replaced with honest, bounded claims ("0 observed unsupported-claim acceptance on $N$ evaluated cases" with Wilson 95% CI).
> - Deletion of ungrounded defense/C4ISR speculation.
> - Insertion of strong baseline comparisons (C0--C8), formal grammar & semantics, and external benchmark results.

---

## Proposed Changes

### 1. Formal Specification Component (`uir/docs/formal/`)

#### [NEW] [UIR_SPEC.md](file:///d:/_Work/goat_bank/uir/docs/formal/UIR_SPEC.md)
- Architectural specification of UIR as a Security Reference Representation (SRR).
- Request lifecycle, components, and formal invariants (INV-1 through INV-5).

#### [NEW] [UIR_GRAMMAR.ebnf](file:///d:/_Work/goat_bank/uir/docs/formal/UIR_GRAMMAR.ebnf)
- Formal EBNF grammar covering request structure, semantic intent, targets, parameters, typed condition AST, policy levels (L0--L3), enforcement actions, execution contracts, and output schemas.

#### [NEW] [UIR_SEMANTICS.md](file:///d:/_Work/goat_bank/uir/docs/formal/UIR_SEMANTICS.md)
- Operational semantics: Judgment rules `<UIR, Policy, Context> ⇓ Decision` (`Allow`, `Reject`, `Quarantine`, `NeedsClarification`).
- Type system for Condition AST: typing judgments for relational (`EQ`, `NE`, `GT`, `GE`, `LT`, `LE`), logical (`AND`, `OR`, `NOT`), and exceptional (`EXCEPT`) operators.
- Inductive invariants and proof sketches for Fail-Closed Execution (INV-1), Verified-Claim Acceptance (INV-2), and Numeric Binding (INV-3).

---

### 2. Core Rust & Python Testing Enhancements (`uir/crates/poa-uir/`, `uir/evaluation/`)

#### [MODIFY] [condition.rs](file:///d:/_Work/goat_bank/uir/crates/poa-uir/src/condition.rs)
- Expand `Condition` operators to include `Ne`, `Ge`, `Le` alongside `Eq`, `Gt`, `Lt`, `Not`, `And`, `Or`, `Except`.
- Implement static type validation rules ensuring typed compatibility before evaluation.

#### [NEW] [formal_invariants_test.rs](file:///d:/_Work/goat_bank/uir/crates/poa-uir/tests/formal_invariants_test.rs)
- Property-based testing using `proptest`:
  1. Semantic digest unchanged by excluded metadata.
  2. Reject/Quarantine never reaches executor.
  3. Numeric binding never mutates authoritative value.
  4. Round-trip serialization invariance.
  5. Policy precedence determinism.

#### [NEW] [mutation_fault_injection.py](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4/mutation_fault_injection.py)
- Fault injection test harness simulating 5 critical mutation bypasses:
  - Policy bypass injection
  - Entity validation skip
  - Corrupted provenance
  - Altered numeric fact
  - Truncated structured output
- Generates `results/uir_phase4/formal_invariant_test_report.csv` and `results/uir_phase4/mutation_test_report.csv`.

---

### 3. Strong Baseline Suite (`uir/evaluation/uir_phase4/baselines_phase4.py`)

#### [NEW] [baselines_phase4.py](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4/baselines_phase4.py)
Implements all required baselines with matched local Phi-3.5 SLM backbone:
- **C0 (Direct SLM)**: Prompt only, unconstrained generation.
- **C1 (Naive RAG)**: Standard dense/BM25 retrieval without verification.
- **C2 (RAG + Entity/Existence Validation Tool)**: Critical adversarial baseline. Queries authoritative entity registry; if absent, emits fail-closed rejection. Evaluates whether simple existence checking matches UIR.
- **C3 (JSON-Schema Constrained Output)**: Structured-generation constrained decoding.
- **C4 (Tool/Function-Calling Agent)**: Agent with authoritative tools (`lookup_entity`, `get_verified_metric`).
- **C5 (Guardrail Pipeline)**: NeMo-style dual input/output safety rails.
- **C6/C7 (GraphRAG / Structured Knowledge Retrieval)**: Graph-structured retrieval integrating `dlg_gnn/graphrag`.
- **C8 (Final UIR B6 Pipeline)**: Full UIR compilation, deterministic policy engine, verified fact binding, and output filtering.

---

### 4. External Public Benchmark Adapters & Datasets (`uir/evaluation/uir_phase4/external_benchmarks/`)

#### [NEW] [financial_adapter.py](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4/external_benchmarks/financial_adapter.py)
- FinQA / TAT-QA adapter executing financial numerical queries, evidence extraction, and exact numeric preservation checks.

#### [NEW] [groundedness_adapter.py](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4/external_benchmarks/groundedness_adapter.py)
- HaluEval / RAGTruth adapter evaluating unsupported claim detection, hallucination vs refusal, and claim consistency.

#### [NEW] [run_external_benchmarks.py](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4/run_external_benchmarks.py)
- Evaluates C2, C4, and C8 on external benchmarks.
- Produces `external_finance_results.csv`, `external_groundedness_results.csv`, and `external_benchmark_manifest.json` with full SHA-256 hashes and license manifests.

---

### 5. Frontend Robustness & Condition Semantics Campaign (`uir/evaluation/uir_phase4/`)

#### [NEW] [build_robustness_v1.py](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4/build_robustness_v1.py)
- Generates `ROBUSTNESS-v1`: 1,000 cases (400 KO, 400 EN, 200 code-mixed).
- Includes paraphrases (5 variants per seed), word-order shifts, Korean particles (`은/는`, `이/가`, `을/를`), spacing perturbations, honorifics, prepositions, negations, double negations, unless/except clauses, nested conditions, code-switching, and OOD requests.
- Freezes dataset split before running evaluation.

#### [NEW] [run_robustness_campaign.py](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4/run_robustness_campaign.py)
- Evaluates parser robustness and outputs `results/uir_phase4/frontend_robustness_summary.csv`.

#### [NEW] [run_condition_investigation.py](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4/run_condition_investigation.py)
- 300 condition-heavy cases spanning AND/OR, NOT, unless, except, nested conditions, scope ambiguity, coordination, temporal, mixed-language, and implicit conditions.
- Compares surface text, condition AST, normalized AST, and parenthesized DSL.
- Produces `results/uir_phase4/condition_semantics_summary.csv`.

---

### 6. Campaign Execution, Metrics & Statistical Analysis (`uir/evaluation/uir_phase4/`)

#### [NEW] [run_phase4_campaign.py](file:///d:/_Work/goat_bank/uir/evaluation/uir_phase4/run_phase4_campaign.py)
- End-to-end runner orchestrating C0--C8 evaluation over the frozen benchmarks.
- Collects latency (P50, P95, P99), TTFT, input/output tokens, VRAM, and tokens/sec split by query category (valid, reject, adversarial).
- Computes McNemar test with 95% Wilson CIs, Wilcoxon signed-rank tests for latency, paired bootstrap CIs for utility, and Holm-Bonferroni corrections.
- Generates all required deliverable CSVs and JSON manifests in `results/uir_phase4/`.

---

### 7. Phase-4 Work Report (`uir/docs/work_reports/uir_phase4/`)

#### [NEW] [REPORT_PHASE4_JOURNAL_STRENGTHENING.md](file:///d:/_Work/goat_bank/uir/docs/work_reports/uir_phase4/REPORT_PHASE4_JOURNAL_STRENGTHENING.md)
- Follows the 18-section format required by Section 17 of the CODEX work order:
  1. Evidence preservation
  2. Reviewer motivation
  3. Strong baseline definitions
  4. External benchmark integrity
  5. Formal UIR specification
  6. Invariant & property testing
  7. Multilingual frontend robustness
  8. Condition-semantics analysis
  9. Strong baseline results
  10. External financial results
  11. External groundedness results
  12. Safety-utility trade-off
  13. Runtime/resource fairness
  14. Statistical significance
  15. Cross-backbone discussion
  16. Reproducibility package
  17. Remaining limitations
  18. Manuscript-readiness verdict

---

### 8. Manuscript Overhaul (`uir/docs/papers/_47_UIR/_47_UIR_8p.tex`)

#### [MODIFY] [_47_UIR_8p.tex](file:///d:/_Work/goat_bank/uir/docs/papers/_47_UIR/_47_UIR_8p.tex)
- Title: Update to *"A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents"* (or approved journal title).
- Abstract: Remove "0.0% hallucination rate" and GATv2 attention claims. State bounded claims with Wilson CIs, strong baseline comparisons (C0--C8), and formal invariant verification.
- Introduction & Related Work: Cite 2024–2026 constrained decoding (Outlines, Guidance), guardrails (NeMo), tool-calling agents, and advanced RAG (Self-RAG, GraphRAG).
- Architecture: Replace GATv2 module with the Verified Grounding & Policy Evaluation Engine; embed formal condition grammar and operational semantics.
- Experimental Evaluation: Update tables with C0--C8 results, external benchmarks (FinQA, HaluEval), robustness (ROBUSTNESS-v1), condition diagnostic findings, and Holm-corrected p-values.
- Discussion & Conclusion: Remove defense speculation; document condition semantics ambiguity and future work.

---

## Verification Plan

### Automated Tests
1. **Rust Cargo Check & Test**:
   ```bash
   wsl.exe -d Ubuntu -- env PATH=/home/sam/.cargo/bin:/usr/local/bin:/usr/bin:/bin cargo test --manifest-path /mnt/d/_Work/goat_bank/uir/Cargo.toml
   ```
2. **Formal Invariant & Mutation Verification**:
   ```bash
   wsl.exe -d Ubuntu -- /mnt/d/_Work/goat_bank/.venv/bin/python /mnt/d/_Work/goat_bank/uir/evaluation/uir_phase4/mutation_fault_injection.py
   ```
3. **Phase-4 Campaign Smoke & Full Execution**:
   ```bash
   wsl.exe -d Ubuntu -- /mnt/d/_Work/goat_bank/.venv/bin/python /mnt/d/_Work/goat_bank/uir/evaluation/uir_phase4/run_phase4_campaign.py --smoke
   wsl.exe -d Ubuntu -- /mnt/d/_Work/goat_bank/.venv/bin/python /mnt/d/_Work/goat_bank/uir/evaluation/uir_phase4/run_phase4_campaign.py
   ```
4. **LaTeX Compilation Check**:
   ```bash
   wsl.exe -d Ubuntu -- pdflatex -interaction=nonstopmode /mnt/d/_Work/goat_bank/uir/docs/papers/_47_UIR/_47_UIR_8p.tex
   ```

### Manual Verification
- Review generated reports and CSVs in `results/uir_phase4/` to ensure all 18 files from Section 16 of the work order are populated with authentic, non-fabricated metrics.
- Verify that `_47_UIR_8p.tex` compiles cleanly with no legacy GATv2/78.94% strings remaining.
