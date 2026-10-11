import json

import pytest

from projects.uir_base.scripts.run_local_ai_review import FIELDS, agreement, make_packet, parse_review


def label():
    return {**{field: choices[0] for field, choices in FIELDS.items()},
            "request_quote": "MSFT", "explanation": "The candidate matches the request."}


def response(value, reason="stop"):
    return {"done": True, "done_reason": reason, "message": {"content": json.dumps(value)}}


def test_strict_review_response_requires_real_quote():
    item = label()
    parsed, error = parse_review(response(item), "MSFT revenue 2024")
    assert error is None and parsed == item
    item["request_quote"] = "a quote that was not present"
    assert parse_review(response(item), "MSFT revenue 2024")[1] == "invented_request_quote"


def test_truncated_and_missing_labels_never_default_to_a_decision():
    assert parse_review(response(label(), "length"), "MSFT")[0] is None
    assert parse_review(response({}), "MSFT")[0] is None
    assert parse_review({"message": {"content": "not json"}}, "MSFT")[0] is None


def test_two_invalid_reviews_are_not_agreement():
    records = [{"reviewer_id": r, "case_id": "a", "valid": False, "label": None} for r in ("AI_J1", "AI_J2")]
    stats = agreement(records, ["a"])
    for result in stats["fields"].values():
        assert result["N_agree"] == 0
        assert result["N_missing_or_invalid_pair"] == 1
        assert result["valid_agreement_full_packet"] == 0
        assert result["cohen_kappa_jointly_valid"] is None


def test_degenerate_kappa_is_not_one():
    records = [{"reviewer_id": r, "case_id": "a", "valid": True, "label": label()} for r in ("AI_J1", "AI_J2")]
    stats = agreement(records, ["a"])
    assert stats["fields"]["intent_match"]["agreement_jointly_valid"] == 1
    assert stats["fields"]["intent_match"]["cohen_kappa_jointly_valid"] is None


def test_joint_uncertainty_is_not_decisive_agreement():
    value = label()
    value["conditions_preservation"] = "UNCERTAIN"
    records = [{"reviewer_id": r, "case_id": "a", "valid": True, "label": value} for r in ("AI_J1", "AI_J2")]
    result = agreement(records, ["a"])["fields"]["conditions_preservation"]
    assert result["N_both_uncertain"] == 1
    assert result["valid_agreement_full_packet"] == 1
    assert result["decisive_valid_agreement_full_packet"] == 0


def test_observed_perfect_mixed_label_agreement_gives_kappa_one():
    records = []
    for cid, match in (("a", "MATCH"), ("b", "MISMATCH")):
        value = label(); value["intent_match"] = match
        records += [{"reviewer_id": r, "case_id": cid, "valid": True, "label": value} for r in ("AI_J1", "AI_J2")]
    assert agreement(records, ["a", "b"])["fields"]["intent_match"]["cohen_kappa_jointly_valid"] == 1


def test_model_visible_id_does_not_disclose_stratum():
    from evaluation.uir_phase4d.runtime.uir_compiler import UIRCompiler
    case = {"case_id": "EXT-ADVERSARIAL-0003", "language": "ko", "input": "META revenue 2017",
            "requested_entity": "META", "requested_attribute": "revenue", "requested_period": "2017"}
    packet = make_packet(case, UIRCompiler(), "public_attributes: [revenue]")
    assert packet["case_id"].startswith("BLIND-")
    assert "ADVERSARIAL" not in json.dumps(packet)
    assert packet["candidate_is_reference"] is False


@pytest.mark.parametrize("field", ["gold_claims", "GOLD_LABEL", "expected_entity", "ground_truth", "ｇｏｌｄ_answer", "answer_gold"])
def test_gold_annotation_fields_are_rejected_from_packets(field):
    from evaluation.uir_phase4d.runtime.uir_compiler import UIRCompiler
    with pytest.raises(ValueError):
        make_packet({field: []}, UIRCompiler(), "")
