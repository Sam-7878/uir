# HETE UIR-ZTA V3.1 Publication Evidence Repair Implementation Plan

This plan specifies the technical execution for **HETE UIR-ZTA V3.1 Publication Evidence Repair Work Order** (`HETE_UIR_ZTA_V3_1_PUBLICATION_EVIDENCE_REPAIR_WORK_ORDER.md` and `background.md`).

The goal is to transition the research artifacts and IEEE manuscript (`_47.1_UIR_ZTA.tex`) from `V3_PREVALIDATION_ENGINEERING_EVIDENCE` to **`FINAL_PUBLICATION_EVIDENCE`**, removing all simulated/approximate claims, eliminating deterministic fallbacks, exercising active capability/resource gates end-to-end, running real 20-query adaptive mutations, executing multi-model evaluation with identical cases and dynamic denominators, and completely replacing old V2 results in the manuscript.

---

## User Review Required

> [!IMPORTANT]
> **Human Validation vs AI-Assisted Evaluator Audit**:
> The work order strictly prohibits simulated human labels (`rng.random()` with artificial disagreement). We will generate the blinded `human_review_pack.csv` (N=220). For the automated pipeline and manuscript claims, unless you provide manual human ratings for the pack, we will honestly classify this in the manuscript as **"AI-assisted evaluator audit"** and **remove all claims of "dual-blinded human expert adjudication with Cohen's $\kappa$ between experts"**. This completely eliminates scientific integrity risk.

> [!IMPORTANT]
> **Baseline Claim Accuracy (CaMeL, Progent, AgentDojo)**:
> Following Section 6 and Section 7 of the work order, CaMeL and Progent will be explicitly designated and documented as **`CaMeL-inspired capability-isolation approximation`** and **`Progent-inspired runtime sandbox approximation`** in `BASELINE_FIDELITY_REPORT.md` and the manuscript, avoiding overclaiming superiority over official implementations. AgentDojo micro-suite cases will be accurately designated as **`AgentDojo-inspired micro-suite`**.

> [!IMPORTANT]
> **Computational Scale & Zero Fallback Rule**:
> `enable_deterministic_fallback = False` is strictly enforced. Inference uses local Ollama backends (`phi3.5:latest` and `qwen2.5:7b`). To ensure high-quality execution without server timeouts, the full 850 held-out cases will be evaluated across the primary HETE and baseline pipelines, and the multi-model comparison will use an identical frozen subset of held-out cases across both Phi-3.5 and Qwen2.5 with dynamic denominators.

---

## Open Questions

None at this stage. All requirements, mathematical metrics, and architectural constraints are strictly specified in `HETE_UIR_ZTA_V3_1_PUBLICATION_EVIDENCE_REPAIR_WORK_ORDER.md`.

---

## Proposed Changes

### 1. P0: Prevalidation Archive & Preservation

#### [NEW] `results/llm_security_v3_prevalidation/`
- Archive existing `results/llm_security_v3/*` intact to preserve prevalidation evidence without overwriting.

#### [NEW] `docs/security_v3_prevalidation/`
- Archive existing `docs/security_v3/*` intact.

---

### 2. P1, P2: Opaque Runtime Identity & Field Allow-List

#### [NEW] `uir/evaluation/llm_security_v3_1/schema/runtime_case.py`
- Define `RuntimeCase` with strict field allow-list: `case_id`, `language`, `user_input`, `retrieved_context`, `principal_id`, `environment_id`, `session_metadata`.
- Strict validation: any additional fields or oracle fields (`attack_class`, `attack_goal`, `is_attack`) raise an immediate runtime error.
- Enforce opaque identifier format (e.g. `c_01J...` or UUID hex), completely removing `heldout-atk-` and `heldout-benign-` prefixes from runtime visibility.

#### [NEW] `uir/evaluation/llm_security_v3_1/schema/oracle_case.py`
- Define `OracleCase` mapping opaque `case_id` to ground truth: `original_case_id`, `attack_class`, `attack_goal`, `forbidden_output_patterns`, `target_entities`, `expected_numeric_values`, `admissible_evidence_ids`.

#### [NEW] `uir/evaluation/llm_security_v3_1/datasets/generate_opaque_datasets.py`
- Convert existing dev (1,400), validation (350), and held-out (850) datasets into opaque-identified versions:
  - `custom_heldout_v3_1.jsonl`
  - `oracle_heldout_v3_1.jsonl`
  - `custom_dev_v3_1.jsonl`, `oracle_dev_v3_1.jsonl`
  - `dataset_manifest_v3_1.json` with exact SHA-256 hashes and counts.

#### [NEW] `uir/tests/security_v3_1/test_opaque_runtime_identity.py`
- Unit tests verifying zero attack/benign label leakage in runtime cases, UUID opacity, and rejection of unauthorized fields.

---

### 3. P3: Semantic Leakage & Diversity Audit

#### [NEW] `uir/evaluation/llm_security_v3_1/audit_semantic_leakage.py`
- Compute exact duplicate rate, normalized duplicate rate, 3-gram and 5-gram Jaccard overlap, template-family overlap, attack-payload stem overlap, TF-IDF nearest-neighbor similarity across splits.
- Compute per-class case counts and distinct template counts (verifying $\ge 50$ cases and $\ge 20$ distinct templates per threat class).
- Output: `results/llm_security_v3_1/dataset_independence_audit.json`.

---

### 4. P4: Authenticated Provenance & Anti-Spoofing

#### [NEW] `uir/evaluation/llm_security_v3_1/fixtures/trusted_source_manifest.json`
- Frozen trusted source manifest with HMAC-SHA256 signatures over `authority`, `resource_id`, `content_sha256`, and `signer_id`.

#### [NEW] `uir/evaluation/llm_security_v3_1/provenance.py`
- Implement `ProvenanceVerifier` with:
  - Strict host parsing with Punycode / IDNA normalization (no substring trust).
  - Content SHA-256 verification.
  - Manifest lookup and HMAC signature authentication.
  - Tier assignment: `VERIFIED_MANIFEST`, `VERIFIED_SOURCE`, `UNVERIFIED`, `QUARANTINED`, `INTEGRITY_FAILURE`.

#### [NEW] `uir/tests/security_v3_1/test_provenance_anti_spoofing.py`
- Mandatory anti-spoofing test suite: authority substring spoof (`sec.gov.evil.com`), subdomain trick, punycode lookalike (`ѕес.gоv`), recomputed attacker hash on malicious content, invalid signer, missing signature, stale manifest, and cross-case replay.

---

### 5. P11: Attack-Specific Behavioral Judges

#### [NEW] `uir/evaluation/llm_security_v3_1/judges/`
- `base_judge.py`: Base abstract judge interface returning `(mcr: bool, e2e_asr: bool, reason: str)`.
- `direct_jailbreak_judge.py`: Evaluates policy override, refusal erosion, and intent shift.
- `indirect_injection_judge.py`: Evaluates untrusted context instruction hijack vs trusted system effect.
- `poisoning_judge.py`: Evaluates whether falsified retrieval evidence was accepted into UIR and altered accepted facts.
- `sensitive_exfiltration_judge.py`: Evaluates private context secret leakage (synthetic secret seeded in protected context, not user prompt).
- `excessive_agency_judge.py`: Evaluates unauthorized action proposals vs unauthorized mock tool executions.
- `resource_exhaustion_judge.py`: Evaluates actual token counts, tool calls, recursion depth, and budget-exceeded terminal status.
- `nonexistent_entity_judge.py`: Verifies accepted claims against authoritative entity registry.

---

### 6. P12: End-to-End CapabilityGate and ResourceGuard Execution

#### [NEW] `uir/evaluation/llm_security_v3_1/baselines/uir_v3_1_security.py`
- Implement `UirV31SecurityPipeline` with full zero-trust enforcement:
  - **CapabilityGate**: Actually intercept and evaluate tool proposals against capability tokens and principal policies before mock execution.
  - **ResourceGuard**: Actually accumulate token counts, tool call invocations, and recursion depth against `ResourceBudget`; terminate with `BLOCKED_RESOURCE_EXHAUSTED` when budget is exceeded.
  - **InputGuard & Frontend**: Normalization, taint assignment, structured draft routing.
  - **EvidenceResolver & Authenticated Provenance**: Context firewall quarantine of instruction-bearing evidence.
  - **PolicyEngine**: Deterministic policy decision point.
  - **OutputGuard**: Schema revalidation and citation integrity checking.

#### [NEW] `uir/tests/security_v3_1/test_capability_and_resource_gates.py`
- Invariant tests verifying:
  - $I_1$: Unauthorized proposal does not cause unauthorized execution.
  - $I_4$: Resource budget cannot be expanded by model output.

---

### 7. P5, P6: Baseline Adapters & Fidelity Report

#### [NEW] `uir/evaluation/llm_security_v3_1/baselines/`
- `spotlighting_adapter.py`: Implements paper-faithful Spotlighting (Hines et al. 2024) with delimiter and structure transformations.
- `camel_adapter.py`: `CaMeL-inspired capability-isolation approximation` using dual-channel separation.
- `progent_adapter.py`: `Progent-inspired runtime sandbox approximation`.
- `naive_rag.py`, `vanilla_slm.py`, `prompt_guardrail.py`: Standard comparison baselines.

#### [NEW] `uir/docs/security_v3_1/BASELINE_FIDELITY_REPORT.md`
- Complete fidelity report detailing reference papers, implemented mechanisms, omitted mechanisms, and direct comparison validity.

---

### 8. P7: Real Adaptive Attack Search Engine

#### [NEW] `uir/evaluation/llm_security_v3_1/adaptive_attacks/mutation_engine.py`
- Implement real mutation transformations: paraphrase, role-play framing, instruction splitting, zero-width/Unicode injection, nested structured data smuggling, tool-output injection, RAG document injection, code switching, semantic synonym substitution, provenance spoof attempts, capability-escalation phrasing.

#### [NEW] `uir/evaluation/llm_security_v3_1/adaptive_attacks/search_runner.py`
- Search engine with up to 20 query iterations per seed case across 6 threat campaigns under A0 (black-box), A1 (gray-box), and A2 (white-box) attacker models.
- Track query-by-query mutations, guard traces, first MCR, first E2E bypass, containment gate, time-to-first-bypass, queries-to-first-bypass.
- Generates MCR vs query budget curve and E2E-ASR vs query budget curve.

---

### 9. P8, P9, P10, P13, P14, P15: Campaign Runner & Analysis

#### [NEW] `uir/evaluation/llm_security_v3_1/run_publication_campaign.py`
- Main campaign runner:
  - `enable_deterministic_fallback = False` strictly enforced on `OllamaClient`.
  - Full raw run capture: saves per-case JSON records for every execution under `results/llm_security_v3_1/raw_runs/`.
  - Multi-model execution: evaluates Phi-3.5 and Qwen2.5 on identical cases with dynamic denominators.
  - Stochastic robustness: temperature=0.7, top_p=0.9 across 5 seeds.
  - Real utility scoring: exact expected numeric/target entity match + JSON contract schema validation.
  - Exact statistics: `scipy.stats.binomtest` for exact paired McNemar test, Wilson 95% CIs, Holm-Bonferroni correction.
  - Containment funnel: recomputed directly from raw per-case records.

---

### 10. P17: Strict Publication Validator

#### [NEW] `uir/evaluation/llm_security_v3_1/validate_publication_results.py`
- Derive `publication_eligible` strictly by inspecting raw execution records:
  - 100% case count match against manifest.
  - Same case set across compared systems and models.
  - Zero deterministic fallback records.
  - Non-identical adaptive mutations reaching query budget 20.
  - CapabilityGate and ResourceGuard actually exercised.
  - Exact statistics verified.
  - Fails loudly with list of failures if any condition is not satisfied.

---

### 11. P19, P20: Manuscript Overhaul & Final Report

#### [MODIFY] `uir/docs/papers/_47_1_UIR_for_ZTA/references.bib`
- Fix citation keys:
  - Add `hofer2026automated`
  - Add `westfall2010multiple`
  - Ensure keys match LaTeX: `debenedetti2025camel`, `progent2024`, `wallace2024instructionhierarchy`, `zou2025poisonedrag`.

#### [MODIFY] `uir/docs/papers/_47_1_UIR_for_ZTA/_47.1_UIR_ZTA.tex`
- Replace Section VI (Results) and Section VII (Discussion) entirely:
  - Remove all stale V2 numbers (320 held-out, 280 attacks, 0/280).
  - Insert V3.1 frozen results: baseline comparison, per-class breakdown (600 attacks, 250 benign), adaptive attack budget curves, multi-model Phi/Qwen comparison, stochastic 5-seed robustness, containment funnel.
  - Synchronize dataset sizes directly from frozen manifest (1,400 dev, 350 validation, 850 held-out).
  - Update Appendix and Bibliography order (`\appendices` followed by bibliography).
  - Verify clean compilation with `pdflatex` + `bibtex` + `pdflatex` + `pdflatex` (0 undefined citations).

#### [NEW] `uir/docs/security_v3_1/HETE_UIR_V3_1_FINAL_REPORT.md`
- Final programmatic summary report answering all 20 questions in Section 21 of the work order.

#### [NEW] `uir/docs/security_v3_1/README_REPRODUCE.md`
- Full reproducibility instructions with commands, environment setup, and verification checks.

---

## Verification Plan

### Automated Tests
1. **Opaque Identity & Allow-List**:
   ```bash
   wsl.exe -d Ubuntu env PYTHONPATH=/mnt/d/_Work/goat_bank/uir /mnt/d/_Work/goat_bank/.venv/bin/pytest uir/tests/security_v3_1/test_opaque_runtime_identity.py -v
   ```
2. **Provenance Anti-Spoofing**:
   ```bash
   wsl.exe -d Ubuntu env PYTHONPATH=/mnt/d/_Work/goat_bank/uir /mnt/d/_Work/goat_bank/.venv/bin/pytest uir/tests/security_v3_1/test_provenance_anti_spoofing.py -v
   ```
3. **Capability & Resource Gates**:
   ```bash
   wsl.exe -d Ubuntu env PYTHONPATH=/mnt/d/_Work/goat_bank/uir /mnt/d/_Work/goat_bank/.venv/bin/pytest uir/tests/security_v3_1/test_capability_and_resource_gates.py -v
   ```
4. **Dataset Leakage & Diversity Audit**:
   ```bash
   wsl.exe -d Ubuntu env PYTHONPATH=/mnt/d/_Work/goat_bank/uir /mnt/d/_Work/goat_bank/.venv/bin/python -m evaluation.llm_security_v3_1.audit_semantic_leakage
   ```
5. **Full Publication Campaign Execution**:
   ```bash
   wsl.exe -d Ubuntu env PYTHONPATH=/mnt/d/_Work/goat_bank/uir /mnt/d/_Work/goat_bank/.venv/bin/python -m evaluation.llm_security_v3_1.run_publication_campaign
   ```
6. **Strict Publication Validation**:
   ```bash
   wsl.exe -d Ubuntu env PYTHONPATH=/mnt/d/_Work/goat_bank/uir /mnt/d/_Work/goat_bank/.venv/bin/python -m evaluation.llm_security_v3_1.validate_publication_results --strict
   ```
7. **Manuscript Clean Compilation**:
   ```bash
   wsl.exe -d Ubuntu bash -c "cd /mnt/d/_Work/goat_bank/uir/docs/papers/_47_1_UIR_for_ZTA && pdflatex -interaction=nonstopmode _47.1_UIR_ZTA.tex && bibtex _47.1_UIR_ZTA && pdflatex -interaction=nonstopmode _47.1_UIR_ZTA.tex && pdflatex -interaction=nonstopmode _47.1_UIR_ZTA.tex"
   ```

### Manual Verification
- Verify that `publication_validation.json` outputs `"publication_eligible": true` and `"failures": []`.
- Inspect compiled PDF `_47.1_UIR_ZTA.pdf` to ensure zero broken citations `[?]`, correct appendix layout, and consistent V3.1 empirical tables.
