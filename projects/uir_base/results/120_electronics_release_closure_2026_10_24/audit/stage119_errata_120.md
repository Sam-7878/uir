# Stage 119 Errata and Semantic Clarification Notice (Defect B120-01)

**Issuing Stage:** Stage 120 — Evidence, Editorial & Release Closure  
**Date of Notice:** 2026-10-24  
**Subject:** Formal Erratum on Hypergeometric Null Hypothesis Notation and Confidence Upper Bound Inversion  
**Impacted Documents in Stage 119 (Preserved Frozen):**  
1. `docs/work_reports/uir_base/119_T49-T59/T119_EXECUTION_REPORT.md` (Section 2, Task T49)
2. `projects/uir_base/results/119_electronics_final_submission_2026_10_23/audit/publication_consistency_119.json` (Entry `exact_hypergeometric_p_value`)

---

## 1. Description of the Semantic Error in Stage 119 Reports

In `T119_EXECUTION_REPORT.md` (Section 2, Task T49), the text stated:
$$\text{Erroneous Formula in T119 Report:}\quad P(X=0 \mid K=3, M=82, n=60) = \frac{\binom{3}{0}\binom{79}{60}}{\binom{82}{60}} = \frac{22 \times 21 \times 20}{82 \times 81 \times 80} = 0.000965134$$
Similarly, `publication_consistency_119.json` mapped the symbol `P(X=0 | K=3)` to the value `0.000965134`.

### Mathematical Fact:
Calculating the product explicitly:
$$\frac{22 \times 21 \times 20}{82 \times 81 \times 80} = \frac{9,240}{531,360} \approx \mathbf{0.017389340560072266}$$
The value **$0.000965133799...$** is mathematically the probability under **$K=5$**:
$$P(X=0 \mid K=5, M=82, n=60) = \frac{\binom{5}{0}\binom{77}{60}}{\binom{82}{60}} = \frac{22 \times 21 \times 20 \times 19 \times 18}{82 \times 81 \times 80 \times 79 \times 78} = \frac{3,160,080}{3,274,240,320} \approx \mathbf{0.0009651337993418882}$$

---

## 2. Distinction Between Hypothesis Testing and Confidence Inversion

In the formal statistical methodology of design-based inference (SRSWOR over finite population $M=82$):

1. **Primary Hypothesis Test ($H_0: K \ge 5$ vs. $H_1: K \le 4$):**
   - The null hypothesis asserts that at least 5 clusters in the convenience frame are defective ($K \ge 5$).
   - The test statistic is $X$, the number of observed defective clusters in a sample of $n=60$.
   - The p-value is the maximum probability of observing $X=0$ under $H_0$:
     $$p = \max_{K \ge 5} P(X \le 0 \mid K) = P(X=0 \mid K=5) \approx \mathbf{0.000965134}$$
   - Since $p < 0.001 \ll 0.05$, $H_0$ is decisively rejected.

2. **95% One-Sided Upper Confidence Bound ($K \le 2$):**
   - The confidence bound is derived by testing each integer $K$ at significance level $\alpha = 0.05$:
     - For $K=3$: $P(X=0 \mid K=3) = 0.017389 < 0.05 \implies \text{REJECT } K=3$.
     - For $K=2$: $P(X=0 \mid K=2) = 0.069557 \ge 0.05 \implies \text{ACCEPT } K=2$.
   - Therefore, the exact $95\%$ one-sided upper confidence bound is strictly **$K \le 2$** ($2/82 = 2.439\%$).

---

## 3. Status of the Primary Manuscript (`main.tex`)

Fortunately, the primary manuscript text in `paper/mdpi_electronics_119/main.tex` and `mdpi_electronics_120/main.tex` already correctly separated these two operations in its Section 5.4:
- Equation (4) explicitly tests $H_0: K \ge 5$ yielding $p = 0.0009651338$.
- Equation (5) explicitly inverts the test using $P(X=0 \mid K=3) < 0.05$ to establish $K \le 2$.

Therefore, **the scientific findings and conclusions of the paper remain 100% valid and mathematically uncompromised.** The error was confined to narrative text in the secondary execution report and the variable naming in the automated consistency validator.

---

## 4. Supersession by Stage 120
Stage 120 establishes [`statistics/hypergeom_source_of_truth_120.json`](file:///d:/_Work/goat_bank/uir/projects/uir_base/results/120_electronics_release_closure_2026_10_24/statistics/hypergeom_source_of_truth_120.json) and enforces automated semantic validation via [`scripts/check_hypergeom_semantics_120.py`](file:///d:/_Work/goat_bank/uir/projects/uir_base/results/120_electronics_release_closure_2026_10_24/scripts/check_hypergeom_semantics_120.py) across all Stage 120 artifacts.
