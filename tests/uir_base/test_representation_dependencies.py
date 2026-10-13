import copy
import json
import pytest
from uir_common.representation import TypedRequest, accept, catalog, deterministic_candidate


def derived_fixture():
    base = {"claim_type": "numeric_claim", "entity_id": "D001", "attribute": "revenue", "value": "100", "unit": "USD",
            "period": "2025", "provenance": "fixture://dependency/revenue"}
    income = {**base, "attribute": "net_income", "value": "10", "provenance": "fixture://dependency/income"}
    ratio = {**base, "claim_type": "derived_claim", "attribute": "ratio", "value": "0.1", "unit": "1", "provenance": "derived://trusted/divide"}
    source = catalog([base, income, ratio], "E1")
    ids = {v["attribute"]: k for k, v in source["facts"].items()}
    source["dependencies"][ids["ratio"]] = [ids["net_income"], ids["revenue"]]
    source["derivations"][ids["ratio"]] = {"op": "divide", "args": [ids["net_income"], ids["revenue"]]}
    request = TypedRequest("D001", "ratio", "2025", "1", None, "read", "P1", "E1")
    policy = {"version": "P1", "decision": "ALLOW"}
    return request, source, policy, ids


def test_complete_derived_graph_and_safe_partial():
    r, s, p, ids = derived_fixture()
    full = accept(r.plan(), s, p, {}, deterministic_candidate(r.plan(), s, r.digest), identity=r.digest)
    assert full["state"] == "FULL_VERIFIED_ANSWER" and len(full["accepted_claims"]) == 3
    candidate = json.dumps({"contract_digest": r.digest, "fact_ids": [ids["ratio"], ids["net_income"]]})
    partial = accept(r.plan(), s, p, {}, candidate, identity=r.digest)
    assert partial["state"] == "PARTIAL_VERIFIED_ANSWER"
    assert all(c["claim_type"] != "derived_claim" for c in partial["accepted_claims"])
    assert "0.1" not in partial["accepted_rendered_text"]
    assert accept(r.plan(), s, p, {}, candidate, identity=r.digest, partial=False)["state"] == "NO_VERIFIED_ANSWER"


@pytest.mark.parametrize("mutation", ["wrong_result", "wrong_period", "wrong_unit", "wrong_entity", "zero_denominator", "missing_operand", "cycle"])
def test_derived_dependency_errors_do_not_execute_or_emit(mutation):
    r, s, p, ids = derived_fixture()
    if mutation == "wrong_result": s["facts"][ids["ratio"]]["value"] = "0.2"
    if mutation == "wrong_period": s["facts"][ids["revenue"]]["period"] = "2024"
    if mutation == "wrong_unit": s["facts"][ids["revenue"]]["unit"] = "KRW"
    if mutation == "wrong_entity": s["facts"][ids["revenue"]]["entity_id"] = "OTHER"
    if mutation == "zero_denominator": s["facts"][ids["revenue"]]["value"] = "0"
    if mutation == "missing_operand": del s["facts"][ids["revenue"]]
    if mutation == "cycle": s["dependencies"][ids["revenue"]] = [ids["ratio"]]
    candidate = json.dumps({"contract_digest": r.digest, "fact_ids": list(ids.values())})
    result = accept(r.plan(), s, p, {}, candidate, identity=r.digest)
    assert result["state"] == "QUARANTINE" and not result["accepted_claims"]
