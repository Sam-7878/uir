from copy import deepcopy
import json
import zipfile
import pytest
from uir_common.contracts import canonical_digest, reject_gold
from uir_common.query_contract import parse_raw, make_artifact, public_line
from projects.uir_base.representation_research.baseline import checked_zip, authoritative_report, unique_rows, validate_lineage
from projects.uir_base.representation_research.common import RELEASE_SHA
from projects.uir_base.representation_research.dataset import source_first
from projects.uir_base.representation_research.evaluation import packet_for, closed_output
from projects.uir_base.representation_research.interpreter_python import interpret
from projects.uir_base.representation_research.specialized import packet_for_specialized
from projects.uir_base.representation_research.gates import check_claim


@pytest.fixture
def row():
    source, _ = source_first()
    return {"case_id": "TEST", "raw_user_request": "show CIRRUS assets for 2024 in USD.", "source": source,
            "authority": {"version": "P1", "decision": "ALLOW", "approved": False}, "context": {"active": True}, "action": "read"}


def test_query_has_real_distractors(row):
    packet = packet_for(row)
    answer = interpret(packet)
    assert answer == {"state": "FULL_VERIFIED_ANSWER", "fact_ids": ["CIRRUS_2024_assets"]}
    assert len(row["source"]["facts"]) == 48
    assert interpret(packet_for_specialized(row)) == answer


@pytest.mark.parametrize("raw", ["show CIRRUS assets for 2024 in USD.", "CIRRUS의 2024년 자산을 USD 단위로 보여 주세요.", "Please show CIRRUS assets for 2024 in USD."])
def test_true_bilingual_raw_without_slots(raw):
    assert parse_raw(raw)["entity"] == "CIRRUS"


@pytest.mark.parametrize("raw", ["그 회사의 상황이 좋은가요?", "Explain why it improved.", "CIRRUS assets 좀 알려줘", "show CIRRUS assets between 2023 and 2024 in USD."])
def test_unsupported_language_clarifies(raw):
    with pytest.raises(ValueError, match="CLARIFICATION"):
        parse_raw(raw)


def test_negation_preserves_difference():
    positive = parse_raw("show CIRRUS assets for 2024 in USD if active is true.")
    negative = parse_raw("CIRRUS의 2024년 자산을 USD 단위로 보여 주세요. 단, 활성 상태가 거짓일 때만.")
    assert positive["predicate"]["value"] is True
    assert negative["predicate"]["value"] is False


@pytest.mark.parametrize("mutation", ["digest", "evidence", "policy", "version"])
def test_untrusted_mutations_quarantine(row, mutation):
    packet = packet_for(row)
    if mutation == "digest": packet["artifact"]["semantic_digest"] = "0" * 64
    elif mutation == "evidence": packet["artifact"]["execution_contract"]["facts"][0]["value"] = "4"
    elif mutation == "policy": packet["authority"]["version"] = "revoked"
    else: packet["artifact"]["execution_contract"]["version"] = "unknown"
    assert interpret(packet)["state"] == "QUARANTINE"


def test_full_visible_output_not_unchecked_prose(row):
    packet = packet_for(row)
    line = public_line(row["source"]["facts"][0])
    result = closed_output([line, "Company is healthy.", line.replace("2000", "2222")], packet)
    assert result["user_visible_output"] == line
    assert len(result["rejected_lines"]) == 2
    assert result["native_prose_AUCR"] == "NOT_MEASURED"


def test_nonempty_safe_partial(row):
    source = deepcopy(row["source"])
    fact = deepcopy(source["facts"][0])
    fact.update(id="SECOND_SOURCE", provenance="synthetic:second")
    source["facts"].append(fact)
    source["trusted_provenance"].append("synthetic:second")
    packet = packet_for(row, source)
    result = closed_output([public_line(source["facts"][0])], packet)
    assert result["state"] == "PARTIAL_VERIFIED_ANSWER"
    assert result["user_visible_output"]


def test_missing_operand_removes_derived_claim(row):
    row["raw_user_request"] = "show CIRRUS margin for 2024 in percent."
    row["source"]["facts"] = [f for f in row["source"]["facts"] if f["id"] != "CIRRUS_2024_revenue"]
    assert interpret(packet_for(row))["fact_ids"] == []


def test_no_implicit_permission_elevation(row):
    row["action"] = "write"
    assert interpret(packet_for(row))["state"] == "DENY"


def test_old_replay_cannot_be_final():
    with pytest.raises(ValueError):
        authoritative_report({"archive_sha256": "old", "model_calls": 0, "status": "FRESH_ENV_COMBINED_ARCHIVE_REPLAY_PASS"}, RELEASE_SHA)


def test_zip_hash_contamination(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as handle: handle.writestr("file", b"data")
    with pytest.raises(ValueError, match="BASELINE_HASH"):
        checked_zip(archive, "0" * 64)


@pytest.mark.parametrize("names", [["../escape"], ["/absolute"], ["same", "same"]])
def test_zip_members_fail_closed(tmp_path, names):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        for name in names: handle.writestr(name, "test")
    with pytest.raises(ValueError, match="UNSAFE_OR_DUPLICATE"):
        checked_zip(archive)


def test_duplicate_cases_and_missing_lineage():
    with pytest.raises(ValueError): unique_rows([{"case_id": "X"}] * 2, ("case_id",))
    with pytest.raises(ValueError): validate_lineage({})


def test_gold_is_not_runtime_input(row):
    row["expected_ids"] = ["anything"]
    with pytest.raises(ValueError): packet_for_specialized(row)


@pytest.mark.parametrize("record", [
    {"endpoint": "QUERY_AWARE_SELECTION", "raw_request_present": False},
    {"whole_output_AUCR_measured": True, "all_displayed_output_scored": False},
    {"source_scope": "entire_parent_annual_report", "parent_report_bytes_verified": False},
    {"human_validated": True, "actual_human_label_count": 0},
    {"confirmatory": True, "verified_family_disjoint": True, "dev_families": ["same"], "holdout_families": ["same"]},
    {"capability_parity": True, "UIR_source_hash": "one", "specialized_source_hash": "two"},
    {"UIR_accuracy_superiority": True, "UIR_accuracy": 1, "specialized_accuracy": 1},
])
def test_negative_scientific_claims(record):
    with pytest.raises(ValueError): check_claim(record)


def test_submission_without_real_author_is_blocked():
    assert check_claim({"submission_ready": True, "author_approval": False}) == "BLOCKED"
