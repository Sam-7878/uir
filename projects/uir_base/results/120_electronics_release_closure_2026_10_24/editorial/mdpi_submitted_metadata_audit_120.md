# MDPI Submitted Manuscript Metadata Audit (Defect B120-02)

**Audit Stage:** Stage 120 — Evidence, Editorial & Release Closure  
**Date:** 2026-10-24  
**Target File:** `projects/uir_base/paper/mdpi_electronics_120/main.tex`  
**Standard:** MDPI Official Author Instructions & LaTeX Submission Guidelines (`submit` class option)  

---

## 1. Description of Defect B120-02

In the Stage 119 draft of `main.tex`, the preamble contained:
```latex
\pubvolume{15}
\issuenum{18}
\articlenumber{4335}
\pubyear{2026}
\copyrightyear{2026}
```
This hardcoded metadata inadvertently mimicked an already published article from *Electronics*, Volume 15, Issue 18 (e.g., sequentially following Nam & Yang, Article 4334).

### Policy Violation:
1. **Unpublished Submission Status:** The manuscript is currently an original research submission under peer review consideration. It has neither been accepted nor scheduled for publication.
2. **Editorial Office Prerogative:** Under official MDPI workflow, Volume, Issue, Article Number, Publication Dates, and DOI are strictly assigned by the MDPI Production and Editorial Office post-acceptance. Authors must not pre-assign or hardcode these values in submission manuscripts.
3. **Template Norms:** MDPI's official `template.tex` leaves `\pubvolume{}`, `\issuenum{}`, `\articlenumber{}`, `\pubyear{}`, and `\doinum{}` unpopulated or as editorial placeholders during the `submit` phase.

---

## 2. Remediation in Stage 120

In `paper/mdpi_electronics_120/main.tex`, the metadata block is neutralized:
- `\pubvolume{}`, `\issuenum{}`, `\articlenumber{}`, `\doinum{}` are emptied or omitted.
- The documentclass options remain strictly:
  ```latex
  \documentclass[electronics,article,submit,moreauthors,pdftex]{Definitions/mdpi}
  ```
- The title, Special Issue designation (*Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems*), and authentic author/affiliation metadata are preserved.
- No fraudulent DOI or premature publication date is generated in the compiled PDF header/footer.

---

## 3. Verification Gate Disposition
- **Audit Verdict:** RESOLVED.
- **Preamble Status:** Official `submit` mode compliant. Zero false published article identifiers.
