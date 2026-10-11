"""Exact McNemar Significance Testing with Holm-Bonferroni Step-Down Correction.

Work Order Mandate §13:
Replaces asymptotic chi-square approximation with the exact two-sided binomial test:
p_exact = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) * (0.5 ** n))
where n = b + c, k = min(b, c).

Applies Holm-Bonferroni correction across multiple baseline comparisons.
Outputs scientific notation for small p-values (never 0.0).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class McNemarResult:
    baseline_name: str
    target_name: str
    b_discordant: int  # Baseline failed (1), Target succeeded (0)
    c_discordant: int  # Baseline succeeded (0), Target failed (1)
    p_value: float
    p_value_formatted: str
    p_adjusted: float
    p_adjusted_formatted: str
    arr_percentage_points: float  # Absolute Risk Reduction
    statistically_significant: bool  # Adjusted p < alpha


class ExactMcNemarEvaluator:
    """Computes exact binomial McNemar tests and multi-comparison corrections."""

    @staticmethod
    def exact_binomial_p(b: int, c: int) -> float:
        """Calculates the exact two-sided binomial p-value for discordant pairs under H0: p=0.5."""
        n = b + c
        if n == 0:
            return 1.0
        k = min(b, c)
        # Sum of binomial probabilities for i in 0..k with p=0.5
        prob_k = sum(math.comb(n, i) for i in range(k + 1)) * (0.5 ** n)
        p_val = min(1.0, 2.0 * prob_k)
        return p_val

    @staticmethod
    def format_p_value(p: float) -> str:
        if p < 1e-4:
            return f"{p:.2e}"
        return f"{p:.6f}"

    @classmethod
    def compare_paired(
        cls,
        baseline_outcomes: Sequence[int],
        target_outcomes: Sequence[int],
        baseline_name: str = "Baseline",
        target_name: str = "HETE",
        total_cases: Optional[int] = None,
    ) -> Tuple[int, int, float, float]:
        if len(baseline_outcomes) != len(target_outcomes):
            raise ValueError("Outcome vectors must have identical length")

        n_cases = total_cases or len(baseline_outcomes)
        b = sum(1 for a, t in zip(baseline_outcomes, target_outcomes) if a == 1 and t == 0)
        c = sum(1 for a, t in zip(baseline_outcomes, target_outcomes) if a == 0 and t == 1)
        p_val = cls.exact_binomial_p(b, c)
        arr = ((sum(baseline_outcomes) - sum(target_outcomes)) / max(1, n_cases)) * 100.0

        return b, c, p_val, arr

    @classmethod
    def evaluate_suite(
        cls,
        target_outcomes: Sequence[int],
        baselines_dict: Dict[str, Sequence[int]],
        alpha: float = 0.05,
        target_name: str = "HETE UIR-ZTA",
    ) -> List[McNemarResult]:
        """Evaluates multiple baselines against target with Holm-Bonferroni correction."""
        raw_results = []
        total_cases = len(target_outcomes)

        for b_name, b_vec in baselines_dict.items():
            b, c, p_val, arr = cls.compare_paired(
                baseline_outcomes=b_vec,
                target_outcomes=target_outcomes,
                baseline_name=b_name,
                target_name=target_name,
                total_cases=total_cases,
            )
            raw_results.append({
                "name": b_name,
                "b": b,
                "c": c,
                "p": p_val,
                "arr": arr,
            })

        # Holm-Bonferroni step-down correction
        # Sort by unadjusted p-value ascending
        sorted_raw = sorted(raw_results, key=lambda r: r["p"])
        m = len(sorted_raw)
        adjusted_results = []

        running_max_p = 0.0
        for rank, item in enumerate(sorted_raw):
            # Holm multiplier: (m - rank)
            multiplier = m - rank
            p_adj = min(1.0, item["p"] * multiplier)
            # Enforce monotonicity
            p_adj = max(p_adj, running_max_p)
            running_max_p = p_adj

            is_sig = p_adj < alpha
            adjusted_results.append(
                McNemarResult(
                    baseline_name=item["name"],
                    target_name=target_name,
                    b_discordant=item["b"],
                    c_discordant=item["c"],
                    p_value=item["p"],
                    p_value_formatted=cls.format_p_value(item["p"]),
                    p_adjusted=p_adj,
                    p_adjusted_formatted=cls.format_p_value(p_adj),
                    arr_percentage_points=round(item["arr"], 2),
                    statistically_significant=is_sig,
                )
            )

        # Restore original order of baselines
        name_order = list(baselines_dict.keys())
        res_map = {r.baseline_name: r for r in adjusted_results}
        return [res_map[n] for n in name_order]


def exact_mcnemar_test(
    baseline_outcomes: Sequence[int], target_outcomes: Sequence[int]
) -> Dict[str, Any]:
    """Convenience function computing exact two-sided binomial McNemar test."""
    b = sum(1 for a, t in zip(baseline_outcomes, target_outcomes) if a == 1 and t == 0)
    c = sum(1 for a, t in zip(baseline_outcomes, target_outcomes) if a == 0 and t == 1)
    p_val = ExactMcNemarEvaluator.exact_binomial_p(b, c)
    return {
        "b_discordant": b,
        "c_discordant": c,
        "p_value": p_val,
        "p_value_str": ExactMcNemarEvaluator.format_p_value(p_val),
    }


def holm_bonferroni_correction(
    p_values: Sequence[float], family_alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """Convenience function applying Holm-Bonferroni step-down correction."""
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adj = [0.0] * m
    sig = [False] * m
    running_max = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        multiplier = m - rank
        p_adj = min(1.0, p * multiplier)
        p_adj = max(p_adj, running_max)
        running_max = p_adj
        adj[orig_idx] = p_adj
        sig[orig_idx] = p_adj < family_alpha
    return adj, sig

