import copy
import json
import pytest
from uir_common.representation import *
from projects.uir_base.validation.frontends import compile_shared, normalize_predicate


def fixture():
    claim = {"claim_type": "numeric_claim", "entity_id": "D001", "attribute": "revenue", "value": "10", "unit": "USD", "period": "2025", "provenance": "fixture://public/dev/1"}
    source = catalog([claim], "E1")
    policy = {"version": "P1", "decision": "ALLOW", "approved": False}
    request = compile_shared("verify D001 revenue 2025 in USD", policy, source)
    return request, source, policy


@pytest.mark.parametrize("field", FIELDS)
def test_all_seven_fields_required(field):
    request, source, policy = fixture()
    claim = copy.deepcopy(next(iter(source["facts"].values()))); del claim[field]
    result = accept(request.plan(), source, policy, {}, json.dumps({"contract_digest": request.digest, "claims": [claim]}), mode="full", identity=request.digest)
    assert not result["accepted_claims"]


@pytest.mark.parametrize("field,value", [("unit", ""), ("unit", None), ("unit", "unknown"), ("period", ""), ("period", None), ("period", "unknown"),
                                          ("provenance", "forged"), ("entity_id", "OTHER"), ("period", "2024"), ("unit", "KRW"), ("value", "100")])
def test_unknown_or_forged_fields_do_not_pass(field, value):
    request, source, policy = fixture()
    claim = copy.deepcopy(next(iter(source["facts"].values()))); claim[field] = value
    result = accept(request.plan(), source, policy, {}, json.dumps({"contract_digest": request.digest, "claims": [claim]}), mode="full", identity=request.digest)
    assert not result["accepted_claims"]


def test_reference_binding_does_not_pass_model_prose():
    request, source, policy = fixture()
    candidate = deterministic_candidate(request.plan(), source, request.digest)
    result = accept(request.plan(), source, policy, {}, candidate, identity=request.digest)
    assert result["state"] == "FULL_VERIFIED_ANSWER"
    assert json.loads(result["accepted_rendered_text"])["claims"] == list(source["facts"].values())
    bad = json.loads(candidate); bad["answer"] = "invented profits"
    assert not accept(request.plan(), source, policy, {}, json.dumps(bad), identity=request.digest)["accepted_claims"]


def test_gold_labels_cannot_affect_runtime_because_boundary_rejects_them():
    request, source, policy = fixture()
    candidate = deterministic_candidate(request.plan(), source, request.digest)
    # Scoring labels exist only here and are not arguments to runtime.
    before = accept(request.plan(), source, policy, {}, candidate, identity=request.digest)
    gold = {"expected_claims": []}; gold["expected_claims"] = [{"value": "999"}]
    assert before == accept(request.plan(), source, policy, {}, candidate, identity=request.digest)
    polluted = copy.deepcopy(source); polluted.update(gold)
    with pytest.raises(ValueError): eligible_facts(request.plan(), polluted)


def test_authorized_catalog_change_changes_bound_output():
    request, source, policy = fixture()
    candidate = deterministic_candidate(request.plan(), source, request.digest)
    before = accept(request.plan(), source, policy, {}, candidate, identity=request.digest)
    updated = copy.deepcopy(next(iter(source["facts"].values()))); updated["value"] = "20"
    new_source = catalog([updated], "E2")
    assert accept(request.plan(), new_source, policy, {}, candidate, identity=request.digest)["state"] == "QUARANTINE"
    new_request = compile_shared("verify D001 revenue 2025 in USD", policy, new_source)
    after = accept(new_request.plan(), new_source, policy, {}, deterministic_candidate(new_request.plan(), new_source, new_request.digest), identity=new_request.digest)
    assert before["accepted_claims"] != after["accepted_claims"]


def test_semantic_pair_and_distinguishing_pairs():
    request, source, policy = fixture()
    texts = ["verify D001 revenue 2025 in USD if approval AND entity_verified", "D001의 2025년 매출 검증 단위 USD 조건: 기업확인 그리고 승인"]
    left, right = [compile_shared(t, policy, source) for t in texts]
    assert left.digest == right.digest and left.predicate == right.predicate
    other = compile_shared(texts[0].replace("AND", "OR"), policy, source)
    assert other.digest != left.digest


def test_approval_and_snapshot_revocation():
    request, source, policy = fixture()
    candidate = deterministic_candidate(request.plan(), source, request.digest)
    policy = {**policy, "decision": "REQUIRE_APPROVAL", "approved": False}
    assert accept(request.plan(), source, policy, {}, candidate, identity=request.digest)["state"] == "APPROVAL_PENDING"
    policy["approved"] = True
    assert accept(request.plan(), source, policy, {}, candidate, identity=request.digest)["state"] == "FULL_VERIFIED_ANSWER"
    policy["version"] = "P2"
    assert accept(request.plan(), source, policy, {}, candidate, identity=request.digest)["state"] == "QUARANTINE"


def test_duplicate_unknown_id_and_identity_fail_closed():
    request, source, policy = fixture()
    fid = next(iter(source["facts"]))
    for ids, digest in [([fid, fid], request.digest), (["UNKNOWN"], request.digest), ([fid], "0" * 64)]:
        assert not accept(request.plan(), source, policy, {}, json.dumps({"contract_digest": digest, "fact_ids": ids}), identity=request.digest)["accepted_claims"]
