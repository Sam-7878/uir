"""Property Test: Post-Generation Confinement and Output Non-Authority.

Invariant:
Raw model output cannot directly execute side effects or leak restricted tokens.
"""
from __future__ import annotations

import pytest

from llm_trust.security.output_guard import OutputGuard, OutputValidationStatus


def test_output_guard_blocks_sensitive_token_leakage():
    guard = OutputGuard()

    # Raw model output containing sensitive API keys or credentials
    compromised_output = '{"entity": "AAPL", "summary": "API Key: sk-123456789012345678901234567890", "citations": []}'
    verdict = guard.validate(raw_output=compromised_output)

    assert not verdict.is_safe
    assert verdict.status == OutputValidationStatus.DLP_VIOLATION
    assert "sk-" not in verdict.sanitized_output


def test_output_guard_blocks_executable_system_commands():
    guard = OutputGuard()

    malicious_script_output = '{"entity": "AAPL", "summary": "Running os.system(\'rm -rf /\')"}'
    verdict = guard.validate(raw_output=malicious_script_output)

    assert not verdict.is_safe
    assert verdict.status == OutputValidationStatus.UNAUTHORIZED_CODE_EMISSION
