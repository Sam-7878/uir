# Visual and Structural Layout Audit: MDPI Electronics 119 Manuscript

**Manuscript Title:** Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding  
**Authors:** Seong-Su Park, Ki-Hyung Kim (Ajou University)  
**Target Journal:** MDPI *Electronics* (Special Issue: Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems)  
**Compiled Artifact:** `paper/mdpi_electronics_119/main.pdf`  
**Page Count:** 15 pages  
**Compilation Date:** 2026-10-23 23:59:24 KST  
**Engine:** pdfTeX-1.40.28 (TeX Live 2025 / Ubuntu 26.04)

---

## 1. Page-by-Page Inspection Summary

| Page | Content & Section | Visual Layout Status | Typography & Boundaries |
|:---:|:---|:---:|:---|
| **1** | Title, Authors, Affiliations, Abstract, Keywords, Section 1 (Introduction) | PASS | MDPI header logos (`logo-mdpi.eps`, `logo-orcid.pdf`), single-column abstract (181 words), clean metadata, justified body text |
| **2** | Section 1 (Intro cont.), Contributions list, Section 2 (Related Work) | PASS | Clear numbered contribution bullets, clean paragraph spacing, proper cross-references |
| **3** | Section 2 (Related Work cont.), Table 1 (Comparative analysis table), Section 3 (Architecture) | PASS | Table 1 (`tab:related_comparison`) fits full text width with `\resizebox{\linewidth}{!}`, no text truncation |
| **4** | Figure 1 (Architecture diagram - TikZ), Five-stage pipeline description | PASS | Sandwiched Agent Pattern TikZ figure rendered crisp and centered, stage enumerations clean |
| **5** | Section 3.2 (Formal Threat Model), Section 3.3 (Mathematical Notation), Table 2 (`tab:notation`) | PASS | Clear threat definitions, notation table fits column width cleanly, no overflow |
| **6** | Section 4 (Contract Semantics), Listings 1 & 2 (UIR JSON & Compact Specialized contracts) | PASS | Clean monospace listing blocks with light gray background, balanced code formatting |
| **7** | Section 4.2 (Formal Operational Invariants), Section 5 (Empirical Methodology) | PASS | Mathematical definitions and equations (`\Phi_{\text{guard}}`, `\Phi_{\text{auth}}`) properly aligned |
| **8** | Section 5.1 (Sampling Protocol), Table 3 (`tab:primary_results`), Section 6 (Confirmatory Trial) | PASS | Table 3 clean top/mid/bottom rules, footnotes properly aligned, hypergeometric test results clear |
| **9** | Figure 2 (Attribution and Evidence Guard Flow - TikZ), Section 6.2 (Secondary Factorial) | PASS | Attribution TikZ diagram rendered crisp, condition descriptions well aligned |
| **10** | Table 4 (`tab:factorial_results`), Section 6.3 (Representation Neutrality) | PASS | Complete 8-condition factorial results ($N=1,920$) cleanly scaled to linewidth, zero column clipping |
| **11** | Section 7 (Detailed Case Studies: Cases 1, 2, 3), Section 8 (Threats to Validity) | PASS | Case study trace outputs properly formatted, distractor over-selection and omission failure clearly illustrated |
| **12** | Section 8 (Threats cont.), Section 9 (Discussion & Architectural Implications) | PASS | Closed channel boundaries, latency/memory tradeoffs, and design-based inference limitations cleanly stated |
| **13** | Section 10 (Conclusions), Author Contributions, Funding, Conflicts of Interest | PASS | Mandatory MDPI end matter declarations complete and verified against institutional source |
| **14** | References (Entries 1--27) | PASS | MDPI numeric bibliography format, complete DOIs/URLs, authenticated Guest Editor citation included |
| **15** | References (Entries 28--34), Disclaimer | PASS | Balanced final reference columns, clean MDPI standard disclaimer and footer |

---

## 2. Typographical & Layout Defect Verification

1. **Overfull / Underfull Hboxes:**
   - Fatal Overfull Boxes: 0 (No text protrudes into margins or headers).
   - Underfull Badness > 5000: Eliminated via standard `tabular` wrapping and `\resizebox{\linewidth}{!}`.
2. **Floats and Tables:**
   - All 4 tables (`tab:related_comparison`, `tab:notation`, `tab:primary_results`, `tab:factorial_results`) are floating cleanly with captions above tables as required by MDPI guidelines.
   - All 2 figures (`fig:arch`, `fig:attribution`) are centered with captions below figures.
3. **Hyperlinks and Metadata:**
   - PDF metadata (`Title`, `Author`, `Subject`, `Keywords`) populated cleanly without unrendered math tokens or hyperref warnings.
   - All cross-references (Sections, Tables, Figures, Equations) resolve to valid target numbers with 0 undefined labels.
4. **Author & Institutional Metadata:**
   - First Author: Seong-Su Park (`0009-0008-4056-3875`, Dept. of Computer Engineering, Ajou University).
   - Corresponding Author: Ki-Hyung Kim (`0000-0002-2321-4475`, Dept. of Cyber Security, Ajou University).
   - Funding: MSIT / IITP National Program for Excellence in Software (No. 2023-0-00042).
   - No placeholder strings (`TODO`, `TBD`, `[Affiliation]`, `Author 1`) remain anywhere in the document.

---

## 3. Visual Review Verdict
- **Layout Compliance:** PASS
- **MDPI Style Adherence:** PASS
- **Visual Typography:** EXCELLENT
- **Compilation Status:** 0 Errors, 0 Warnings, Ready for Packaging.
