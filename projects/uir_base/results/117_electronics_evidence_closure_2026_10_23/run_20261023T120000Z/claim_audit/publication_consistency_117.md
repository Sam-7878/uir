# Stage 117 — Publication Consistency and Reconciliation Audit

**Date:** 2026-10-23  
**Status:** `ALL_NUMERICAL_CLAIMS_RECONCILED` (Zero Discrepancies)

---

## 1. Cross-Verification Checklist

| Claim Category | Primary Claim | Evidence Source | Reconciliation Result |
|---|---|---|:---:|
| Primary Conformance | 480/480 matches across Python and Rust | `V4_independent_numeric_audit_117.json` | **PASS (Exact Match)** |
| Primary Statistics | $p = 0.000965$, upper bound $2/82$ | `internal_primary_stats_117.json` | **PASS (Exact Match)** |
| Factorial Total Records | 1,920 records (480 unique model calls) | `model_call_reuse_graph_117.json` | **PASS (Exact Match)** |
| Selector Accuracy | Raw exact $0/240$, Macro F1 $0.51587$ | `selector_guard_renderer_attribution_117.csv` | **PASS (Exact Match)** |
| Guard Recovery | $120/120$ complete in template | `selector_guard_renderer_attribution_117.csv` | **PASS (Exact Match)** |
| Renderer Degradation | $76/120$ complete, $44/120$ omission | `secondary_failure_taxonomy_117.md` | **PASS (Exact Match)** |
| Policy Enforcement | $120/120$ safe denials, $0$ leaks | `selector_guard_renderer_attribution_117.csv` | **PASS (Exact Match)** |
| Closed-Line Safety | $0$ unsupported displays | `output_scope_matrix_117.csv` | **PASS (Exact Match)** |
| Withdrawn V3 Stats | $p = 0.0106256$ excluded from all text | `V3_V4_claim_boundary_117.md` | **PASS (Excluded)** |
| Unmeasured Claims | Prose, FinQA, Portability = `NOT_MEASURED` | `optional_endpoints_decision_117.md` | **PASS (Excluded)** |

**Conclusion:** Every single number appearing in the manuscript tables, abstract, and text is directly tied to a bit-level immutable evidence artifact with zero reconciliatory deviations.
