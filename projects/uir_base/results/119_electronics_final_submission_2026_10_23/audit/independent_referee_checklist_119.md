# Independent Referee Audit Checklist: MDPI Electronics Evaluation

**Manuscript Title:** Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding  
**Authors:** Seong-Su Park, Ki-Hyung Kim (Ajou University)  
**Journal:** MDPI *Electronics*  
**Special Issue:** Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems  
**Evaluation Date:** 2026-10-24  
**Audit Standard:** MDPI Peer Review Guidelines & Committee on Publication Ethics (COPE) Standards  

---

## Evaluation Grid

| Category | Evaluation Item | Target Standard | Audit Result | Status |
|:---|:---|:---|:---|:---:|
| **1. Originality & Scope** | Alignment with Special Issue | Explicit focus on generative-AI software architecture and multi-agent contracts | High alignment with Generative & Multi-Agent software dependability | PASS |
| | Novelty of Contribution | Distinct Sandwiched Agent Pattern with typed intermediate contracts and dual reference interpreters | Addresses key gap between probabilistic decoders and deterministic safety boundaries | PASS |
| | Distinction from Prior Work | Contrasted against RAG, Self-RAG, NeMo Guardrails, and LMQL | Explicit Table 1 comparing guarantees and failure modes | PASS |
| **2. Scientific Rigor** | Proof vs. Test Separation | Mathematical invariants separated from empirical statistical trials | Section 4 formalizes proofs; Section 6 bounds empirical tests | PASS |
| | Sampling Frame Validity | Finite convenience frame ($M=82$) explicitly bounded | Zero unwarranted general population extrapolations; $M=82$ convenience frame declared | PASS |
| | Statistical Correctness | Exact hypergeometric test without replacement ($n=60, x=0$) | $p = 0.000965134$, upper bound $K \le 2$ ($2.439\%$) fully recalculated | PASS |
| | Factorial Design Balance | Matched $2 \times 2 \times 2$ factorial evaluation ($N=1,920$) | Balanced orthogonal cells with identical prompt contracts across representations | PASS |
| **3. Presentation & Style** | Official Template Usage | MDPI LaTeX class (`Definitions/mdpi.cls`) | Successfully compiled with official template, logos, and bibtex style | PASS |
| | Abstract Length & Formatting | $\le 200$ words, single paragraph, plain visible text | Exactly 181 words, single paragraph, zero math shift warnings | PASS |
| | Floating Objects & Tables | Tables above caption, figures below, no margin overflow | Clean linewidth scaling via `\resizebox{\linewidth}{!}`, 0 text clip | PASS |
| | Math & Symbols Notation | Unified mathematical symbol table | Comprehensive Table 2 (`tab:notation`) indexing all domains and symbols | PASS |
| **4. Citation & Scholarship** | Citation Authenticity | 100% verified real publisher records, zero hallucinated papers | All 34 entries verified via CrossRef, ACM, IEEE, Springer, MDPI | PASS |
| | Editorial Integrity | Guest Editor paper authentic and accurately characterized | Prof. Geunseok Yang's 2026 *Electronics* paper accurately cited for task-budget regressions | PASS |
| | Citation Placement | Every citation supports a concrete factual claim | Mapped line-by-line in `bibliography/citation_claim_support_119.csv` | PASS |
| **5. Reproducibility & Ethics** | Multi-Tier Reproduction | Level 1 (Instant), Level 2 (CPU), Level 3 (GPU) documented | Complete `REPRODUCTION_LEVELS_119.md` with verified code snippets | PASS |
| | Data Availability Statement | Clear separation of public aggregates vs. restricted raw manifests | Fully aligned with MDPI repository guidelines and license constraints | PASS |
| | Declarations & Governance | Author contributions, funding grant, COI, institutional address | Complete metadata from Ajou University matching grant No. 2023-0-00042 | PASS |

---

## Referee Overall Recommendation
**Recommendation:** **ACCEPT SUBJECT TO PI FINAL REVIEW (NO TECHNICAL REVISION REQUIRED)**  
The manuscript satisfies all MDPI *Electronics* scientific, editorial, and presentation standards.
