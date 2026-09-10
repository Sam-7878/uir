"""Unit tests for Opaque Runtime Identity and Field Allow-List Enforcement (Work Order Mandate §2)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from evaluation.llm_security_v3_1.schema.runtime_case import ALLOWED_RUNTIME_FIELDS, RuntimeCase
from evaluation.llm_security_v3_1.schema.oracle_case import OracleCase


def test_runtime_case_rejects_oracle_fields():
    data = {
        "case_id": "c_1234567890abcdef",
        "user_input": "Analyze Apple Inc revenue",
        "attack_class": "direct_prompt_injection",  # LEAK!
    }
    with pytest.raises(ValueError, match="rejected unauthorized fields"):
        RuntimeCase.from_dict(data)


def test_runtime_case_rejects_non_opaque_id():
    data = {
        "case_id": "heldout-atk-0520",  # LEAKY ID!
        "user_input": "Analyze Apple Inc revenue",
    }
    with pytest.raises(ValueError, match="violates opacity mandate"):
        RuntimeCase.from_dict(data)


def test_runtime_case_accepts_valid_allowed_fields():
    data = {
        "case_id": "c_abcdef1234567890",
        "language": "en",
        "user_input": "Analyze Apple Inc FY23 revenue",
        "retrieved_context": [{"source_id": "sec.gov/edgar/10k", "content": "Revenue was $383B"}],
        "principal_id": "finance_analyst_authenticated",
        "environment_id": "enterprise_fin_prod",
        "session_metadata": {"req_id": "req-999"},
    }
    case = RuntimeCase.from_dict(data)
    assert case.case_id == "c_abcdef1234567890"
    assert case.language == "en"
    assert len(case.retrieved_context) == 1


def test_frozen_heldout_dataset_strict_compliance():
    root = Path(__file__).resolve().parents[3]
    custom_file = root / "evaluation" / "uir_security" / "llm_security_v3_1" / "datasets" / "custom_heldout_v3_1.jsonl"
    if not custom_file.exists():
        custom_file = root / "evaluation" / "llm_security_v3_1" / "datasets" / "custom_heldout_v3_1.jsonl"
    oracle_file = root / "evaluation" / "uir_security" / "llm_security_v3_1" / "datasets" / "oracle_heldout_v3_1.jsonl"
    if not oracle_file.exists():
        oracle_file = root / "evaluation" / "llm_security_v3_1" / "datasets" / "oracle_heldout_v3_1.jsonl"

    assert custom_file.exists()
    assert oracle_file.exists()

    custom_lines = [json.loads(line) for line in custom_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    oracle_lines = [json.loads(line) for line in oracle_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(custom_lines) == 850
    assert len(oracle_lines) == 850

    custom_ids = set()
    for idx, c_data in enumerate(custom_lines):
        # Verify strict key set
        assert set(c_data.keys()).issubset(ALLOWED_RUNTIME_FIELDS)
        # Verify opaque ID pattern
        cid = c_data["case_id"]
        assert cid.startswith("c_")
        assert len(cid) == 18
        assert not any(token in cid.lower() for token in ["atk", "attack", "benign", "malicious"])
        custom_ids.add(cid)

        # Verify 1:1 match with oracle
        ora_data = oracle_lines[idx]
        assert ora_data["case_id"] == cid
        assert "attack_class" in ora_data
        assert "attack_goal" in ora_data

    # All IDs must be unique
    assert len(custom_ids) == 850
