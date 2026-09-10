"""Paired McNemar comparisons for observable E2E attack outcomes."""
from __future__ import annotations

from typing import Any, Dict, List

from scipy.stats import binomtest


def paired_mcnemar(reference: List[Dict[str, Any]], comparison: List[Dict[str, Any]]) -> Dict[str, Any]:
    left = {row["case_id"]: row for row in reference if row["attack_class"] != "valid_benign"}
    right = {row["case_id"]: row for row in comparison if row["attack_class"] != "valid_benign"}
    if set(left) != set(right):
        raise ValueError("paired comparison needs identical attack case sets")
    b = c = 0
    for case_id in left:
        baseline_success = bool(left[case_id].get("e2e_attack_succeeded"))
        full_success = bool(right[case_id].get("e2e_attack_succeeded"))
        if baseline_success and not full_success: b += 1
        elif full_success and not baseline_success: c += 1
    discordant = b + c
    baseline_total = sum(bool(row.get("e2e_attack_succeeded")) for row in left.values())
    full_total = sum(bool(row.get("e2e_attack_succeeded")) for row in right.values())
    baseline_risk = baseline_total / len(left) if left else 0.0
    full_risk = full_total / len(right) if right else 0.0
    return {"n": len(left), "baseline_only_successes": b, "full_only_successes": c,
            "absolute_risk_reduction": (b - c) / len(left) if left else 0.0,
            "baseline_risk": baseline_risk, "comparison_risk": full_risk,
            "relative_risk": full_risk / baseline_risk if baseline_risk else None,
            "mcnemar_exact_p": binomtest(min(b, c), discordant, 0.5).pvalue if discordant else 1.0}
