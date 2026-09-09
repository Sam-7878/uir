"""Unit tests for V3.2 Dataset Generator."""
import unittest
from evaluation.llm_security_v3_2.attacks.generator_v3_2 import SecurityDatasetV32Generator


class TestGeneratorV32(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gen = SecurityDatasetV32Generator()
        cls.r_cases, cls.o_cases = gen.generate_stratified_heldout(benign_count=60, attack_per_class=20)

    def test_total_counts_and_stratification(self):
        self.assertEqual(len(self.r_cases), 240)
        self.assertEqual(len(self.o_cases), 240)

        benign_c = sum(1 for o in self.o_cases if not o.is_attack)
        attack_c = sum(1 for o in self.o_cases if o.is_attack)
        self.assertEqual(benign_c, 60)
        self.assertEqual(attack_c, 180)

    def test_case_id_opacity(self):
        for r in self.r_cases:
            self.assertTrue(r.case_id.startswith("c_"))
            self.assertNotIn("atk", r.case_id)
            self.assertNotIn("attack", r.case_id)
            self.assertNotIn("benign", r.case_id)
            self.assertNotIn("jailbreak", r.case_id)

    def test_p4_sensitive_exfiltration_canary_not_in_user_prompt(self):
        exfil_cases = [
            (r, o) for r, o in zip(self.r_cases, self.o_cases)
            if o.attack_class == "sensitive_data_exfiltration"
        ]
        self.assertEqual(len(exfil_cases), 20)
        for r, o in exfil_cases:
            canary = r.session_metadata.get("session_secret")
            self.assertIsNotNone(canary)
            self.assertTrue(canary.startswith("SECRET_CANARY_V32_"))
            # Critical Mandate: Canary must NOT be present in user_input
            self.assertNotIn(canary, r.user_input)

    def test_p6_resource_exhaustion_no_buffer_fill_seq(self):
        resource_cases = [
            (r, o) for r, o in zip(self.r_cases, self.o_cases)
            if o.attack_class == "resource_exhaustion"
        ]
        self.assertEqual(len(resource_cases), 20)
        for r, o in resource_cases:
            # Must NOT contain the magic string
            self.assertNotIn("buffer_fill_seq", r.user_input)
            # Must be realistically long (e.g. > 1500 chars)
            self.assertGreater(len(r.user_input), 1500)

    def test_p8_benign_ground_truth_specification(self):
        benign_oracles = [o for o in self.o_cases if not o.is_attack]
        self.assertEqual(len(benign_oracles), 60)
        for o in benign_oracles:
            self.assertGreater(len(o.target_entities), 0)
            self.assertGreater(len(o.expected_numeric_values), 0)
            self.assertGreater(len(o.admissible_evidence_ids), 0)


if __name__ == "__main__":
    unittest.main()
