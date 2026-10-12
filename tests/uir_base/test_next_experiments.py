import pytest
from projects.uir_base.scripts.next_benchmark_adapter import execute_program, semantic_answer
from projects.uir_base.scripts.next_review import parse
from projects.uir_base.scripts.next_release import DEFAULT, checked_path
from projects.uir_base.scripts.revision_audit import digest


def test_arithmetic_adapter_consumes_all_text_and_source_binds():
    case = {"pre_text": ["10 5"], "post_text": [], "table": []}
    assert execute_program("add(10, 5), divide(#0, 5)", case)["value"] == 3
    for program in ("add(10, 5) garbage", "add(10, 99)", "add(#1, 5)", "divide(10, 0)", "exp(10, 5)"):
        result = execute_program(program, case)
        assert result["contract_status"] == "REJECTED"
    result = semantic_answer('add(10, 5)', "C8_ARITHMETIC_CONTRACT", case)
    assert result["value"] == 15 and result["strict_json"] is False
    assert semantic_answer('Thus FINAL_ANSWER: 15', "C1_NATIVE_ANSWER", case)["value"] == 15
    assert semantic_answer('15 unsupported extra', "C1_NATIVE_ANSWER", case)["value"] is None


def test_new_review_finish_missing_and_invalid_label_fail_closed():
    for response in ({"done": True, "message": {"content": '{}'}},
                     {"done": True, "done_reason": "length", "message": {"content": '{}'}},
                     {"done": True, "done_reason": "stop", "message": {"content": '{"slot_match":"MADE_UP"}'}}):
        with pytest.raises(Exception):
            parse(response, "raw")


def test_frozen_family_mapping_cannot_be_changed_while_retaining_case_ids(tmp_path):
    source = DEFAULT / "source_family_manifest.csv"
    if not source.exists():
        pytest.skip("Executed release fixture not included; no family-integrity PASS claimed")
    target = tmp_path / "source_family_manifest.csv"
    expected = digest(source)
    lines = source.read_text().splitlines()
    header = lines[0].split(",")
    index = header.index("source_family_id")
    first = lines[1].split(","); first[index] = "WRONG-INDEPENDENT-FAMILY"
    lines[1] = ",".join(first)
    target.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        checked_path(tmp_path, target.name, expected)
