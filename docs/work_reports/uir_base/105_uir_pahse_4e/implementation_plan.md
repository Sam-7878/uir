# Phase UIR-4E Implementation Plan
## Final Publication Reconciliation, Metric Repair & Missing Generalization Evidence

### Objective
Phase 4E is a **reconciliation phase only** — no new UIR architecture. The goal is to produce a fully consistent, publication-ready evidence package by resolving all 9 publication blockers found in the Phase 4D archive.

---

## Key Findings from Phase 4D Archive Analysis

From direct inspection of `strong_baseline_summary_actual.csv` (the canonical raw source):

| Pipeline | Raw Unsupported Accept | Raw Attack Success | Phase 4D Report |
| :--- | :---: | :---: | :--- |
| C0 | 35.83% | 66% | ❌ Different values in MD reports |
| C1 | 49.33% | 92% | ❌ Different values in MD reports |
| C2 | 33.17% | 84% | ✅ Matches |
| C3 | 27.33% | 50% | ❌ Different values in MD reports |
| C4 | 23.83% | 0% | ❌ Different values in MD reports |
| C5 | 0.00% | 0% | ❌ Different values in MD reports |
| C6 | 11.00% | 0% | ❌ Different values in MD reports |
| C7 | 78.00% | 90% | ❌ Different values in MD reports |
| C8 | 0.00% | 0% | ✅ Matches |

**C8 Metric Disambiguation (418 COMMIT-eligible cases):**
- `complete_claim_set_accuracy` = 224/418 = **53.59%**
- `supported_answer_coverage` = 272/418 = **65.07%** (complete + partial)
- `no_verified_answer_rate` = 146/418 = **34.93%**

> The +11.96% "task completion superiority" was a mislabeled comparison (C1 complete vs C8 supported coverage). The correct complete accuracy comparison is **+0.48pp** with McNemar p=0.5 (non-significant).

**Qwen N issue:** `stat_generalization_actual.csv` shows Qwen FinQA N=10, Qwen HaluEval N=10 — not N=200.

---

## Blocker Resolution Plan

### BLOCKER 1 → Rescore from canonical raw
Create `rescore_internal_final.py` that reads `per_case_evidence_actual.jsonl` and re-derives all metrics with the corrected metric contract.

### BLOCKER 2 & 3 → Metric contract fix
Separate `task_completion` into:
- `complete_claim_set_accuracy` (primary utility endpoint)
- `supported_answer_coverage` (secondary)
- `safe_partial_answer_rate`
- `no_verified_answer_rate`

### BLOCKER 4 → Precision/recall denominators
Report macro (over all COMMIT cases) and conditional (over emitted-answer cases) separately.

### BLOCKERS 5 & 6 → Qwen N=200 replication
Run full Qwen2.5-7B via Ollama on 200 FinQA + 200 HaluEval cases with complete per-case raw capture (JSONL).

### BLOCKERS 7 & 8 → Constrained decoding baseline
Run `lm-format-enforcer` (or equivalent) as `D1_EXTERNAL_CONSTRAINED_DECODING`. Rename C3 to "JSON-schema prompted/post-hoc validation baseline" in all prose.

### BLOCKER 9 → Overclaim lint
Create `lint_scientific_claims.py` to detect and flag overreach language.

---

## Proposed Changes

### New Directory Structure

```text
uir/results/uir_phase4e/
uir/evaluation/uir_phase4e/
uir/docs/work_reports/uir_phase4e/
```

---

### A. Core Rescoring & Metric Contract

#### [NEW] `evaluation/uir_phase4e/METRIC_CONTRACT_FINAL.yaml`
Formal YAML defining all 8 final metric names with explicit denominators.

#### [NEW] `evaluation/uir_phase4e/rescore_internal_final.py`
Reads `results/uir_phase4d/per_case_evidence_actual.jsonl` (immutable). Outputs:
- `results/uir_phase4e/per_case_scored_final.jsonl`
- `results/uir_phase4e/strong_baseline_summary_final.csv`
- `results/uir_phase4e/stat_safety_final.csv`
- `results/uir_phase4e/stat_complete_utility_final.csv`
- `results/uir_phase4e/stat_partial_utility_final.csv`
- `results/uir_phase4e/latency_summary_final.csv`

#### [NEW] `results/uir_phase4e/AUTHORITATIVE_EVIDENCE_MAP.yaml`
6-level hierarchy from raw JSONL → manuscript tables.

---

### B. Qwen N=200 Full External Replication

#### [NEW] `evaluation/uir_phase4e/run_qwen_external_full.py`
- Runs Qwen2.5-7B on 200 frozen FinQA + 200 frozen HaluEval cases
- Uses existing frozen inputs from `results/uir_phase4d/frozen_inputs/`
- Saves complete per-case captures with prompt hashes, response hashes, latency
- Outputs:
  - `results/uir_phase4e/qwen_finqa_C1_raw.jsonl`
  - `results/uir_phase4e/qwen_finqa_C8_raw.jsonl`
  - `results/uir_phase4e/qwen_halueval_C1_raw.jsonl`
  - `results/uir_phase4e/qwen_halueval_C8_raw.jsonl`
  - `results/uir_phase4e/external_generalization_final.csv`
  - `results/uir_phase4e/external_failure_taxonomy_final.csv`

---

### C. Genuine Constrained Decoding Baseline

#### [NEW] `evaluation/uir_phase4e/run_constrained_decoding.py`
- Installs and uses `lm-format-enforcer` with Phi-3.5 logits processor
- Runs on same 600 internal cases
- Reports schema validity, safety, complete/partial utility, latency
- Output: `results/uir_phase4e/external_constrained_decoding_summary.csv`

---

### D. Automated Publication Toolchain

#### [NEW] `evaluation/uir_phase4e/generate_publication_tables.py`
- Reads aggregate CSVs only — no hand-entered numbers
- Generates `docs/work_reports/uir_phase4e/generated_tables.md`
- Generates `docs/work_reports/uir_phase4e/generated_tables.tex`

#### [NEW] `evaluation/uir_phase4e/check_final_publication_consistency.py`
- Compares per-case JSONL → CSVs → tables → manuscript
- Fails on metric mislabels, N mismatches, Qwen N<200 claim, C3 terminology errors

#### [NEW] `evaluation/uir_phase4e/lint_scientific_claims.py`
- Flags overclaim phrases (universal safety, hallucination eliminated, etc.)
- Required: 0 unflagged overclaims

---

### E. Final Manuscript Updates (`_47_UIR_8p.tex`)

1. **Section IV Table I** — Rebuild with corrected raw numbers (C0 35.83%, C1 49.33%, etc.)
2. **Section IV** — Split utility table to show `complete_claim_set_accuracy` vs `supported_answer_coverage` vs `no_verified_answer_rate`
3. **Section IV** — C8 vs C1: state non-significant complete-accuracy result (+0.48pp, p=0.5) honestly
4. **Section IV Table IV** — Rebuild cross-model table with Qwen N=200 (not N=10)
5. **C3 terminology** — Rename to "JSON-schema prompted/post-hoc validation" throughout
6. **Section V** — Update discussion to reflect correct scientific narrative:
   - UIR reallocates failures (fabrication → safe partial/abstention) rather than universally boosting accuracy
   - Central claim: system-level verifiability ≠ model-level reasoning ability
7. **Overclaims** — Remove "universal hallucination elimination", scope all claims to assumptions A1–A5

---

### F. Final Reports

#### [NEW] `results/uir_phase4e/FINAL_PUBLICATION_CONSISTENCY.md`
- Automated comparison of all artifacts

#### [NEW] `results/uir_phase4e/PHASE4E_FINAL_MANIFEST.json`
- SHA-256 of all final artifacts

#### [NEW] `docs/work_reports/uir_phase4e/REPORT_PHASE4E_FINAL_PUBLICATION_FREEZE.md`
- Complete narrative of all corrections and final state

---

## Open Questions

> [!IMPORTANT]
> **Qwen N=200 requires Ollama to be running.** The work order recommends Option A (full N=200). This will take ~30-60 minutes. Should I proceed with Option A or use Option B (keep N=10 pilot, remove strong cross-model claims)?

> [!IMPORTANT]
> **lm-format-enforcer baseline** requires installing the `lm-format-enforcer` package and running Phi-3.5 inference on 600 cases (additional ~2-3 hours). The work order recommends Option A. Should I proceed or use Option B (rename C3, remove constrained decoding claims)?

> [!NOTE]
> Based on the background.md, the author suggests that even without Option A for either item, the paper can be made stronger by framing the central result as:
> *"UIR separates probabilistic generation from deterministic evidence authority, reallocating fabricated outputs into verified, safe-partial, or abstained responses."*

---

## Execution Order

1. Create directory structure & `METRIC_CONTRACT_FINAL.yaml`
2. Write & run `rescore_internal_final.py` → corrected CSVs
3. Recompute statistics with corrected endpoints
4. (If approved) Run Qwen N=200 full replication
5. (If approved) Run constrained decoding baseline
6. Generate publication tables automatically
7. Run consistency checker and overclaim lint
8. Update `_47_UIR_8p.tex` manuscript
9. Generate `PHASE4E_FINAL_MANIFEST.json`
10. Write `REPORT_PHASE4E_FINAL_PUBLICATION_FREEZE.md`

## Verification Plan

- `check_final_publication_consistency.py` → 0 blockers, 0 warnings
- `lint_scientific_claims.py` → 0 unflagged overclaims
- Phase 4D immutability: `results/uir_phase4d/` unchanged
- Gate status: `READY_FOR_MANUSCRIPT_DRAFT_FINAL`
