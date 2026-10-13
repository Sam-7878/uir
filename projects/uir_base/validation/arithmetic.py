"""Bounded typed arithmetic AST; no prose execution or silent unknown-unit match."""
from decimal import Decimal, InvalidOperation, localcontext
import re

OPERATORS = ("add", "subtract", "multiply", "divide", "greater", "exp", "table_sum", "table_min", "table_max", "table_average")


def execute_ast(program, facts):
    if not isinstance(program, dict) or set(program) != {"steps"} or not isinstance(program["steps"], list) or not 1 <= len(program["steps"]) <= 16:
        raise ValueError("PROGRAM_AST_INVALID")
    values = []; trace = []
    def operand(ref):
        if not isinstance(ref, dict) or len(ref) != 1: raise ValueError("OPERAND_REFERENCE_INVALID")
        if "source_id" in ref:
            if ref["source_id"] not in facts: raise ValueError("SOURCE_OPERAND_MISSING")
            fact = facts[ref["source_id"]]
            if fact["unit"] == "UNKNOWN" or not fact["unit"]: raise ValueError("UNIT_UNKNOWN")
            number = Decimal(fact["value"]); unit = fact["unit"]
            if unit == "percent": number /= 100; unit = "1"
            if not number.is_finite(): raise ValueError("NONFINITE_OPERAND")
            return number, unit
        if "step" in ref:
            if type(ref["step"]) is not int or not 0 <= ref["step"] < len(values): raise ValueError("FORWARD_STEP_REFERENCE")
            if isinstance(values[ref["step"]][0], str): raise ValueError("BOOLEAN_USED_AS_NUMERIC")
            return values[ref["step"]]
        if "constant" in ref and ref["constant"] in {"1", "-1", "100"}:
            return Decimal(ref["constant"]), "1"
        raise ValueError("OPERAND_REFERENCE_INVALID")
    with localcontext() as ctx:
        ctx.prec = 48
        for step in program["steps"]:
            if not isinstance(step, dict) or set(step) != {"op", "operands"} or step["op"] not in OPERATORS:
                raise ValueError("UNSUPPORTED_OPERATOR")
            op = step["op"]; args = [operand(r) for r in step["operands"]]
            if op.startswith("table_"):
                if not args or len(args) > 32 or len({u for v, u in args}) != 1: raise ValueError("TABLE_UNIT_OR_ARITY_MISMATCH")
                vals = [v for v, u in args]; unit = args[0][1]
                value = sum(vals) if op == "table_sum" else min(vals) if op == "table_min" else max(vals) if op == "table_max" else sum(vals)/len(vals)
            else:
                if len(args) != 2: raise ValueError("OPERATOR_ARITY_MISMATCH")
                (left, ul), (right, ur) = args
                if op in {"add", "subtract", "greater"} and ul != ur: raise ValueError("UNIT_MISMATCH")
                if op == "divide" and right == 0: raise ValueError("DIVISION_BY_ZERO")
                if op == "exp" and (ul != "1" or ur != "1" or right != int(right) or not 0 <= right <= 6):
                    raise ValueError("EXP_TYPE_OR_RESOURCE_MISMATCH")
                value = left+right if op == "add" else left-right if op == "subtract" else left*right if op == "multiply" else left/right if op == "divide" else left**int(right) if op == "exp" else "yes" if left > right else "no"
                unit = ul if op in {"add", "subtract"} else "BOOLEAN" if op == "greater" else "1" if op == "exp" else (ur if ul == "1" else ul if ur == "1" else f"{ul}*{ur}") if op == "multiply" else "1" if ul == ur else ul if ur == "1" else f"{ul}/{ur}"
            if not isinstance(value, str) and (not value.is_finite() or abs(value) > Decimal("1e30")): raise ValueError("ARITHMETIC_OVERFLOW")
            values.append((value, unit)); trace.append({"op": op, "operands": step["operands"], "value": str(value), "unit": unit})
    return {"value": str(values[-1][0]), "unit": values[-1][1], "trace": trace, "support_scope": "typed declared source references, not inferred report-wide units"}


def marker_diagnostic(text):
    matches = re.findall(r"FINAL_ANSWER:\s*([-+]?\d+(?:,\d{3})*(?:\.\d+)?%?|yes|no)", text, re.I)
    distinct = {m.lower().replace(",", "") for m in matches}
    if len(distinct) > 1: return {"status": "AMBIGUOUS", "tokens": matches}
    return {"status": "PRESENT" if distinct else "MISSING", "tokens": matches,
            "value": next(iter(distinct)) if distinct else None, "percent_auto_division": False}
