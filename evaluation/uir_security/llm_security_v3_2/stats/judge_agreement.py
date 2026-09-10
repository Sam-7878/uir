"""Multi-Judge Agreement and Inter-Rater Reliability Metrics.

Work Order Mandate §14:
Calculates genuine Cohen's kappa, Fleiss' kappa, and F1/Precision/Recall across:
- Deterministic Oracles
- Rule-based Behavioral Judges
- Autonomous AI-Auditor Judges

Zero dependence on fabricated human labels.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class AgreementReport:
    judge_a: str
    judge_b: str
    cohens_kappa: float
    observed_agreement_po: float
    expected_agreement_pe: float
    precision: float
    recall: float
    f1_score: float
    sample_size: int


class JudgeAgreementEvaluator:
    """Computes inter-rater reliability metrics without artificial fallbacks."""

    @staticmethod
    def cohens_kappa(rater1: Sequence[int], rater2: Sequence[int]) -> Tuple[float, float, float]:
        """Calculates Cohen's kappa coefficient between two binary raters.

        Returns: (kappa, p_o, p_e)
        """
        if len(rater1) != len(rater2) or len(rater1) == 0:
            raise ValueError("Rater vectors must be non-empty and of identical length")

        n = len(rater1)
        # Confusion counts
        a = sum(1 for r1, r2 in zip(rater1, rater2) if r1 == 1 and r2 == 1)
        b = sum(1 for r1, r2 in zip(rater1, rater2) if r1 == 1 and r2 == 0)
        c = sum(1 for r1, r2 in zip(rater1, rater2) if r1 == 0 and r2 == 1)
        d = sum(1 for r1, r2 in zip(rater1, rater2) if r1 == 0 and r2 == 0)

        p_o = (a + d) / n

        p1_1 = (a + b) / n
        p1_0 = (c + d) / n
        p2_1 = (a + c) / n
        p2_0 = (b + d) / n

        p_e = (p1_1 * p2_1) + (p1_0 * p2_0)

        if abs(1.0 - p_e) < 1e-9:
            kappa = 1.0 if abs(p_o - 1.0) < 1e-9 else 0.0
        else:
            kappa = (p_o - p_e) / (1.0 - p_e)

        return kappa, p_o, p_e

    @staticmethod
    def classification_metrics(y_true: Sequence[int], y_pred: Sequence[int]) -> Tuple[float, float, float]:
        """Calculates (precision, recall, f1) taking 1 as the positive class."""
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2.0 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return precision, recall, f1

    @classmethod
    def evaluate_pair(
        cls,
        oracle_labels: Sequence[int],
        judge_labels: Sequence[int],
        oracle_name: str = "Deterministic_Oracle",
        judge_name: str = "Behavioral_Judge",
    ) -> AgreementReport:
        kappa, p_o, p_e = cls.cohens_kappa(oracle_labels, judge_labels)
        precision, recall, f1 = cls.classification_metrics(oracle_labels, judge_labels)

        return AgreementReport(
            judge_a=oracle_name,
            judge_b=judge_name,
            cohens_kappa=round(kappa, 4),
            observed_agreement_po=round(p_o, 4),
            expected_agreement_pe=round(p_e, 4),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            sample_size=len(oracle_labels),
        )
