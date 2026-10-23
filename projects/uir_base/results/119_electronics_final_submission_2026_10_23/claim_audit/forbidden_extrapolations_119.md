# Stage 119 Forbidden Extrapolations and Bounded Language Policy

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
1. **Deductive Mathematical Consequence:** $\mathcal{F}_{	ext{acc}} = \mathcal{F}_{	ext{prop}} \cap \mathcal{F}_{	ext{auth}} \cap \mathcal{F}_{	ext{req}}$ deterministically purges unauthorized or extraneous facts.
2. **Observed Sample Outcome:** 480/480 records matched between Python and Rust; 0/120 exact raw match by SLM; 120/120 recovery under template rendering.
3. **Finite-Population Statistical Inference:** Hypergeometric test ($p=0.000965$, $K \le 2$) applies strictly to the defined convenience frame of $M=82$ open-source manifest clusters.
4. **Explicitly Unmeasured Endpoints (`NOT_MEASURED`):** Unconstrained conversational prose, FinQA accuracy, energy consumption, execution latency, FPGA acceleration, and multi-domain generalization.
