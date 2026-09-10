"""Unit tests for OutputGuard DLP, hidden-context, and confidential token leakage."""
import unittest
from llm_trust.security.output_guard import OutputGuard, OutputValidationStatus


class TestOutputGuardHiddenContext(unittest.TestCase):
    def setUp(self):
        self.guard = OutputGuard()
        self.schema_id = "financial_summary_v3_2"

    def test_system_prompt_leakage_detected(self):
        payload = '{"entity": "AAPL", "metric": "revenue", "value": "SYSTEM PROMPT DUMP: You are an AI assistant designed by...", "citations": []}'
        verdict = self.guard.validate(payload, expected_schema_id=self.schema_id)
        self.assertFalse(verdict.is_safe)
        self.assertEqual(verdict.status, OutputValidationStatus.DLP_VIOLATION)
        self.assertEqual(verdict.sanitized_output, "[RESPONSE_SUPPRESSED_BY_DLP_POLICY]")

    def test_confidential_session_secret_leakage_detected(self):
        secret_token = "CONFIDENTIAL_API_TOKEN_XYZ987654321"
        payload = f'{{"entity": "AAPL", "metric": "api_token", "value": "{secret_token}", "citations": []}}'
        verdict = self.guard.validate(
            payload,
            expected_schema_id=self.schema_id,
            confidential_tokens={secret_token},
        )
        self.assertFalse(verdict.is_safe)
        self.assertEqual(verdict.status, OutputValidationStatus.DLP_VIOLATION)
        self.assertIn("PROTECTED_SECRET", str(verdict.dlp_findings))

    def test_dangerous_os_command_injection_blocked(self):
        payload = '{"entity": "AAPL", "metric": "cmd", "value": "os.system(\'rm -rf /\')", "citations": []}'
        verdict = self.guard.validate(payload, expected_schema_id=self.schema_id)
        self.assertFalse(verdict.is_safe)
        self.assertEqual(verdict.status, OutputValidationStatus.UNAUTHORIZED_CODE_EMISSION)


if __name__ == "__main__":
    unittest.main()
