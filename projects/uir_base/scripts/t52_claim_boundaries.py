#!/usr/bin/env python3
"""
Stage 119: T52 Scientific Claim Tightening and Proof-vs-Test Separation
"""
import csv
from pathlib import Path

def main():
    base_dir = Path("/mnt/d/_Work/goat_bank/uir/projects/uir_base")
    s119_results = base_dir / "results" / "119_electronics_final_submission_2026_10_23"
    claim_dir = s119_results / "claim_audit"
    claim_dir.mkdir(parents=True, exist_ok=True)

    # 1. line_claim_support_119.csv
    rows = [
        {
            "section": "Abstract",
            "prose_claim": "Python 3.14 and Rust 1.99 interpreters achieved 100.0% (480/480) mutual state and fact-level conformance",
            "evidence_category": "Observed Sample Outcome",
            "underlying_evidence": "primary_raw.jsonl: 480 paired records, 240 cases, 0 mismatches",
            "boundary_qualification": "Applies to frozen 60 sampled owner clusters (240 test cases); both interpreters implemented by same research group from shared spec"
        },
        {
            "section": "Abstract",
            "prose_claim": "hypergeometric test rejects null K >= 5 (p=0.000965), bounding frame failure to <= 2/82 at 95% confidence",
            "evidence_category": "Design-Based Survey Sampling Inference",
            "underlying_evidence": "Hypergeometric tail formula comb(77, 60)/comb(82, 60) = 0.0009651338",
            "boundary_qualification": "Inference strictly bounded to M=82 convenience frame; not generalizable to all open-source packages"
        },
        {
            "section": "Abstract",
            "prose_claim": "SLM selector achieved 0/120 exact match on authorized queries due to distractor over-selection",
            "evidence_category": "Observed Sample Outcome",
            "underlying_evidence": "secondary_raw.jsonl: 120 ALLOW cases with Phi-3.5-mini selector, all selected supersets containing distractors",
            "boundary_qualification": "Component-level limitation of Phi-3.5-mini on closed fact selection; Macro F1=0.5159, Recall=1.0000, Precision=0.3529"
        },
        {
            "section": "Abstract",
            "prose_claim": "deterministic evidence guard recovered 100.0% (120/120) complete displays under template rendering",
            "evidence_category": "Mathematical Set-Intersection Consequence",
            "underlying_evidence": "F_acc = F_prop cap F_auth cap F_req; full recall guarantees F_req subset of F_prop, allowing guard to filter distractors",
            "boundary_qualification": "Recovery occurs because selector preserved 100% recall; guard CANNOT recover facts omitted by the model"
        },
        {
            "section": "Abstract",
            "prose_claim": "generative rendering incurred a 36.67% (44/120) utility omission penalty without safety gain",
            "evidence_category": "Observed Sample Outcome",
            "underlying_evidence": "secondary_raw.jsonl: 44 cases with generative SLM renderer produced incomplete or unparseable outputs",
            "boundary_qualification": "Evaluated on Phi-3.5-mini generative decoder on CLOSED_FACT_LINES_S1 format"
        },
        {
            "section": "Abstract",
            "prose_claim": "equivalent specialized contracts produced identical outcomes, confirming safety stems from deterministic boundary",
            "evidence_category": "Empirical Equivalence Observation",
            "underlying_evidence": "secondary_raw.jsonl: Delta between UIR and specialized representation is exactly 0 across all 1920 cells",
            "boundary_qualification": "Shows representation neutrality; neither UIR nor specialized contract has intrinsic safety superiority"
        },
        {
            "section": "Section 5.2 / Threats",
            "prose_claim": "DENY cases evaluated with model calls",
            "evidence_category": "Counterfactual Stress Testing",
            "underlying_evidence": "model_capture_reuse_118.csv: 240 DENY prompts evaluated on Phi-3.5-mini",
            "boundary_qualification": "Diagnostic stress test of guard interception; in optimized production, pre-inference authority short-circuits compute"
        }
    ]

    with open(claim_dir / "line_claim_support_119.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["section", "prose_claim", "evidence_category", "underlying_evidence", "boundary_qualification"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print("Wrote line_claim_support_119.csv")

    # 2. forbidden_extrapolations_119.md
    forbidden_md = """# Stage 119 Forbidden Extrapolations and Bounded Language Policy

**Date:** 2026-10-23  
**Auditor:** Stage 119 Scientific Rigor & Governance Engine  
**Status:** **ACTIVE CONSTRAINTS FOR REVISED MANUSCRIPT**

---

## 1. Strictly Prohibited Statements & Mandatory Replacements

| Prohibited Phrase / Assertion | Flaw / Risk | Mandatory Scoped Replacement |
| :--- | :--- | :--- |
| *"formally validates strict behavioral safety for electronic and cyber-physical systems"* | Over-generalization beyond measured software manifest boundary. | *"empirically evaluates runtime conformance and deterministic output boundaries for generative software components"* |
| *"achieves verifiable semantic correctness"* | Implies whole-system formal program correctness theorem. | *"enforces verifiable adherence to structured intermediate contracts"* |
| *"formally proves that generative AI is dependable"* | Conflates empirical finite sampling with deductive mathematical proof. | *"establishes bounded statistical confidence over a sampled convenience frame"* |
| *"guarantees dependability on edge devices"* | Unmeasured hardware metric; no physical edge testing was conducted. | *"demonstrates that deterministic guard boundaries can filter model proposals in software architectures"* |
| *"first study to solve LLM hallucination"* | Unsupported novelty hype; hallucination in unconstrained prose is NOT solved. | *"evaluates typed intermediate contracts for closed-format evidence grounding"* |
| *"independent implementation teams"* | Python and Rust interpreters were implemented by the same research group from a shared spec. | *"two independently executable interpreters in Python and Rust developed by the same research group from a common formal specification"* |
| *"guard recovers missing facts"* | The guard only filters; it cannot hallucinate or recover facts omitted by the SLM. | *"deterministic guard recovers full utility because the SLM achieved 100% recall, enabling set-intersection filtering of extraneous distractors"* |
| *"reduced compute on DENY cases"* | In the factorial experiment, DENY cases actually invoked the model to test guard interception. | *"in production systems, pre-inference policies can short-circuit compute, whereas in our factorial study, DENY cases served as counterfactual stress tests"* |

---

## 2. Epistemic Categories

All statements in the manuscript must adhere to one of four epistemological categories:
1. **Deductive Mathematical Consequence:** $\mathcal{F}_{\text{acc}} = \mathcal{F}_{\text{prop}} \cap \mathcal{F}_{\text{auth}} \cap \mathcal{F}_{\text{req}}$ deterministically purges unauthorized or extraneous facts.
2. **Observed Sample Outcome:** 480/480 records matched between Python and Rust; 0/120 exact raw match by SLM; 120/120 recovery under template rendering.
3. **Finite-Population Statistical Inference:** Hypergeometric test ($p=0.000965$, $K \le 2$) applies strictly to the defined convenience frame of $M=82$ open-source manifest clusters.
4. **Explicitly Unmeasured Endpoints (`NOT_MEASURED`):** Unconstrained conversational prose, FinQA accuracy, energy consumption, execution latency, FPGA acceleration, and multi-domain generalization.
"""
    with open(claim_dir / "forbidden_extrapolations_119.md", "w", encoding="utf-8") as f:
        f.write(forbidden_md)
    print("Wrote forbidden_extrapolations_119.md")

    # 3. claim_boundary_redline_119.md
    redline_md = """# Stage 119 Claim Boundary Redline

**Date:** 2026-10-23  
**Subject:** Line-by-Line Prose Redline for Scoped Scientific Positioning

---

### Abstract
- **OLD:** `In this paper, we propose and formally validate a Policy-and-Evidence Intermediate Contract architecture that enforces strict behavioral safety without modifying underlying model weights.`
- **NEW:** `In this paper, we evaluate an externally enforced Policy-and-Evidence Intermediate Contract architecture that wraps generative components with typed semantic contracts and deterministic verification boundaries without altering model weights.`

### Introduction
- **OLD:** `Our architecture guarantees zero hallucination across complex electronic workflows.`
- **NEW:** `Our architecture bounds generative proposals to closed, byte-grounded display formats, intercepting unauthorized claims prior to presentation.`

### Conformance Interpretation
- **OLD:** `Proven by independent engineering teams.`
- **NEW:** `Evaluated using two independent interpreter implementations in Python~3.14 and Rust~1.99 developed by the research group from a shared formal specification.`

### Factorial Causality
- **OLD:** `The SLM demonstrated effective intelligence when paired with UIR.`
- **NEW:** `The SLM selector failed raw exact selection ($0/120$), but its full recall ($1.0000$) enabled the deterministic evidence guard's set intersection to recover $100.0\\%$ complete displays in template mode.`
"""
    with open(claim_dir / "claim_boundary_redline_119.md", "w", encoding="utf-8") as f:
        f.write(redline_md)
    print("Wrote claim_boundary_redline_119.md")

if __name__ == "__main__":
    main()
