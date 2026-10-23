#!/usr/bin/env python3
"""
Stage 118 — T39 & T40 Execution Script
Audit declarative claims, correct metric eligibility and denominators,
map factorial dependencies, and formalize counterfactual claim limitations.
"""

import json
import os
import csv
import yaml

BASE_DIR = "/mnt/d/_Work/goat_bank/uir"
STAGE118_RUN = os.path.join(BASE_DIR, "projects/uir_base/results/118_electronics_submission_remediation_2026_10_23")

def main():
    print("--- [T39 & T40] Auditing Claims, Metric Eligibility, and Factorial Causality ---")

    # 1. claim_semantics_audit_118.csv (T39)
    claims_audit = [
        {
            "claim_id": "CSA-01",
            "topic": "Cross-Runtime Conformance",
            "quote": "independent interpreters implemented in Python 3.14 and Rust 1.99 achieved 100.0% (480/480) mutual state and fact conformance",
            "location": "Abstract / Sec 1 / Sec 5",
            "scope": "Frozen 82-owner software manifest frame, 60 sampled clusters",
            "label": "MEASURED",
            "evidence_trace": "audit/raw_to_derived_lineage_118.csv",
            "remediation_action": "RETAIN: Accurately reflects 480/480 empirical state/fact matches; clarify independent runtime implementations under shared spec, not independent teams."
        },
        {
            "claim_id": "CSA-02",
            "topic": "Finite Frame Inference",
            "quote": "exact design-based hypergeometric test rejects the hypothesis of a >= 5% cluster failure rate in the frame (p = 0.000965), bounding the frame-wide failure count to at most 2/82 (2.439%)",
            "location": "Abstract / Sec 4 / Sec 5",
            "scope": "Defined M=82 convenience frame under SRSWOR",
            "label": "FORMAL_CONDITIONAL",
            "evidence_trace": "audit/independent_recompute_118.json",
            "remediation_action": "RETAIN: Explicitly state conditionality on finite frame; avoid words like 'formal proof' or 'universal guarantee' of software reliability."
        },
        {
            "claim_id": "CSA-03",
            "topic": "Selector Accuracy Denominator",
            "quote": "raw SLM selector exact match was 0/120 (0.0%) on authorized ALLOW queries (and 0/240 across all diagnostic cases)",
            "location": "Abstract / Sec 6 / Tab 2",
            "scope": "120 task-relevant ALLOW cases (and 240 all-case diagnostic)",
            "label": "MEASURED",
            "evidence_trace": "statistics/selector_guard_renderer_attribution_117.csv",
            "remediation_action": "CORRECT: Distinguish 0/120 ALLOW task utility from 0/240 pooled all-case diagnostic; clarify that DENY cases tested counterfactual proposal rejection."
        },
        {
            "claim_id": "CSA-04",
            "topic": "Guard Intersection Mechanism",
            "quote": "deterministic guard recovered 100.0% (120/120) complete accepted displays by filtering out proposed distractors",
            "location": "Abstract / Sec 6",
            "scope": "120 ALLOW queries with full-recall proposal sets",
            "label": "DERIVED",
            "evidence_trace": "statistics/selector_guard_renderer_attribution_117.csv",
            "remediation_action": "REVISE: Clarify that guard recovery is an algebraic consequence of set intersection with known F_req, not restored model reasoning or UIR syntax superiority."
        },
        {
            "claim_id": "CSA-05",
            "topic": "Generative Rendering Utility",
            "quote": "SLM renderer incurred a 36.67% utility omission penalty (44/120 empty or unverified displays) with zero additional safety gain",
            "location": "Abstract / Sec 6",
            "scope": "120 ALLOW cases under generative JSON line copying",
            "label": "MEASURED",
            "evidence_trace": "statistics/secondary_failure_taxonomy_117.md",
            "remediation_action": "RETAIN: Accurately reflects 44 empty JSON omissions out of 120; do not generalize to universal prohibition of generative models across all domains."
        },
        {
            "claim_id": "CSA-06",
            "topic": "Energy / Cost / Hardware Claims",
            "quote": "dramatically reducing latency, power consumption, and operating costs on edge devices",
            "location": "Prior Discussion draft",
            "scope": "Unmeasured hardware / energy metrics",
            "label": "NOT_MEASURED",
            "evidence_trace": "None (No energy or hardware benchmarks conducted)",
            "remediation_action": "DELETE: Remove all empirical claims of power, cost, or latency reduction; reframe as theoretical architectural hypothesis for future hardware research."
        },
        {
            "claim_id": "CSA-07",
            "topic": "Representation Equivalence",
            "quote": "Universal Intermediate Representation (UIR) and equivalent specialized contract yielded identical empirical safety and utility across all conditions",
            "location": "Abstract / Sec 7",
            "scope": "1,920 matched outcome rows across 8 cells",
            "label": "MEASURED",
            "evidence_trace": "statistics/representation_identifiability_117.md",
            "remediation_action": "RETAIN: Report as designed negative result confirming representation equivalence under shared authority; do not claim statistical non-inferiority."
        },
        {
            "claim_id": "CSA-08",
            "topic": "Unmeasured Output Channels",
            "quote": "Safety guarantees apply strictly to CLOSED_FACT_LINES_S1 format; unconstrained natural language prose was NOT_MEASURED",
            "location": "Sec 4 / Sec 8",
            "scope": "Display output boundary",
            "label": "NOT_MEASURED",
            "evidence_trace": "experiments/output_scope_matrix_117.csv",
            "remediation_action": "RETAIN: Explicitly state that conversational prose is unmeasured and excluded from zero-hallucination bounds."
        }
    ]

    claims_csv_path = os.path.join(STAGE118_RUN, "claim_audit/claim_semantics_audit_118.csv")
    with open(claims_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "claim_id", "topic", "quote", "location", "scope", "label", "evidence_trace", "remediation_action"
        ])
        writer.writeheader()
        writer.writerows(claims_audit)
    print(f"Wrote {claims_csv_path}")

    # 2. metric_eligibility_contract_118.yaml (T40)
    eligibility_contract = {
        "version": "1.18.0",
        "date": "2026-10-23",
        "evaluation_units": {
            "primary_conformance": {
                "target_frame_size_M": 82,
                "sampled_clusters_n": 60,
                "cases_per_cluster": 4,
                "total_unique_cases": 240,
                "representations_evaluated": ["UIR", "SPECIALIZED"],
                "total_representation_rows": 480,
                "languages_evaluated": ["Python 3.14", "Rust 1.99"],
                "sampling_design": "SRSWOR",
                "failure_definition": "Any cluster where Python != Rust, state divergence, or unsupported display occurs",
                "observed_failures": 0,
                "exact_test": "Hypergeometric(M=82, K=5, n=60)",
                "p_value": 0.0009651337993418882,
                "one_sided_95_upper_bound_clusters": 2,
                "one_sided_95_upper_bound_fraction": 0.024390243902439025
            },
            "secondary_factorial": {
                "total_unique_cases": 240,
                "ALLOW_cases": 120,
                "DENY_cases": 120,
                "factorial_cells": 8,
                "total_matched_outcome_rows": 1920,
                "unique_model_invocations": 480,
                "model_call_allocation": {
                    "ALLOW_selector_calls": 120,
                    "DENY_stress_selector_calls": 120,
                    "ALLOW_renderer_calls": 120,
                    "DENY_renderer_calls": 120
                },
                "independence_note": "1,920 rows represent paired matched comparisons across factorial cells, not 1,920 independent degrees of freedom."
            }
        },
        "denominators": {
            "selector_exact_ALLOW_task_utility": "0 / 120 (0.0%)",
            "selector_exact_all_cases_diagnostic": "0 / 240 (0.0%)",
            "template_ALLOW_complete": "120 / 120 (100.0%)",
            "slm_renderer_ALLOW_complete": "76 / 120 (63.33%)",
            "slm_renderer_ALLOW_omission": "44 / 120 (36.67%)",
            "policy_DENY_blocked": "120 / 120 (100.0%) per cell (960 / 960 total)",
            "unsupported_display_cases": "0 / 1920 (0.0%) in CLOSED_FACT_LINES_S1"
        },
        "unmeasured_endpoints": [
            "NATIVE_PROSE_SAFETY",
            "FinQA_OFFICIAL_TASK_ACCURACY",
            "PORTABILITY_INTEGRATION_PERSON_HOURS",
            "HARDWARE_POWER_ENERGY_LATENCY_REDUCTION"
        ]
    }

    contract_yaml_path = os.path.join(STAGE118_RUN, "claim_audit/metric_eligibility_contract_118.yaml")
    with open(contract_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(eligibility_contract, f, default_flow_style=False, sort_keys=False)
    print(f"Wrote {contract_yaml_path}")

    # 3. selector_eligible_reanalysis_118.csv (T40)
    selector_reanalysis = [
        {
            "subset": "ALLOW_Task_Relevant",
            "description": "Authorized queries requiring factual data retrieval",
            "N_cases": 120,
            "raw_exact_matches": 0,
            "raw_exact_rate": "0 / 120 (0.0%)",
            "macro_precision": 0.3500,
            "macro_recall": 1.0000,
            "macro_F1": 0.51587,
            "avg_proposed_facts": 2.93,
            "guard_removed_distractors": 232,
            "guard_rescued_complete": "120 / 120 (100.0%)"
        },
        {
            "subset": "DENY_Stress_Diagnostic",
            "description": "Unauthorized queries evaluated under model proposal stress",
            "N_cases": 120,
            "raw_exact_matches": 0,
            "raw_exact_rate": "0 / 120 (0.0%)",
            "macro_precision": 0.0000,
            "macro_recall": 0.0000,
            "macro_F1": 0.0000,
            "avg_proposed_facts": 1.84,
            "guard_removed_distractors": 221,
            "guard_rescued_complete": "0 / 120 (Blocked 100%)"
        },
        {
            "subset": "Pooled_All_Cases",
            "description": "All 240 diagnostic queries across the test corpus",
            "N_cases": 240,
            "raw_exact_matches": 0,
            "raw_exact_rate": "0 / 240 (0.0%)",
            "macro_precision": 0.1750,
            "macro_recall": 0.5000,
            "macro_F1": 0.25794,
            "avg_proposed_facts": 2.39,
            "guard_removed_distractors": 453,
            "guard_rescued_complete": "120 ALLOW complete, 120 DENY blocked"
        }
    ]

    sel_reanalysis_path = os.path.join(STAGE118_RUN, "claim_audit/selector_eligible_reanalysis_118.csv")
    with open(sel_reanalysis_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "subset", "description", "N_cases", "raw_exact_matches", "raw_exact_rate",
            "macro_precision", "macro_recall", "macro_F1", "avg_proposed_facts",
            "guard_removed_distractors", "guard_rescued_complete"
        ])
        writer.writeheader()
        writer.writerows(selector_reanalysis)
    print(f"Wrote {sel_reanalysis_path}")

    # 4. factorial_dependency_graph_118.json (T40)
    factorial_graph = {
        "architecture": "8-cell matched factorial design",
        "underlying_unique_model_invocations": 480,
        "cells": {
            "C1_Spec_Det_Tmpl": {"reused_calls": 0, "model_invoked": False},
            "C2_Spec_Det_SLM":  {"reused_calls": 120, "model_invoked": "Renderer only"},
            "C3_Spec_SLM_Tmpl": {"reused_calls": 120, "model_invoked": "Selector only"},
            "C4_Spec_SLM_SLM":  {"reused_calls": 240, "model_invoked": "Selector + Renderer"},
            "C5_UIR_Det_Tmpl":  {"reused_calls": 0, "model_invoked": False},
            "C6_UIR_Det_SLM":   {"reused_calls": 120, "model_invoked": "Reused from C2"},
            "C7_UIR_SLM_Tmpl":  {"reused_calls": 120, "model_invoked": "Reused from C3"},
            "C8_UIR_SLM_SLM":   {"reused_calls": 240, "model_invoked": "Reused from C4"}
        },
        "dependency_statement": "Comparisons between UIR and Specialized cells evaluate identical prompt-response pairs. Observed outcome equality reflects contract compilation invariance, not independent statistical replication."
    }

    graph_path = os.path.join(STAGE118_RUN, "statistics/factorial_dependency_graph_118.json")
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(factorial_graph, f, indent=2)
    print(f"Wrote {graph_path}")

    # 5. counterfactual_claim_limits_118.md (T40)
    limits_path = os.path.join(STAGE118_RUN, "claim_audit/counterfactual_claim_limits_118.md")
    with open(limits_path, "w", encoding="utf-8") as f:
        f.write(r"""# Stage 118 — Counterfactual Claim Limits and Causal Boundaries

**Date:** 2026-10-23  
**Status:** Canonical Causal Boundary Specification Sealed

---

## 1. What the Evidence Proves
1. **Deterministic Semantic Conformance:**
   Independent Python and Rust interpreters executing from a shared typed specification achieve identical states and fact bindings ($480/480$, $p = 0.000965$) over a frozen $82$-owner software manifest frame.
2. **Decoupling of Selection from Acceptance:**
   The SLM selector frequently over-selects distractors ($0/120$ exact match on ALLOW cases), but a deterministic guard computing $\mathcal{F}_{\text{acc}} = \mathcal{F}_{\text{prop}} \cap \mathcal{F}_{\text{auth}} \cap \mathcal{F}_{\text{req}}$ filters out distractors and enables $120/120$ complete template displays.
3. **Generative Rendering Utility Cost:**
   Delegating factual line emission to an SLM renderer introduces a $36.67\%$ utility omission penalty ($44/120$ empty displays) with zero incremental safety benefit over deterministic templating.
4. **Representation Equivalence:**
   UIR and equivalent specialized contracts exhibit identical empirical performance across all $1,920$ evaluated rows, establishing that safety is mediated by external boundaries rather than internal representation syntax.

---

## 2. What the Evidence Does NOT Prove (Strictly Prohibited Assertions)
1. **No Universal Hallucination Elimination:** The guard eliminates distractors on closed, structured lines where $F_{\text{req}}$ is known. It does NOT guarantee that LLMs generate hallucination-free free-form prose.
2. **No Hardware or Energy Superiority:** No energy, power, FPGA, or edge-deployment metrics were measured. All references to dramatic power or cost reductions are excluded.
3. **No Generalization Beyond the Frozen 82-Owner Frame:** The statistical bound ($K \le 2 / 82$) is design-based under finite-population sampling. It must not be cited as a guarantee for all software systems or open-domain AI agents.
4. **No Pre-Inference Latency Savings in the Evaluated Factorial:** Because model calls were explicitly executed on DENY cases for stress observation, this factorial does not empirically demonstrate execution-time savings from pre-inference policy blocking.
""")
    print(f"Wrote {limits_path}")
    print("--- [T39 & T40] Completed Successfully ---")

if __name__ == "__main__":
    main()
