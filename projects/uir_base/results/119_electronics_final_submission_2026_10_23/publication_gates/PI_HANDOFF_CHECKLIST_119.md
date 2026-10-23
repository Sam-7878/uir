# Principal Investigator (PI) Final Submission Handoff Checklist

**Target Journal:** MDPI *Electronics*  
**Special Issue:** Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems  
**Special Issue URL:** https://www.mdpi.com/journal/electronics/special_issues/WFBEQFE47X  
**Submission Package:** `projects/uir_base/results/119_electronics_final_submission_2026_10_23/release/local_submission_sources_119.zip`  
**Compiled Manuscript Proof:** `projects/uir_base/paper/mdpi_electronics_119/main.pdf`  
**Date Prepared:** 2026-10-24  

---

## Step-by-Step PI Portal Submission Instructions (MDPI SuSy)

### Step 1: Portal Access and Paper Type Selection
1. Navigate to the MDPI Submission System (SuSy): [https://susy.mdpi.com](https://susy.mdpi.com).
2. Log in using your institutional credentials (`kkim86@ajou.ac.kr`).
3. Click **"Submit Manuscript"**.
4. Select Journal: **Electronics**.
5. Select Article Type: **Article** (Original Research Paper).
6. Select Special Issue: **"Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems"** (Guest Editors: Prof. Geunseok Yang, Prof. Carlos Becker Westphall).

---

### Step 2: Metadata Entry (Copy & Paste from Frozen Package)

- **Manuscript Title:**
  ```text
  Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding
  ```

- **Abstract (Single Paragraph, 181 Words, Plain Text):**
  ```text
  Integrating Small Language Model (SLM) components into software systems introduces dependability challenges, including non-deterministic semantic hallucination and unauthorized action proposals. In this paper, we evaluate an externally enforced Policy-and-Evidence Intermediate Contract architecture that wraps generative components with typed semantic contracts and deterministic verification boundaries without altering model weights. In a design-based confirmatory trial over a frozen frame of M = 82 open-source software manifest clusters (N = 240 cases, n = 60 sampled clusters), independently implemented Python 3.14 and Rust 1.99 interpreters achieved 100.0% (480/480) mutual state and fact-level conformance (p = 0.000965, bounding frame failures to at most 2/82 at 95% confidence). In an eight-condition factorial evaluation (N = 1,920 matched outcomes using Phi-3.5-mini), the SLM selector achieved 0/120 exact match on authorized queries due to distractor over-selection, yet full proposal recall enabled a deterministic evidence guard to recover 100.0% (120/120) complete displays under template rendering. Generative rendering incurred a 36.67% (44/120) utility omission penalty without safety gain. Equivalent specialized contracts produced identical outcomes, confirming that safety guarantees stem from the deterministic policy boundary rather than representation syntax.
  ```

- **Keywords:**
  ```text
  generative AI software; typed intermediate contracts; runtime verification; small language models; semantic conformance; evidence grounding; deterministic guardrails; software dependability
  ```

---

### Step 3: Author and Institutional Affiliations

1. **First Author:**
   - **Name:** Seong-Su Park
   - **Email:** `parky@ajou.ac.kr`
   - **Affiliation:** Department of Computer Engineering, Ajou University, Suwon 16499, Republic of Korea
   - **ORCID:** `0009-0008-4056-3875`
2. **Corresponding Author (*):**
   - **Name:** Ki-Hyung Kim
   - **Email:** `kkim86@ajou.ac.kr`
   - **Affiliation:** Department of Cyber Security, Ajou University, Suwon 16499, Republic of Korea
   - **Phone:** `+82-31-219-2433`
   - **ORCID:** `0000-0002-2321-4475`

---

### Step 4: Mandatory Statements & Funding Declarations

- **Funding Statement:**
  ```text
  This research was supported by the National Program for Excellence in Software, Institute of Information & Communications Technology Planning & Evaluation (IITP) grant funded by the Korea government (MSIT) (No. 2023-0-00042).
  ```
- **Data Availability Statement:**
  ```text
  The mathematical models, statistical recomputation scripts, and evaluation metadata supporting the conclusions of this article are available in the local replication archive. Independent numerical recalculation of all primary hypergeometric p-values and factorial attribution tables can be fully performed using the open-source statistical routines provided in the supplementary materials. The raw third-party repository software manifests and model interaction capture logs are maintained in a secure local repository to respect repository owner licensing terms and will be made available by the corresponding author upon reasonable academic request and execution of a standard research data agreement.
  ```
- **Conflicts of Interest:**
  ```text
  The authors declare no conflict of interest.
  ```

---

### Step 5: File Uploads

1. **Manuscript Source File:**
   - Upload: `local_submission_sources_119.zip` (contains `main.tex`, `references.bib`, `soul*.sty`, `Definitions/`, `figures/`, `main.pdf`).
2. **Cover Letter:**
   - Mention submission to Special Issue *"Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems"*, highlighting software dependability guarantees for autonomous agents.

---

### Step 6: Review Generated Proof & Submit
1. Verify that the SuSy automated PDF generation correctly displays all 15 pages, 2 figures, 4 tables, and 34 bibliography references.
2. Confirm author order: Seong-Su Park (1st), Ki-Hyung Kim (Corresponding).
3. Click **"Submit"**.
