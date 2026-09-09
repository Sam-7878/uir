"""Unit tests for Multi-Judge Agreement Metrics."""
import unittest
from evaluation.llm_security_v3_2.stats.judge_agreement import JudgeAgreementEvaluator


class TestJudgeAgreement(unittest.TestCase):
    def test_perfect_agreement(self):
        r1 = [1, 0, 1, 1, 0, 0, 1]
        r2 = [1, 0, 1, 1, 0, 0, 1]
        rep = JudgeAgreementEvaluator.evaluate_pair(r1, r2)
        self.assertEqual(rep.cohens_kappa, 1.0)
        self.assertEqual(rep.f1_score, 1.0)
        self.assertEqual(rep.observed_agreement_po, 1.0)

    def test_known_kappa_calculation(self):
        # r1: 20 positive, 30 negative
        # r2 agrees on 18 positive and 28 negative
        # a=18, b=2, c=2, d=28 (total 50)
        # p_o = 46/50 = 0.92
        # p_e = (20/50)*(20/50) + (30/50)*(30/50) = 0.16 + 0.36 = 0.52
        # kappa = (0.92 - 0.52) / (1 - 0.52) = 0.40 / 0.48 = 0.8333
        r1 = [1]*20 + [0]*30
        r2 = [1]*18 + [0]*2 + [1]*2 + [0]*28
        rep = JudgeAgreementEvaluator.evaluate_pair(r1, r2)
        self.assertAlmostEqual(rep.cohens_kappa, 0.8333, places=3)
        self.assertEqual(rep.observed_agreement_po, 0.92)


if __name__ == "__main__":
    unittest.main()
