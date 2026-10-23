# Principal Investigator (PI) Submission Handoff Checklist (Stage 120)

**Manuscript Title:** Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding  
**Target Venue:** MDPI *Electronics*  
**Special Issue:** *Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems*  
**Submission Portal:** [MDPI SuSy Submission System](https://susy.mdpi.com/)  
**Corresponding Author / PI:** Prof. Ki-Hyung Kim (`kkim86@ajou.ac.kr`)  
**First Author:** Seong-Su Park (`parky@ajou.ac.kr`)  
**Date of Handover:** 2026-10-24  

---

## 1. Submission Package Inventory and Checksums

Please verify the following three primary deliverables before logging into MDPI SuSy:

| Deliverable Item | Local File Path | Size (Bytes) | SHA-256 Checksum |
|---|---|---|---|
| **Submission PDF** | `projects/uir_base/paper/mdpi_electronics_120/main.pdf` | 282,139 | `d3470e0076c92d450ef1f9d107055688d950b41f516150c0db29105b1704eb37` |
| **Submission Source ZIP** | `projects/uir_base/results/120_electronics_release_closure_2026_10_24/release/local_submission_sources_120.zip` | 1,313,485 | `4f863829589fb7a43f52e94851feda4cee0cb66ca28435b8a4f50c2d389be81a` |
| **Reviewer Replication ZIP** | `projects/uir_base/results/120_electronics_release_closure_2026_10_24/release/reviewer_safe_replication_120.zip` | 8,109 | `739a7bb24f5a2f5bc9fa4da6e3532cfd52a22be220f83ae06d530ee233513a9d` |

---

## 2. One-Page Pre-Submission Action Checklist for PI

- [ ] **Step 1: Inspect Compiled Manuscript Text (`main.pdf`)**
  - Verify author names, affiliations, and emails on Page 1.
  - Verify that MDPI header metadata displays official submission placeholders (`vol 1, no 1, 0`) rather than premature published issue numbers.
  - Check the exact hypergeometric formulation on Page 6: $H_0: K \ge 5$ ($p = 0.000965134$) and $95\%$ confidence upper bound $K \le 2 / 82$ ($2.439\%$).
  - Review Figure 1 (Architecture Pipeline, Page 4) and Figure 2 (Factorial Response Reuse Topology, Page 9).
  - Verify Funding acknowledgement on Page 15 (IITP grant No. 2023-0-00042).

- [ ] **Step 2: Review and Execute Cover Letter (`COVER_LETTER_DRAFT_NOT_SENT.md`)**
  - Path: `results/120_electronics_release_closure_2026_10_24/editorial/COVER_LETTER_DRAFT_NOT_SENT.md`
  - Confirm the required warranty: manuscript is original and not under consideration elsewhere.
  - Confirm that all co-authors have approved the submission.
  - Copy text into MDPI SuSy submission form or export as signed PDF.

- [ ] **Step 3: Confirm Co-Author Approval (`HUMAN_APPROVAL_EVIDENCE_120_PRIVATE.md`)**
  - Path: `results/120_electronics_release_closure_2026_10_24/publication_gates/HUMAN_APPROVAL_EVIDENCE_120_PRIVATE.md`
  - Confirm that First Author Seong-Su Park has reviewed and agreed to the final text.
  - Note: Automated agent systems are strictly prohibited from submitting on your behalf.

- [ ] **Step 4: Upload Submission Archive to MDPI SuSy**
  - Upload `local_submission_sources_120.zip` as LaTeX manuscript source.
  - Upload `main.pdf` as manuscript PDF.
  - Upload `reviewer_safe_replication_120.zip` as Supplementary Material for reviewers.
  - Select Special Issue: *Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems*.

---

## 3. Post-Submission Notification

Once the submission confirmation email is received from MDPI:
1. Record MDPI Manuscript ID (e.g., `electronics-XXXXXXX`) in `results/120_.../publication_gates/FINAL_STAGE_GATE_120.json`.
2. Transition gate state from `SUBMISSION_READY: BLOCKED_PENDING_HUMAN_ACTION` to `SUBMISSION_COMPLETED`.
