# Cover Letter (Draft — Not Sent Pending Author Confirmation)

**To:**  
Editorial Office, MDPI *Electronics*  
Guest Editors, Special Issue on *Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems*:  
- Prof. Dr. Geunseok Yang (Guest Editor, *Electronics*)  
- Prof. Dr. Carlos Becker Westphall (Guest Editor, *Electronics*)  

**Date:** 2026-10-24  
**Subject:** Submission of Original Research Article to Special Issue  

---

Dear Editors,

We are pleased to submit our original research manuscript titled:

> **"Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding"**

by **Seong-Su Park** (First Author) and **Ki-Hyung Kim** (Corresponding Author) from Ajou University, Republic of Korea, for consideration in the Special Issue **"Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems"** of MDPI *Electronics*.

### 1. Alignment with Special Issue and Scientific Contributions
As autonomous generative AI and multi-agent systems are integrated into production software, ensuring deterministic safety and verifiable provenance without modifying underlying model weights is a paramount challenge. Our paper presents a software-engineering architecture—the **Sandwiched Agent Pattern**—which sandwiches generative components between pre-inference typed policy authorities and post-inference cryptographic evidence guards.

Key findings established in our manuscript include:
- **Dual-Interpreter Conformance:** Over a frozen convenience frame of $M=82$ open-source software manifest clusters ($n=60$ sampled clusters, $N=240$ primary cases), independent Python 3.14 and Rust 1.99 reference interpreters achieved $100.0\%$ ($480/480$) mutual state and fact-level conformance.
- **Exact Hypergeometric Bounding:** Under design-based inference without replacement, the null hypothesis $H_0: K \ge 5$ is decisively rejected ($p = 0.000965134$), establishing an exact 95% one-sided upper confidence bound of $K \le 2$ defective clusters ($2.439\%$ of the convenience frame).
- **Causal Decoupling via Factorial Design ($N=1,920$):** Using Microsoft Phi-3.5-mini-instruct, we demonstrate that generative fact selection suffers from distractor over-selection ($0/120$ exact match on authorized queries), but complete proposal recall allows the deterministic evidence guard to recover $100.0\%$ ($120/120$) complete displays under template rendering. Conversely, generative text rendering incurs a $36.67\%$ ($44/120$) utility omission penalty with zero incremental safety benefit.
- **Representation Neutrality:** Comparing the Universal Intermediate Representation (UIR canonical JSON) against a compact specialized format yields an identical outcome delta ($\Delta = 0.0\%$), confirming that dependability is an invariant of the deterministic contract boundary rather than representation syntax. We explicitly do not claim representation-specific accuracy superiority.

### 2. Mandatory Declarations and Affirmations
In submitting this manuscript, we formally declare:
1. **Originality and Non-Duplication:** This manuscript represents original research work. Neither this manuscript nor any substantial part of it is currently under consideration for publication elsewhere, nor has it been previously published in any peer-reviewed journal.
2. **Authorship and Consent:** Both listed authors have actively contributed to the conceptualization, execution, and manuscript preparation. All authors have reviewed the final manuscript and consent to its submission to MDPI *Electronics*.  
   *Current Status:* `[AUTHOR CONFIRMATION REQUIRED — TO BE FORMALLY RATIFIED BY THE PRINCIPAL INVESTIGATOR PRIOR TO SUSY PORTAL SUBMISSION]`
3. **Conflicts of Interest:** The authors declare no conflict of interest.
4. **Funding:** This work was supported by the National Program for Excellence in Software, Institute of Information & Communications Technology Planning & Evaluation (IITP) grant funded by the Korea government (MSIT) (No. 2023-0-00042).
5. **Data Availability:** Mathematical models, statistical recomputation scripts, and tabular reproduction routines are fully provided in our replication archive, enabling immediate, CPU-only verification by peer reviewers in under two seconds.

We believe this work provides timely, disciplined, and rigorous engineering principles directly relevant to the readership of *Electronics* and this Special Issue.

Thank you very much for your time and consideration of our manuscript.

Sincerely,

**Ki-Hyung Kim, Ph.D.** *(Corresponding Author)*  
Professor, Department of Cyber Security  
Ajou University, Suwon 16499, Republic of Korea  
Email: `kkim86@ajou.ac.kr` | Tel: +82-31-219-2433  
ORCID: 0000-0002-2321-4475  

**Seong-Su Park** *(First Author)*  
Department of Computer Engineering  
Ajou University, Suwon 16499, Republic of Korea  
Email: `parky@ajou.ac.kr`  
ORCID: 0009-0008-4056-3875  
