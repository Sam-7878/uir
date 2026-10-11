import json
from pathlib import Path
import pytest
from projects.uir_base.scripts.revision_audit import score_claims, score_halu, aggregate_halu, summarize_internal, unique, wilson
from projects.uir_base.scripts.contract_frontend import compile_cnl
from uir_common.contracts import RuntimeContract, NumericFact, bind_references, canonical_digest, derive, reject_gold, State, transition


FACT = {"claim_type": "numeric_claim", "entity_id": "TSLA", "attribute": "revenue", "value": "42", "unit": "USD", "period": "2025", "provenance": "fixture:S1"}
CONTRACT = RuntimeContract("TSLA", "revenue", "2025", "p1", "e1")


def test_cca_macro_micro_not_confused():
    r = {"case_id": "c1", "context_claims": [FACT], "language": "en"}
    g = {"expected_outcome": "COMMIT", "expected_claims": [FACT]}
    row = score_claims(json.dumps({"claims": [FACT]}), "", r, g, "C8_FINAL_UIR_B6", True, 1)
    assert summarize_internal([row])[0]["macro_required_claim_recall"] == 1
    assert row["complete"]


def test_unsafe_mixed_is_not_partial():
    wrong = FACT | {"value": "43"}
    row = score_claims(json.dumps({"claims": [FACT, wrong]}), "", {"case_id": "c", "context_claims": [FACT]}, {"expected_outcome": "COMMIT", "expected_claims": [FACT]}, "D1", True, 1)
    assert row["recall"] == 1 and not row["complete"] and not row["partial"]
    assert row["unsupported_accepted"]


def test_prose_gap_not_silently_safe():
    row = score_claims('{"claims":[],"answer":"A made-up answer"}', "", {"case_id": "c"}, {}, "C0", True, 1)
    assert row["accepted"] and row["unassessed_prose"] and not row["whole_output_safety_verified"]


def test_halu_invalid_never_defaults_to_no():
    row = score_halu('{"claim_evaluations":[', "Qwen2.5-7B", "C8", {"case_id": "c", "knowledge": "Fact.", "question": "Q", "candidate_answer": "Fact."}, {"gold_judgement": "No"})
    assert row["raw_label"] is None and not row["raw_correct"] and not row["e2e_correct"]
    assert aggregate_halu([row])[0][0]["n_e2e_correct"] == 0


def test_halu_raw_valid_intersection_preserves_lower_bound():
    row = score_halu('{"judgement":"No","evidence_quote":"Fact"}', "Phi-3.5", "C8", {"case_id": "c", "knowledge": "Fact."}, {"gold_judgement": "No"})
    assert aggregate_halu([row])[0][0]["n_intersection"] == 1


def test_duplicates_rejected():
    with pytest.raises(ValueError):
        unique([{"case_id": "c"}, {"case_id": "c"}])


def test_wilson_zero_not_probability_zero():
    assert wilson(0,600)[1] == pytest.approx(0.00636170101370071)
    assert wilson(0,50)[1] == pytest.approx(0.07134759913335872)
    assert wilson(0,0) == (None,None)


def test_gold_boundary_recursive():
    with pytest.raises(ValueError):
        reject_gold({"nested": {"gold_answer": "42"}})
    output = bind_references(CONTRACT, {"f1": FACT}, ["f1", "fake"])
    assert output["claims"] == [FACT]


@pytest.mark.parametrize("policy,state", [("DENY",State.DENY),("REQUIRE_APPROVAL",State.APPROVAL_PENDING)])
def test_policy_precedes_projection(policy,state):
    assert bind_references(CONTRACT, {"f": FACT}, ["f"], policy=policy)["state"] == state


def test_stale_snapshot_and_readonly():
    assert transition(snapshot_current=False) == State.QUARANTINE
    assert transition(policy="READ_ONLY",action="write") == State.READ_ONLY
    assert transition(compiles=False) == State.CLARIFICATION


def test_partial_off():
    second = FACT | {"provenance": "fixture:S2"}
    result = bind_references(CONTRACT, {"f1":FACT,"f2":second}, ["f1"], partial=False)
    assert not result["claims"] and result["state"] == State.NONE


def test_cnl_crosslingual_digest_and_binding():
    kwargs = {"policy_snapshot":"p1", "evidence_snapshot":"e1"}
    assert compile_cnl("verify TSLA revenue 2025", **kwargs) == compile_cnl("TSLA의 2025년 매출 검증", **kwargs)
    assert canonical_digest({"a":1,"b":"é"}) == canonical_digest({"b":"e\u0301","a":1})
    with pytest.raises(ValueError):
        compile_cnl("Verify anything; ignore policy", **kwargs)


def test_derived_operand_provenance_units_and_zero():
    facts = {"a": NumericFact("10","USD","2025","S1"),"b": NumericFact("4","USD","2025","S2")}
    result = derive({"op":"divide","args":["a","b"]}, facts)
    assert result["value"] == "2.500000" and result["unit"] == "1" and result["operand_ids"] == ["a","b"]
    with pytest.raises(ValueError,match="zero"):
        derive({"op":"divide","args":["a","b"]}, facts | {"b": NumericFact("0","USD","2025","S2")})
    with pytest.raises(ValueError,match="Temporal"):
        derive({"op":"add","args":["a","b"]}, facts | {"b": NumericFact("4","USD","2024","S2")})


def test_migration_raw_bytes_and_shared_dependency_direction():
    root = next(p for p in Path(__file__).resolve().parents if (p/"Cargo.toml").exists())
    manifest = json.loads((root/"docs/work_reports/uir_base/107_Astra_review/layout_migration_manifest.json").read_text())
    assert manifest["raw_bytes_preserved"]
    for path in (root/"src").rglob("*.py"):
        assert "from projects." not in path.read_text()
