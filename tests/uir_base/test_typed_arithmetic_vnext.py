import pytest
from projects.uir_base.validation.arithmetic import execute_ast, marker_diagnostic


@pytest.mark.parametrize("op", ["add", "subtract", "multiply", "divide", "greater", "exp", "table_sum", "table_average", "table_min", "table_max"])
def test_typed_operators(op):
    facts = {"a": {"value": "10", "unit": "1"}, "b": {"value": "2", "unit": "1"}}
    result = execute_ast({"steps": [{"op": op, "operands": [{"source_id": "a"}, {"source_id": "b"}]}]}, facts)
    assert result["value"] and result["trace"]


@pytest.mark.parametrize("fault", ["unknown_unit", "wrong_unit", "zero", "forward", "unsupported", "prose"])
def test_typed_program_errors_are_explicit(fault):
    facts = {"a": {"value": "10", "unit": "USD"}, "b": {"value": "2", "unit": "USD"}}
    step = {"op": "divide" if fault == "zero" else "add", "operands": [{"source_id": "a"}, {"source_id": "b"}]}
    if fault == "unknown_unit": facts["a"]["unit"] = "UNKNOWN"
    if fault == "wrong_unit": facts["b"]["unit"] = "KRW"
    if fault == "zero": facts["b"]["value"] = "0"
    if fault == "forward": step["operands"][0] = {"step": 0}
    if fault == "unsupported": step["op"] = "shell"
    if fault == "prose": step = "Calculate the answer using addition"
    with pytest.raises(ValueError): execute_ast({"steps": [step]}, facts)


def test_marker_middle_is_only_diagnostic_and_ambiguous_is_not_chosen():
    assert marker_diagnostic("FINAL_ANSWER: 25% then explanation")["value"] == "25%"
    assert marker_diagnostic("FINAL_ANSWER: 1 FINAL_ANSWER: 2")["status"] == "AMBIGUOUS"
