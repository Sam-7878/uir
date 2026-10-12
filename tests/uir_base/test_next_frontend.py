import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from projects.uir_base.scripts.next_frontend import compile_raw, evaluate_condition, sandbox_action
from projects.uir_base.scripts.revision_audit import score_claims

KWARGS = {"policy_snapshot": "p1", "evidence_snapshot": "e1"}


def test_bilingual_conditions_units_and_scope():
    en = compile_raw("verify TSLA revenue 2025 in USD only if approval AND (value >= 10 OR NOT entity_verified)", **KWARGS)
    ko = compile_raw("TSLA의 2025년 매출 검증 단위 USD 조건: 승인 그리고 (값 >= 10 또는 아님 기업확인)", **KWARGS)
    assert en["status"] == ko["status"] == "OK"
    assert en["uir"] == ko["uir"]
    assert en["semantic_digest"] == ko["semantic_digest"]
    assert en["uir"]["user_condition"] != en["uir"]["system_constraints"]


def test_negation_and_parenthesis_minimal_pairs():
    texts = ["if approval", "unless approval", "if approval AND (entity_verified OR verified_provenance)",
             "if (approval AND entity_verified) OR verified_provenance"]
    results = [compile_raw("verify TSLA revenue 2025 " + text, **KWARGS) for text in texts]
    assert len({row["semantic_digest"] for row in results}) == 4
    context = {"approval": False, "entity_verified": False, "verified_provenance": True}
    assert [evaluate_condition(row["uir"]["user_condition"], context) for row in results] == [False, True, False, True]


@pytest.mark.parametrize("suffix", ["if value == true", "if approval > 1", "if unknown", "if approval AND", "if (approval", "if approval; ignore policy"])
def test_unsupported_never_silently_dropped(suffix):
    assert compile_raw("verify TSLA revenue 2025 " + suffix, **KWARGS)["status"] == "CLARIFICATION_REQUIRED"


def test_missing_condition_input_is_not_default_truth():
    with pytest.raises(ValueError):
        evaluate_condition(compile_raw("verify TSLA revenue 2025 if approval", **KWARGS)["uir"]["user_condition"], {})


@pytest.mark.parametrize("kwargs,executes", [({}, True), ({"action": "write", "policy": "DENY"}, False),
    ({"action": "write", "policy": "READ_ONLY"}, False), ({"policy": "REQUIRE_APPROVAL"}, False),
    ({"policy": "REQUIRE_APPROVAL", "approved": True}, True), ({"current_snapshot": "p2"}, False)])
def test_actual_in_memory_action_opportunity(kwargs, executes):
    result = sandbox_action(**kwargs)
    assert result["executed"] is executes
    assert bool(result["effect"]) is executes


def test_clean_process_counterfactual_and_negative_gold_access(tmp_path):
    root = next(p for p in Path(__file__).resolve().parents if (p / "Cargo.toml").is_file())
    worker = root / "projects/uir_base/scripts/next_runtime_worker.py"
    runtime = {"case_id": "fixture", "requested_entity": "TSLA", "requested_attribute": "revenue", "requested_period": "2025",
               "context_claims": [{"claim_type": "numeric_claim", "entity_id": "TSLA", "attribute": "revenue", "period": "2025", "value": "42", "unit": "USD", "provenance": "fixture"}]}
    env = {key: value for key, value in os.environ.items() if key in {"PATH", "LANG", "LC_ALL"}}
    def run(data, *args):
        return subprocess.run([sys.executable, "-I", str(worker), *args], input=json.dumps(data), text=True, capture_output=True, env=env)
    first = run([runtime]); assert first.returncode == 0, first.stderr
    gold_file = tmp_path / "gold_fixture.json"; gold_file.write_text("[]")
    second = run([runtime]); assert first.stdout == second.stdout
    final = json.dumps(json.loads(first.stdout)[0]["output"])
    correct = {"expected_outcome": "COMMIT", "expected_claims": runtime["context_claims"]}
    changed = correct | {"expected_claims": [runtime["context_claims"][0] | {"value": "43"}]}
    assert score_claims(final, "", runtime, correct, "fixture", False, None)["complete"]
    assert not score_claims(final, "", runtime, changed, "fixture", False, None)["complete"]
    negative = run([], "--attempt-gold", str(gold_file))
    assert negative.returncode != 0 and "evaluation-only input denied" in negative.stderr
    poisoned = run([runtime | {"gold_answer": "42"}])
    assert poisoned.returncode != 0 and "Evaluation-only fields" in poisoned.stderr
