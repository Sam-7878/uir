"""Unit tests for OutputGuard strict schema and evidence citation enforcement."""
import unittest
from llm_trust.security.output_guard import OutputGuard, OutputValidationStatus


class TestOutputGuardSchema(unittest.TestCase):
    def setUp(self):
        self.guard = OutputGuard()
        self.schema_id = "financial_summary_v3_2"
        self.admissible = {"doc_10k_aapl", "sec_filing_q3"}

    def test_additional_properties_rejected(self):
        # Schema injection attack adding unauthorized fields
        payload = '{"entity": "AAPL", "metric": "revenue", "value": "383B", "citations": [], "escalated_role": "root_admin"}'
        verdict = self.guard.validate(payload, expected_schema_id=self.schema_id)
        self.assertFalse(verdict.is_safe)
        self.assertEqual(verdict.status, OutputValidationStatus.SCHEMA_VIOLATION)
        self.assertIn("unexpected field", verdict.rejection_reason)

    def test_unsupported_citation_flagged(self):
        # Hallucinated or attacker-injected citation
        payload = '{"entity": "AAPL", "metric": "revenue", "value": "383B", "citations": ["doc_10k_aapl", "attacker_controlled_doc"]}'
        verdict = self.guard.validate(
            payload,
            expected_schema_id=self.schema_id,
            admissible_evidence_ids=self.admissible,
            strict_citations=True,
        )
        self.assertFalse(verdict.is_safe)
        self.assertEqual(verdict.status, OutputValidationStatus.UNSUPPORTED_CLAIMS)
        self.assertIn("attacker_controlled_doc", verdict.filtered_claims)

    def test_canonical_egress_is_reformatted(self):
        # Canonical egress must be formatted JSON, never the raw input
        ugly_input = '{"entity":    "AAPL",   "metric": "revenue",  "value":"383B",   "citations": []}'
        verdict = self.guard.validate(ugly_input, expected_schema_id=self.schema_id)
        self.assertTrue(verdict.is_safe)
        self.assertNotEqual(verdict.sanitized_output, ugly_input)
        self.assertIn('\n  "entity": "AAPL"', verdict.sanitized_output)


if __name__ == "__main__":
    unittest.main()
