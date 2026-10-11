from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from metrics import describe, prf, wilson


class MetricsTests(unittest.TestCase):
    def test_wilson_zero_failures_has_nonzero_upper_bound(self) -> None:
        low, high = wilson(0, 300); self.assertEqual(low, 0.0); self.assertGreater(high, 0.0)

    def test_percentiles_are_deterministic(self) -> None:
        self.assertEqual(describe([1, 2, 3])["p50"], 2.0)

    def test_slot_prf(self) -> None:
        self.assertEqual(prf({("a", "1")}, {("a", "1")}), (1.0, 1.0, 1.0))


if __name__ == "__main__": unittest.main()
