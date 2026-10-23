# Visual Page Index and Preflight Audit Report (Stage 120)

**Manuscript Title:** Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding  
**Target Venue:** MDPI *Electronics* (Special Issue: Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems)  
**PDF Target:** `projects/uir_base/paper/mdpi_electronics_120/main.pdf`  
**Page Count:** 16 pages  
**PDF SHA-256:** `d3470e0076c92d450ef1f9d107055688d950b41f516150c0db29105b1704eb37`  
**Render Resolution:** 150 DPI PNGs archived in `projects/uir_base/results/120_electronics_release_closure_2026_10_24/audit/pages_150dpi/`

---

## 1. Page-by-Page Visual and Typographic Audit

| Page | Primary Content / Structural Elements | Float Elements (Tables / Figures / Algorithms) | Visual & Typographic Quality Checks | Status |
|:---:|---|---|---|:---:|
| **1** | Title, Authors, ORCID icons, Affiliations, Correspondence, Abstract, Keywords, Section 1 Introduction | Header MDPI logo, article metadata placeholders (`vol 1, no 1, 0`) | Proper margins, no metadata overflow, ORCID vector links sharp | **PASS** |
| **2** | Section 1 Intro (cont.), RQ1--RQ3, Summary of Contributions (1--5), Section 2 Related Work | None | Clear bullet alignment, clean paragraph spacing | **PASS** |
| **3** | Section 2 Related Work (cont.), Section 3 Architecture (Sandwiched Agent, AST Grammar) | None | Math definitions and BNF grammar cleanly formatted | **PASS** |
| **4** | Section 3 Architecture (Formal State-Transition Semantics, Trace Invariant) | **Figure 1:** Architecture Pipeline (TikZ vector diagram) | Figure fits within column margins; vector fonts sharp; no raster pixelation | **PASS** |
| **5** | Closed-Channel Soundness Proof (Lemma 1, Theorem 1), Section 4 Sampling Frame ($M=82$, SRSWOR) | None | Theorem environments properly italicized with bold headers | **PASS** |
| **6** | Section 4 Methodology (Hypergeometric Invariance, Python 3.14 & Rust 1.99 Implementation) | Equations (4)--(6) | Multi-line equation breaks fit within column margins with zero overflow | **PASS** |
| **7** | Conformance Protocol, Verification Criteria | **Table 1:** Frame and Sample Specifications | Table text readable; full width aligned; clean borders | **PASS** |
| **8** | Matched Factorial Design ($2 \times 2 \times 2$, Conditions C1--C8) | **Table 2:** Factorial Evaluation Conditions | Clean tabular rules (`\toprule`, `\midrule`, `\bottomrule`), text legible | **PASS** |
| **9** | Factorial Invocation Topology & Response Reuse, Section 5 Findings | **Figure 2:** Factorial Response Reuse Graph (TikZ vector diagram) | Node labels, directional arrows, and branch labels 100% vector Palatino | **PASS** |
| **10** | Factorial Conformance Results, Quantitative Performance Analysis | **Table 3:** Factorial Evaluation Results across C1--C8 | Full 8-condition matrix centered; numbers aligned; bold row highlights clear | **PASS** |
| **11** | Deep Causal Insights (Distractor Over-Selection, Deterministic Guard Recovery, Representation Neutrality) | **Algorithm 1:** Deterministic Policy & Evidence Guard Pipeline | Algorithm box cleanly framed; algorithmic keywords formatted; no margin overflow | **PASS** |
| **12** | Section 6 Case Studies (Intro, Case Study 1: React `loose-envify`, Case Study 2: Express Policy Deny) | Trace listings | Monospace identifiers (`\texttt`) wrapped; offsets clearly formatted | **PASS** |
| **13** | Section 6 Case Studies (Case Study 3: Cargo Serde Transitive Query), Section 7 Threats to Validity | None | Internal, external, and construct validity subsections well structured | **PASS** |
| **14** | Section 8 Discussion (Sandwiched Agent Significance, Latency Overhead, Scope Limits), Section 9 Conclusions | None | Explicit negative constraints clearly enumerated; concise conclusions | **PASS** |
| **15** | Back Matter (Contributions, Funding, IRB, Consent, Data Availability, COI), References (1--24) | None | MDPI back matter styles properly applied; Data Availability strictly consistent | **PASS** |
| **16** | References (25--36) | None | Full citation metadata complete; DOIs active; clean page termination | **PASS** |

---

## 2. Preflight Defect and Invariant Checklist

1. **Submission Metadata Neutralization (Defect B120-02):**
   - Verified that premature published metadata (`\pubvolume{15}`, `\issuenum{18}`, `\articlenumber{4335}`, specific 2026 dates) is **completely purged**.
   - Current header displays official MDPI submit placeholders: `Electronics 2026, 1, 0`.
2. **Hypergeometric Arithmetic Semantics (Defect B120-01):**
   - Verified that Page 6 Section 4.3 and Page 14 Conclusion strictly present:
     - Null hypothesis: $H_0: K \ge 5$ with $p = P(X=0 \mid K=5) = 0.000965134$.
     - Test inversion: $P(X=0 \mid K=3) = 0.01738934 < 0.05$ (rejected).
     - Test boundary: $P(X=0 \mid K=2) = 0.06955736 \ge 0.05$ (non-rejected).
     - Upper confidence bound: strictly $K \le 2 / 82$ ($2.439\%$) at $95\%$ confidence.
   - Zero occurrences of conflating $K=3$ with $p=0.000965$.
3. **Reproducibility Scope Honesty (Defect B120-03):**
   - Data Availability statement on Page 15 accurately demarcates Level 1 runnable reproduction (provided scripts and mathematical models) vs. Level 2/3 proprietary/third-party repositories (available upon reasonable request).
4. **Visual Elements and Overflow:**
   - 0 fatal errors, 0 undefined citations, 0 overfull hboxes.
   - All TikZ figures compile to vector primitives without bitmap font rasterization.

**Overall Visual Preflight Disposition:** **PASS (READY FOR AUTHOR & PI REVIEW)**
