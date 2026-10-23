# Stage 117 — V3/V4 Lineage and Claim Boundary Specification

**Date:** 2026-10-23  
**Auditor:** Independent Re-scoring Engine (Stage 117)  
**Status:** Canonical Claim Boundary Sealed

---

## 1. Executive Lineage Map

| Checkpoint Alias | Run ID | Status | Valid Scientific Claims | Strictly Forbidden Claims |
|---|---|---|---|---|
| **V4 Primary** | `run_20261023T100000Z` | Valid Scoped Confirmatory | Exact finite-frame hypergeometric rejection ($p=0.000965$, upper bound $2/82$ failed clusters). Deterministic semantic and cross-runtime conformance ($480/480$). | Generalization to all software systems, Bernoulli i.i.d. inference, UIR superiority over specialized representation. |
| **V3 Secondary** | `run_20261023T095730Z` | Valid Descriptive Factorial | 8 factorial conditions ($N=1,920$). Raw SLM selector exact match $0/240$. Shared guard recovers $120/120$ template completion. SLM renderer utility drop ($76/120$ complete, $44$ empty/omission). | Independent SLM reasoning capability, 1,920 independent inference calls (actually 480 unique calls reused across representations). |
| **V3 Primary** | `run_20261023T094720Z` | Inferential Stats Withdrawn | Descriptive agreement preserved ($480/480$). | Citing $p=0.0106256$ or associated confidence intervals. |
| **Stage 116 Seal** | `run_20261023T100400Z` | Manifest-Sealed Checkpoint | Bit-level byte integrity verified across all 16 runs ($16/16$ exact SHA-256 match). | Claiming external publication readiness or remote repository cleanliness. |

---

## 2. Mathematical Formalization of V4 Primary Inference

1. **Finite Population Frame:**
   The target frame comprises $M = 82$ frozen eligible software-owner clusters from GitHub.
2. **Sampling Protocol:**
   $n = 60$ distinct clusters were drawn via simple random sampling without replacement (SRSWOR).
3. **Cluster Evaluation:**
   Each sampled cluster was evaluated on 4 query cases under both UIR and Specialized contracts across Python and Rust interpreters ($60 \times 4 \times 2 = 480$ evaluation rows).
4. **Observed Result:**
   Failed clusters $k = 0$.
5. **Exact Hypergeometric Hypothesis Test:**
   - Null Hypothesis $H_0: K \ge 5$ (failure rate in the 82-owner frame is $\ge 6.1\%$).
   - One-sided $p$-value:
     $$p = \frac{\binom{82-5}{60}}{\binom{82}{60}} = \frac{\binom{77}{60}}{\binom{82}{60}} \approx 0.000965134$$
   - Decision: Reject $H_0$ at $\alpha = 0.05$.
6. **One-sided 95% Confidence Upper Bound:**
   - Smallest $K$ satisfying $P(X = 0 \mid M=82, K, n=60) \le 0.05$ is $K = 3$.
   - Hence, with $95\%$ confidence, the number of failing clusters in the frame is at most $2$ ($2/82 = 2.439\%$).

---

## 3. Core Scientific Principles for the Electronics Manuscript

1. **Model-Level Correctness $\neq$ Accepted-System Correctness:**
   The SLM selector frequently proposed irrelevant fact IDs (raw exact match $0/240$). However, the deterministic intermediate guard computed the exact intersection between proposed facts and normative policy requirements, rescuing the final accepted template display ($120/120$).
2. **Utility-Safety Trade-off in Model Rendering:**
   While the deterministic template achieved $120/120$ complete allowed displays, delegating rendering to the SLM resulted in $44/120$ omissions/refusals ($63.33\%$ completion rate), demonstrating the utility cost of unconstrained generative components.
3. **Representation Equivalence Without Superiority:**
   Because both UIR and Specialized formats interfaced with the same underlying deterministic policy authority and fact registry, their execution semantics and safety properties were strictly identical ($480/480$). UIR provides architectural interoperability, not algorithmic superiority.
