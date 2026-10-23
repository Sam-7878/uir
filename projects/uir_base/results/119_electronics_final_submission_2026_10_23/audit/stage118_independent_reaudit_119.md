# Stage 118 Independent Re-Audit & Stage 119 Scope Downgrade

**Date:** 2026-10-23T23:40:00Z  
**Auditor:** Stage 119 Independent Verification & Audit Committee  
**Subject:** Full Audit Reconciliation of Stage 118 Artifacts, Statistical Claims, and Defect Detection  
**Status:** **STAGE 118 PHYSICAL HASHES VERIFIED; TECHNICAL READINESS DOWNGRADED TO `REVISION_REQUIRED`**

---

## 1. Physical Artifact & Lineage Integrity Verification

All 28 sealed artifacts declared in `EVIDENCE_MANIFEST_118.json` were independently re-hashed using SHA-256 and compared against recorded sizes.

- **Total Sealed Entries:** 28
- **Verified Bit-Exact Matches:** 28 / 28 (100.0%)
- **Mismatches / Corruptions:** 0
- **Cross-Stage Raw Links:** The four foundational lineage files (`primary_raw.jsonl`, `secondary_raw.jsonl`, `primary_manifest_116.json`, `model_capture_reuse_118.csv`) match Stage 116/117 hashes bit-for-bit.

---

## 2. Mathematical Recomputation of Primary Statistics

The primary confirmatory trial statistics were re-evaluated under exact design-based finite-population hypergeometric sampling without replacement (SRSWOR):
- **Finite Convenience Frame ($M$):** 82 eligible GitHub software manifest owner clusters.
- **Random Sample Size ($n$):** 60 distinct owners drawn without replacement.
- **Observed Failed Clusters ($x$):** 0
- **Null Hypothesis:** Frame failure count $K \ge 5$ ($5/82 = 6.098\%$).
- **Exact Hypergeometric Equation:**
  $$p = \frac{\binom{77}{60}}{\binom{82}{60}} = \frac{49,053,802,362,729,780}{50,825,908,693,881,519,120} \approx 0.0009651337993418882$$
- **Exact 95% One-Sided Conservative Upper Bound:**
  $$P(X=0 \mid K=1) = \frac{\binom{81}{60}}{\binom{82}{60}} \approx 0.268293 \ge 0.05$$
  $$P(X=0 \mid K=2) = \frac{\binom{80}{60}}{\binom{82}{60}} \approx 0.069557 \ge 0.05$$
  $$P(X=0 \mid K=3) = \frac{\binom{79}{60}}{\binom{82}{60}} \approx 0.017389 < 0.05$$
  Therefore, the conservative 95% confidence upper bound on frame failures is exactly $K \le 2$ ($2/82 = 2.439\%$).

---

## 3. Identification of Submission-Critical Defects (Downgrade Justification)

While Stage 118 successfully resolved the physical TikZ overfull `\hbox` bug (0.0 pt overfull verified) and verified internal lineage, it suffered from three critical defects that invalidate `MANUSCRIPT_TECHNICAL_READY=PASS`:

1. **Defect 1: MDPI Abstract Word Count Violation (P0)**
   - *Electronics* Instructions for Authors mandate an abstract of **approximately 200 words maximum, in a single paragraph**.
   - Stage 118 self-reported: "305 words, PASS".
   - Plain text tokenization of the actual Stage 118 abstract reveals **343 words**, exceeding the allowable maximum by over 70%.
   - *Action required in Stage 119:* Condense abstract to 180–200 words in a single paragraph.

2. **Defect 2: Demonstrable Bibliographic Record Falsification (P0)**
   - In `references.bib`, entry `yang2024multiagent` cited *Electronics*, 2024, Vol. 13, Issue 18, Article 3612.
   - Authoritative publisher audit confirms that Article 3612 is actually:
     *Paulo H. N. Gonçalves, Hendrio Bragança, and Eduardo Souto, "Efficient Human Activity Recognition on Wearable Devices Using Knowledge Distillation Techniques"*.
   - Successful BibTeX compilation does not guarantee bibliographic veracity.
   - *Action required in Stage 119:* Conduct exhaustive 34-entry provenance forensics, replace fabricated citations, and link all references to verifiable DOIs/venues.

3. **Defect 3: Unfilled Author Metadata Placeholders (P0)**
   - `main.tex` contains literal placeholders: `[AUTHOR NAMES PENDING AUTHOR SIGN-OFF]`.
   - *Action required in Stage 119:* Import candidate author details from `dlg_gnn/projects/benchmark/paper/current/a10/` (Seong-Su Park, Ki-Hyung Kim; Ajou University) and obtain human PI sign-off.

---

## 4. Formal Disposition

Stage 118 is formally designated:
`STAGE_118_STATUS = PHYSICAL_HASHES_VERIFIED_BUT_DOWNGRADED_TO_REVISION_REQUIRED`

Stage 119 will execute tasks T49 through T59 to remediate all bibliographic, editorial, and metadata defects.
