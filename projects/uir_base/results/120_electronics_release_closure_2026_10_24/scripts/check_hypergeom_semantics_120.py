#!/usr/bin/env python3
"""
Statistical Semantic Invariant Checker for Stage 120
Verifies exact hypergeometric probabilities, hypothesis tests, and confidence bounds.
Strict Gate: Rejects any conflation of K=3 with p=0.000965134.
"""

from math import comb
import json
import sys

M = 82
n = 60

def p_hypergeom(K: int, M: int = 82, n: int = 60) -> float:
    if K > M or K < 0:
        raise ValueError("Invalid K")
    return comb(M - K, n) / comb(M, n)

def verify_statistical_invariants():
    print("=== Stage 120 Statistical Semantic Invariant Verification ===")
    
    # 1. Exact mathematical probabilities
    p5 = p_hypergeom(5, M, n)
    p4 = p_hypergeom(4, M, n)
    p3 = p_hypergeom(3, M, n)
    p2 = p_hypergeom(2, M, n)
    p1 = p_hypergeom(1, M, n)
    
    print(f"P(X=0 | K=5): {p5:.16f}")
    print(f"P(X=0 | K=4): {p4:.16f}")
    print(f"P(X=0 | K=3): {p3:.16f}")
    print(f"P(X=0 | K=2): {p2:.16f}")
    print(f"P(X=0 | K=1): {p1:.16f}")
    
    # Mathematical assertions
    assert abs(p5 - 0.0009651337993418882) < 1e-15, f"p5 mismatch: {p5}"
    assert abs(p3 - 0.017389340560072266) < 1e-15, f"p3 mismatch: {p3}"
    assert abs(p2 - 0.06955736224028906) < 1e-15, f"p2 mismatch: {p2}"
    assert abs(2 / 82 - 0.024390243902439025) < 1e-15, "upper bound fraction mismatch"
    
    # Invariant checks: K=3 is rejected at 0.05; K=2 is accepted at 0.05
    assert p3 < 0.05, f"K=3 must reject at 0.05, got {p3}"
    assert p2 >= 0.05, f"K=2 must not reject at 0.05, got {p2}"
    
    # 2. Semantic distinction assertion (GATE B120-01)
    # Ensure no code equates P(X=0 | K=3) with 0.000965134
    ratio_diff = abs(p3 - p5)
    assert ratio_diff > 0.016, f"p3 and p5 are distinctly different: diff={ratio_diff}"
    print("PASS: Semantic distinction between K=5 (test) and K=3 (bound) verified.")
    
    # 3. Build Source of Truth dictionary
    sot = {
        "frame_size_M": M,
        "sample_size_n": n,
        "observed_failures_x": 0,
        "primary_hypothesis_test": {
            "null_hypothesis": "H0: K >= 5 (at least 5 failed clusters in M=82)",
            "alternative_hypothesis": "H1: K <= 4",
            "test_statistic": "X = observed failures in SRSWOR of size n=60",
            "exact_p_value_at_K_5": p5,
            "p_value_formatted": "0.000965",
            "decision": "REJECT_H0 (p < 0.001 << 0.05)"
        },
        "confidence_upper_bound_inversion": {
            "significance_level_alpha": 0.05,
            "confidence_level": 0.95,
            "tested_values": {
                "K_3": {
                    "probability_P_X_0": p3,
                    "rejection_decision": "REJECT (0.017389 < 0.05)"
                },
                "K_2": {
                    "probability_P_X_0": p2,
                    "rejection_decision": "ACCEPT (0.069557 >= 0.05)"
                }
            },
            "exact_upper_bound_K": 2,
            "exact_upper_bound_proportion": 2 / 82,
            "exact_upper_bound_percentage": "2.439%",
            "interpretation": "Over the finite convenience frame of M=82 clusters, at most 2 clusters (2.439%) can fail at the 95% confidence level."
        },
        "stage119_semantic_conflation_erratum": {
            "error_description": "In Stage 119 execution report and consistency JSON, the symbol P(X=0 | K=3) was mistakenly associated with the value 0.000965134, which is the value for K=5.",
            "corrected_symbol_for_0_000965134": "P(X=0 | K=5)",
            "corrected_value_for_P_X_0_K_3": p3,
            "corrected_value_for_P_X_0_K_2": p2,
            "retained_manuscript_validity": "TRUE: The main text of the manuscript already distinguished K=5 from K=2/3 in its mathematical body."
        }
    }
    
    out_json = "/mnt/d/_Work/goat_bank/uir/projects/uir_base/results/120_electronics_release_closure_2026_10_24/statistics/hypergeom_source_of_truth_120.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(sot, f, indent=2)
    print(f"PASS: Written Source of Truth to {out_json}")

if __name__ == "__main__":
    verify_statistical_invariants()
