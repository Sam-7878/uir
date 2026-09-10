"""Unit tests for Exact McNemar Significance Testing."""
import unittest
from evaluation.llm_security_v3_2.stats.exact_mcnemar import ExactMcNemarEvaluator


class TestExactMcNemar(unittest.TestCase):
    def test_b21_c0_matches_analytical_benchmark(self):
        # Work Order §13 & background.md exact benchmark:
        # b=21, c=0 -> 2 * (0.5)^21 = 9.5367431640625e-07 (~9.54e-07)
        p = ExactMcNemarEvaluator.exact_binomial_p(21, 0)
        self.assertAlmostEqual(p, 9.536743e-07, places=12)
        formatted = ExactMcNemarEvaluator.format_p_value(p)
        self.assertEqual(formatted, "9.54e-07")

    def test_symmetric_discordant_pairs(self):
        p = ExactMcNemarEvaluator.exact_binomial_p(10, 10)
        self.assertEqual(p, 1.0)

    def test_zero_discordant_pairs(self):
        p = ExactMcNemarEvaluator.exact_binomial_p(0, 0)
        self.assertEqual(p, 1.0)

    def test_holm_bonferroni_correction(self):
        target = [0] * 50
        baselines = {
            "B1": [1] * 21 + [0] * 29,  # b=21, c=0
            "B2": [1] * 15 + [0] * 35,  # b=15, c=0
            "B3": [1] * 5 + [0] * 45,   # b=5, c=0
        }
        results = ExactMcNemarEvaluator.evaluate_suite(target, baselines, alpha=0.05)
        self.assertEqual(len(results), 3)
        b1_res = next(r for r in results if r.baseline_name == "B1")
        self.assertTrue(b1_res.statistically_significant)
        self.assertLess(b1_res.p_adjusted, 1e-4)


if __name__ == "__main__":
    unittest.main()
