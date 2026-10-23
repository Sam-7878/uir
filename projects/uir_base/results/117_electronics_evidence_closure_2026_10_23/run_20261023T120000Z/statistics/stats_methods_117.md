# Stage 117 — Statistical Methodology Specification

**Target Manuscript:** MDPI *Electronics* Special Issue  
**Title:** Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding  

---

## 1. Primary Hypothesis: Design-Based Finite Population Inference

Traditional software testing often misapplies Bernoulli i.i.d. assumptions to non-random software samples. In contrast, our primary confirmatory evaluation strictly employs **design-based finite-population sampling theory**:

1. **Target Frame:**
   A frozen frame of $M = 82$ eligible GitHub repository owners whose software manifests satisfied our strict inclusion criteria.
2. **Sampling Mechanism:**
   A simple random sample without replacement ($SRSWOR$) of $n = 60$ distinct clusters was drawn before any test outcome was observed.
3. **Cluster Evaluation:**
   Within each selected cluster $i \in \{1, \dots, 60\}$, four distinct query cases were executed under both UIR and Specialized contracts across independent Python and Rust runtimes:
   $$N_{\text{total}} = 60 \times 4 \times 2 = 480 \text{ records}$$
   A cluster is scored as a *failure* if any of its 4 cases exhibits a semantic discrepancy, runtime crash, state divergence, or unauthorized display.
4. **Exact Hypergeometric Hypothesis Test:**
   - Null Hypothesis $H_0: K \ge 5$ (at least 5 clusters in the 82-owner frame fail, representing an intolerable error rate $\ge 6.1\%$).
   - Alternative Hypothesis $H_1: K < 5$.
   - Test Statistic: Observed failing clusters $k = 0$.
   - Exact one-sided $p$-value:
     $$p = P(X = 0 \mid M=82, K=5, n=60) = \frac{\binom{5}{0}\binom{82-5}{60}}{\binom{82}{60}} = \frac{\binom{77}{60}}{\binom{82}{60}} \approx 0.000965134$$
   - Conclusion: Reject $H_0$ at the nominal $\alpha = 0.05$ significance level.
5. **Exact One-Sided 95% Confidence Upper Bound:**
   The maximum number of failing clusters $K_{\text{upper}}$ in the frame compatible with observing $0$ failures at confidence $1 - \alpha = 0.95$ is:
   $$\max \{ K : P(X = 0 \mid M=82, K, n=60) > 0.05 \} = 2$$
   Hence, the failure rate in the frame is bounded by $2 / 82 = 2.439\%$.

---

## 2. Secondary Factorial Design: Generative Attribution

The secondary experiment evaluates an $8$-condition full factorial design:
$$\{ \text{UIR}, \text{SPECIALIZED} \} \times \{ \text{DETERMINISTIC}, \text{SLM Selector} \} \times \{ \text{TEMPLATE}, \text{SLM Renderer} \}$$
applied to $240$ cases ($120$ authorized ALLOW, $120$ unauthorized DENY), totaling $1,920$ outcome rows.

- **Model Execution Accounting:** Phi-3.5-mini-instruct was called exactly $480$ unique times ($240$ unique selector prompts and $240$ unique renderer prompts). Because UIR and Specialized share identical semantic contracts, responses were reused across representations to prevent duplicate GPU compute.
- **Reporting Rule:** The $1,920$ rows represent paired matched evaluations across configurations, NOT $1,920$ independent degrees of freedom.
