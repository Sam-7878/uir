# Visual Page Index: 15-Page Compiled MDPI Manuscript

**Manuscript Title:** Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding  
**Compiled Document:** `paper/mdpi_electronics_119/main.pdf`  
**Total Pages:** 15  
**Compilation Status:** Verified Clean-Room Build (0 Errors, 0 Warnings)  

---

## Page-by-Page Detailed Layout Index

### Page 1
- **Top Matter:** MDPI Electronics Journal Header, ISSN, Volume, Special Issue Banner, `logo-mdpi.eps`, `logo-orcid.pdf`.
- **Title Block:** `Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding`.
- **Authors & Affiliations:** Seong-Su Park (Dept. of Computer Engineering, Ajou University), Ki-Hyung Kim (Dept. of Cyber Security, Ajou University).
- **Correspondence & Dates:** `kkim86@ajou.ac.kr`, Tel. +82-31-219-2433; Received / Revised / Accepted / Published metadata fields.
- **Abstract:** Single paragraph, 181 words, plain visible text (M = 82, n = 60, N = 240, 480/480, p = 0.000965, K <= 2/82, 0/120, 120/120, 44/120).
- **Keywords:** 8 authoritative keywords.
- **Body Content:** Section 1 (Introduction) opening paragraphs.

### Page 2
- **Body Content:** Section 1 (Introduction cont.) — Dependability Challenges (Stochastic Hallucination, Unauthorized Action Proposals, Cross-Environment Divergence).
- **Contributions List:** Four explicit architectural and empirical contributions.
- **Section 2:** Related Work (Generative AI Safety, Grounding Architectures, RAG, Self-RAG, NeMo Guardrails, LMQL).

### Page 3
- **Floating Element:** **Table 1 (`tab:related_comparison`):** Comparative analysis of generative AI safety and grounding architectures (full linewidth scaling).
- **Body Content:** Section 2 cont. — Compiler Intermediate Representations (LLVM, WebAssembly), Small Language Models for Systems Control (Phi-3.5-mini, LLaMA).
- **Section 3:** System Architecture and Threat Taxonomy overview.

### Page 4
- **Floating Element:** **Figure 1 (`fig:arch`):** The Policy-and-Evidence Intermediate Contract Architecture (Sandwiched Agent Pattern TikZ diagram).
- **Body Content:** Section 3.1 cont. — Detailed five-stage pipeline operational flow (Contract Compilation, Policy Authority, Registry Binding, Proposal Generation, Guard & Display).

### Page 5
- **Body Content:** Section 3.2 — Formal Threat Model (Threat 1: Semantic Hallucination, Threat 2: Privilege Escalation, Threat 3: Runtime Inconsistency).
- **Section 3.3:** Mathematical Foundations and Notation.
- **Floating Element:** **Table 2 (`tab:notation`):** Mathematical notation and architectural symbols ($M, n, N, K, x, \mathcal{C}_{\text{query}}, \mathcal{F}_{\text{prop}}, \mathcal{F}_{\text{auth}}, \mathcal{F}_{\text{req}}, \mathcal{F}_{\text{acc}}, \pi$).
- **Section 4:** Formal Contract Semantics and Concrete Specifications.

### Page 6
- **Code Listings:**
  - **Listing 1 (`lst:uir_contract`):** Universal Intermediate Representation (UIR Canonical JSON schema).
  - **Listing 2 (`lst:specialized_contract`):** Specialized Compact Intermediate Representation.
- **Body Content:** Section 4.2 — Formal Operational Invariants and Soundness Guarantees (Definition 1: Ground Truth Conformance, Lemma 1: Deterministic Guard Invariance, Theorem 1: Grounded Attribution Soundness).

### Page 7
- **Body Content:** Section 5 (Empirical Methodology and Experimental Setup).
- **Section 5.1:** Sampling Protocol and Design-Based Inference ($M=82$ convenience frame, random sampling without replacement).
- **Section 5.2:** Sampling Frame and Cluster Stratification.
- **Section 5.3:** Hypothesis Formulation ($H_0: K \ge 3$ vs. $H_1: K \le 2$).
- **Section 5.4:** Statistical Decision Rule and Hypergeometric Exact Testing.

### Page 8
- **Floating Element:** **Table 3 (`tab:primary_results`):** Primary confirmatory trial results ($M=82, n=60, N=240, \text{Cross-Exec}=480/480$, $p = 0.000965134$, $K \le 2/82$).
- **Body Content:** Section 6 (Confirmatory Trial: Interpreter Conformance) analysis.
- **Section 6.1:** Secondary Factorial Evaluation Design ($2 \times 2 \times 2$ conditions).

### Page 9
- **Floating Element:** **Figure 2 (`fig:attribution`):** Fact Proposal, Interception, and Display Rendering Flow (TikZ sequence and set-intersection diagram).
- **Body Content:** Section 6.2 cont. — Condition-by-condition definitions (Conditions C1 through C8).

### Page 10
- **Floating Element:** **Table 4 (`tab:factorial_results`):** Complete secondary factorial experimental results ($N=1,920$ outcome rows, Macro F1, Complete Display, Blocked DENY).
- **Body Content:** Section 6.3 — Representation Neutrality ($\Delta = 0.0\%$).
- **Section 7:** Detailed Case Studies and Execution Traces introduction.

### Page 11
- **Body Content:**
  - Case Study 1: SLM Distractor Over-Selection and Guard Recovery (`CASE_ALLOW_REACT_DEP`).
  - Case Study 2: Generative Renderer Omission Failure (`CASE_ALLOW_MULTIDEP`).
  - Case Study 3: Counterfactual Interception of Unauthorized Requests (`CASE_DENY_PRIVATE_CONFIG`).
- **Section 8:** Threats to Validity (Internal Validity: deterministic seeding, exact arithmetic; External Validity: bounded convenience frame).

### Page 12
- **Body Content:**
  - Section 8 cont.: Construct Validity (closed channel guarantees vs. open unconstrained prose).
  - Section 9: Discussion and Architectural Implications (Sandwiched Agent Pattern, Computational and Latency Overhead, Negative Constraints on Unmeasured Claims).

### Page 13
- **Body Content:** Section 10 (Conclusions and Future Work).
- **End Matter Declarations:**
  - Author Contributions (CRediT taxonomy for Seong-Su Park and Ki-Hyung Kim).
  - Funding (MSIT / IITP National Program for Excellence in Software No. 2023-0-00042).
  - Institutional Review Board & Informed Consent Statements.
  - Data Availability Statement (Multi-tier governance).
  - Conflicts of Interest (Declared none).

### Page 14
- **References:** Bibliography entries [1] through [26], formatted in MDPI numeric style with complete publication metadata, DOIs, and URLs.

### Page 15
- **References cont.:** Bibliography entries [27] through [34] (including Guest Editor authentic citation [28]: Nam & Yang 2026 *Electronics*).
- **MDPI Publisher Disclaimer & Copyright Notice:** Standard MDPI Open Access disclaimer, Creative Commons CC BY 4.0 license block.
