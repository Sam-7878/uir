# Human Author Approval and Authorship Evidence Ledger (Stage 120 Private)

> **CONFIDENTIALITY NOTICE:** This ledger records private author verification states, contact information, and institutional sign-off requirements for Stage 120. Do not redistribute in public replication archives.

---

## 1. Author and Institutional Registry

| Author Name | Role & Authorship Order | Institutional Affiliation | Official Email | ORCID Identifier | Baseline Provenance |
|---|---|---|---|---|---|
| **Seong-Su Park** | First Author / Software & Primary Investigation | Department of Computer Engineering, Ajou University, Suwon 16499, Republic of Korea | `parky@ajou.ac.kr` | [0009-0008-4056-3875](https://orcid.org/0009-0008-4056-3875) | `dlg_gnn/projects/benchmark/paper/current/a10/` |
| **Ki-Hyung Kim** | Corresponding Author / Principal Investigator (PI) | Department of Cyber Security, Ajou University, Suwon 16499, Republic of Korea | `kkim86@ajou.ac.kr` | [0000-0002-2321-4475](https://orcid.org/0000-0002-2321-4475) | `dlg_gnn/projects/benchmark/paper/current/a10/` |

---

## 2. Target Submission Artifacts Anchoring

- **Manuscript Title:** Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding
- **Target Venue:** MDPI *Electronics* (Special Issue: *Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems*)
- **Target PDF Path:** `projects/uir_base/paper/mdpi_electronics_120/main.pdf`
- **Target PDF SHA-256:** `d3470e0076c92d450ef1f9d107055688d950b41f516150c0db29105b1704eb37`
- **Target PDF Page Count:** 16 pages
- **Cover Letter Draft:** `projects/uir_base/results/120_electronics_release_closure_2026_10_24/editorial/COVER_LETTER_DRAFT_NOT_SENT.md`

---

## 3. Human Approval Status and Event Ledger

| Checklist Item | Required Verification Action | Verification Status | Verification Timestamp & Method |
|---|---|---|---|
| **Manuscript Text Approval** | Both authors review the complete 16-page PDF text and confirm technical accuracy | `PENDING_HUMAN_VERIFICATION` | Pending human author inspection of `main.pdf` |
| **Author Contributions** | Confirmation of CRediT contribution taxonomy statement | `REPORTED_CONSISTENT_PENDING_SIGNOFF` | Sourced from `a10`; pending PI final sign-off |
| **Funding & Grant Attribution** | Grant No. 2023-0-00042 (IITP/MSIT) accuracy confirmation | `CONFIRMED_VALID_ON_FILE` | Verified against project administrative records |
| **Conflicts of Interest** | Both authors declare no financial or personal conflicts | `PENDING_HUMAN_VERIFICATION` | Placeholder on file; requires author sign-off |
| **Non-Duplication Warranty** | Warranty that manuscript has not been published or submitted elsewhere | `PENDING_HUMAN_VERIFICATION` | Drafted in cover letter; requires human execution |
| **Data Availability Policy** | Agreement to provide replication artifacts upon academic request | `PENDING_HUMAN_VERIFICATION` | Policy drafted in manuscript; requires PI sign-off |
| **Portal Submission Authority** | Physical credential holder logs into MDPI SuSy portal and uploads package | `BLOCKED_PENDING_HUMAN_ACTION` | Automation tools strictly prohibited from portal action |

---

## 4. Policy on Automated Approvals

In accordance with Section C.6 and T68 of the Stage 120 Work Order:
1. Automated tools, agents, and build scripts are strictly prohibited from generating simulated signature stamps, fake approval hashes, or declaring unverified approvals.
2. The Stage 119 declaration of `APPROVED` is recognized as a reflection of metadata transcription from baseline `a10`, but cannot substitute for independent, contemporaneous human verification of the compiled Stage 120 manuscript.
3. Therefore, the gate disposition for external submission remains:
   $$\mathbf{SUBMISSION\_READY: BLOCKED\_PENDING\_HUMAN\_ACTION}$$

---

## 5. Sign-off Action Instructions for PI

Upon manual inspection of `projects/uir_base/paper/mdpi_electronics_120/main.pdf`:
1. Verify author list, affiliations, and funding details on Pages 1 and 15.
2. Confirm that the exact hypergeometric values on Page 6 and Page 14 match your theoretical expectations ($H_0: K \ge 5$, $p = 0.000965$, $K \le 2 / 82$).
3. Review and sign `editorial/COVER_LETTER_DRAFT_NOT_SENT.md`.
4. Upload `release/local_submission_sources_120.zip` to the MDPI SuSy submission system.
