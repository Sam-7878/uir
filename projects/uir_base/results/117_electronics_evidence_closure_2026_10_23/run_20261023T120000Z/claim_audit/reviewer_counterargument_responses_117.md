# Stage 117 — Adversarial Peer-Reviewer Audit and Author Rebuttal

**Manuscript Title:** Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding  
**Target Venue:** MDPI *Electronics* Special Issue  
**Reviewer Role:** Adversarial SCI Scientific Auditor (Simulated Independent Review)

---

### Reviewer Question 1: What is the practical difference between UIR and the Specialized contract if both achieve identical scores across all 1,920 evaluations?
**Author Response:**
We thank the reviewer for this critical observation. The empirical equality across all $1,920$ cells is not a deficiency but a central finding of our work (Section 7). Both UIR and the specialized contract compile into the identical canonical semantics and evaluate against the same deterministic policy authority and evidence guard. The true engineering contribution of UIR is not an algorithmic accuracy advantage, but **interoperability, standardized dual-runtime execution (Python and Rust), and ecosystem portability**. We have explicitly revised Section 7 to ensure no reader mistakes UIR for an algorithmic improvement over equivalent typed contracts.

---

### Reviewer Question 2: The abstract reports 120/120 complete allowed displays under template rendering, yet the SLM selector achieved 0/240 exact selection. How is this possible without data leakage?
**Author Response:**
This result directly demonstrates the decoupling of Model Selection Accuracy from Accepted System Correctness (Section 6, Figure 2). The SLM selector exhibited perfect recall ($1.0000$) but poor precision ($\approx 0.35$), proposing on average $2.93$ facts per query (including distractors). The deterministic evidence guard performed a strict set intersection:
$$\mathcal{F}_{\text{acc}} = \mathcal{F}_{\text{proposed}} \cap \mathcal{F}_{\text{authorized}} \cap \mathcal{F}_{\text{requested}}$$
Because the true target fact was present, the guard discarded all $232$ extraneous distractors and passed solely the authorized target fact to the template renderer. Thus, system-level accuracy was mediated entirely by the deterministic guard, not the model's selector reasoning.

---

### Reviewer Question 3: Can the exact p-value (p = 0.000965) be interpreted as proof that UIR is safe for general industrial software?
**Author Response:**
No. As emphasized in Section 4 and Section 8, the test is strictly design-based over a frozen convenience frame of $M=82$ eligible GitHub repository owners. It provides mathematical confidence that the failure rate within *this defined frame* is at most $2.439\%$. It does not warrant an unbounded Bernoulli i.i.d. generalization to arbitrary software systems or natural language domains.

---

### Reviewer Question 4: Does the system prevent hallucinations in conversational prose?
**Author Response:**
Our zero-hallucination guarantees apply strictly to the structured \texttt{CLOSED\_FACT\_LINES\_S1} format, where every emitted claim is verified against physical source bytes at a recorded offset. As explicitly stated in Section 8, unconstrained conversational natural language prose was \texttt{NOT\_MEASURED} and is excluded from our safety claims.
