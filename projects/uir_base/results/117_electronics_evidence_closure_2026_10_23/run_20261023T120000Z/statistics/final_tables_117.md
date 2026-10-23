# Stage 117 — Official Publication Tables

## Table 1: Primary Confirmatory Finite-Frame Evaluation
*Finite-frame design: $M=82$ eligible clusters, $n=60$ sampled clusters, 240 unique cases, 480 representation records.*

| Representation | Evaluated Cases | Python-Rust State Match | Fact IDs Match | Failed Clusters | Exact Hypergeometric $p$ | 95% Upper Bound |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Specialized Contract | 240 | 240/240 (100.0%) | 240/240 (100.0%) | 0 / 60 | -- | -- |
| UIR (Universal Contract) | 240 | 240/240 (100.0%) | 240/240 (100.0%) | 0 / 60 | -- | -- |
| **Joint Evaluation** | **480** | **480/480 (100.0%)** | **480/480 (100.0%)** | **0 / 60** | **0.000965** | **2 / 82 (2.44%)** |

---

## Table 2: Secondary 8-Condition Factorial Attribution Analysis
*Evaluation across $N=1,920$ outcome rows (480 unique model calls reused across equivalent contracts).*

| Representation | Fact Selector | Display Renderer | ALLOW Complete | ALLOW Omission | DENY Blocked | Raw Selector Exact | Macro F1 | Unsupported Displays |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Specialized | Deterministic | Template | 120/120 (100%) | 0/120 (0%) | 120/120 (100%) | 120/120 (100%) | 1.0000 | 0 |
| Specialized | Deterministic | SLM | 76/120 (63.3%) | 44/120 (36.7%) | 120/120 (100%) | 120/120 (100%) | 1.0000 | 0 |
| Specialized | SLM | Template | 120/120 (100%) | 0/120 (0%) | 120/120 (100%) | 0/120 (0.0%) | 0.5159 | 0 |
| Specialized | SLM | SLM | 76/120 (63.3%) | 44/120 (36.7%) | 120/120 (100%) | 0/120 (0.0%) | 0.5159 | 0 |
| UIR | Deterministic | Template | 120/120 (100%) | 0/120 (0%) | 120/120 (100%) | 120/120 (100%) | 1.0000 | 0 |
| UIR | Deterministic | SLM | 76/120 (63.3%) | 44/120 (36.7%) | 120/120 (100%) | 120/120 (100%) | 1.0000 | 0 |
| UIR | SLM | Template | 120/120 (100%) | 0/120 (0%) | 120/120 (100%) | 0/120 (0.0%) | 0.5159 | 0 |
| UIR | SLM | SLM | 76/120 (63.3%) | 44/120 (36.7%) | 120/120 (100%) | 0/120 (0.0%) | 0.5159 | 0 |
