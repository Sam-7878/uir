# Independent Referee Adversarial Audit Checklist (Stage 118)

**Audit Perspective:** Skeptical Senior Referee (MDPI *Electronics* / IEEE TSE / ACM TOSEM standards)  
**Date of Audit:** 2026-10-23  
**Manuscript Under Review:** `main.pdf` (17 pages)  
**Title:** *"Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding"*  
**Verdict:** **ACCEPT WITH FORMAL SCOPE ACKNOWLEDGMENT (No Fatal Flaws Remaining)**

---

## 1. Denominator Consistency & Metric Eligibility Audit

- [x] **Criterion 1.1: Clarified SLM Selector Denominator**  
  *Finding:* In earlier revisions, reporting raw selector accuracy as $0\%$ without specifying the subset created ambiguity. In Section 5.3 and Table 2, the authors explicitly differentiate the ALLOW-case exact match rate ($0/120$, $0.0\%$) from the pooled diagnostic rate ($0/240$, $0.0\%$), and report component Precision ($0.3529$), Recall ($1.0000$), and Macro F1 ($0.5159$).  
  *Referee Verdict:* **SATISFACTORY.**

- [x] **Criterion 1.2: Clarified Generative Renderer Utility Loss**  
  *Finding:* The renderer utility loss is correctly computed exclusively over authorized cases: $44/120$ ($36.67\%$). The authors do not artificially inflate or deflate this denominator with DENY cases.  
  *Referee Verdict:* **SATISFACTORY.**

- [x] **Criterion 1.3: Counterfactual Role of DENY Model Inferences**  
  *Finding:* The authors explicitly address why model inferences were executed on DENY cases: they serve as counterfactual stress tests demonstrating that even if an untrusted component generates output under an unauthorized state, the external guard intercepts and blocks it. The manuscript explicitly clarifies that in an optimized production system, the pre-inference policy authority short-circuits the pipeline before compute allocation.  
  *Referee Verdict:* **SATISFACTORY.**

---

## 2. Scientific Claim Boundaries & Over-claiming Audit

- [x] **Criterion 2.1: Route B Finite Population Boundary**  
  *Finding:* The manuscript repeatedly and consistently bounds its primary confirmatory claims to the frozen convenience frame of $M=82$ open-source software manifest clusters ($n=60$ sample, $p = 0.000965$, $K \le 2$). There is no claim of generalizability to unconstrained software ecosystems, web datasets, or open-domain text.  
  *Referee Verdict:* **EXCELLENT RIGOR.**

- [x] **Criterion 2.2: Removal of Hardware, Energy, and Latency Claims**  
  *Finding:* All unverified claims regarding energy consumption, battery lifetime, and FPGA acceleration were audited. The manuscript explicitly states in Section 8.3: *"Energy consumption, power dissipation, execution latency, and FPGA hardware acceleration metrics were not measured. No empirical claims regarding energy or cost reductions on edge devices are made."*  
  *Referee Verdict:* **FULLY REMEDIATED.**

- [x] **Criterion 2.3: Restricting Zero-Hallucination to Closed Channel**  
  *Finding:* The manuscript explicitly clarifies in Section 8.3 that zero-hallucination guarantees apply strictly to the pipe-delimited, byte-grounded closed display channel (`CLOSED_FACT_LINES_S1`), not to unconstrained conversational text.  
  *Referee Verdict:* **HONEST & PRECISE.**

---

## 3. Causal Decoupling & Representation Neutrality Audit

- [x] **Criterion 3.1: Attribution of Recovery to Deterministic Guard**  
  *Finding:* The manuscript does NOT claim that the generative SLM learned to be accurate. It explicitly models the causal structure as a set intersection:
  $$\mathcal{F}_{\text{acc}} = \mathcal{F}_{\text{prop}} \cap \mathcal{F}_{\text{auth}} \cap \mathcal{F}_{\text{req}}$$
  Because the model achieved full recall ($\mathcal{F}_{\text{req}} \subseteq \mathcal{F}_{\text{prop}}$), the deterministic guard is able to discard the 232 over-selected distractors and recover $120/120$ ($100.0\%$) valid displays. System safety is correctly credited to software engineering boundaries rather than model intelligence.  
  *Referee Verdict:* **THEORETICALLY SOUND.**

- [x] **Criterion 3.2: Representation Equivalence (UIR vs. Specialized)**  
  *Finding:* Table 2 demonstrates that UIR and the specialized contract produce identical outcomes across all 1,920 factorial rows. The authors explicitly state in Section 5.4 that representation superiority is `NOT_IDENTIFIED`, confirming that safety guarantees stem from the invariant policy architecture rather than syntax.  
  *Referee Verdict:* **HIGH INTEGRITY (Resists temptation to hype custom syntax).**

---

## 4. Visual Layout & Typographic Hygiene

- [x] **Criterion 4.1: Elimination of Margin Truncation**  
  *Finding:* Prior drafts exhibited severe TikZ overflows (up to 401.02 pt). The revised document compiles with 0.0 pt overfull boxes across all 17 pages. Figures 1 and 2 and Tables 1 and 2 fit cleanly within standard margins.  
  *Referee Verdict:* **PASSED.**

- [x] **Criterion 4.2: Completeness of Scholarly Context**  
  *Finding:* The bibliography has been expanded to 34 verified, relevant citations spanning software architecture, formal contracts, neurosymbolic verification, and SLM safety. Every citation is discussed in depth in the text.  
  *Referee Verdict:* **COMPREHENSIVE.**

---

## 5. Overall Recommendation

The manuscript presents an exceptionally thorough, mathematically sound, and rigorously bounded evaluation of intermediate software contracts for generative AI. All previous audit discrepancies, overfull warnings, and metric ambiguities have been resolved. The paper is ready for final author sign-off and publication processing.
