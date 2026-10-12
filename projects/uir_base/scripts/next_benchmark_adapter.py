"""Strict source-number arithmetic adapter and official FinQA parity diagnostics.

This is not the official evaluator and not seven-field claim groundedness.
"""
from decimal import Decimal, InvalidOperation
import importlib.util
import json
import re
from projects.uir_base.scripts import revision_audit as a
from projects.uir_base.scripts.next_release import DEFAULT, jsonl

SOURCE = a.ROOT / "projects/uir_base/evaluation/uir_phase4c/official_sources/FinQA"
OPS = {"add", "subtract", "multiply", "divide", "greater"}
STEP = re.compile(r"(add|subtract|multiply|divide|greater)\(\s*([^(),]+)\s*,\s*([^(),]+)\s*\)")


def official_evaluator():
    spec = importlib.util.spec_from_file_location("uir_next_official_finqa", SOURCE / "evaluate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runtime_row(row, index):
    # Never copy qa/gold evidence selections into runtime; no gold-aware retrieval.
    return {"case_id": f"FINQA-NEXT-{index:04d}", "source_index": index, "source_original_id": row["id"],
            "source_row_hash": hash_object(row), "source_file_sha256": a.digest(SOURCE / "test.json"), "question": row["qa"]["question"],
            "pre_text": row["pre_text"], "post_text": row["post_text"], "table": row["table"], "filename": row.get("filename", "")}


def execute_program(program, case):
    if not isinstance(program, str) or not program or len(program) > 500:
        return {"contract_status": "REJECTED", "reason": "missing_or_resource_limit", "execution_status": "NOT_EXECUTED", "value": None}
    matches = list(STEP.finditer(program))
    if not matches or len(matches) > 12:
        return {"contract_status": "REJECTED", "reason": "unsupported_operator_or_steps", "execution_status": "NOT_EXECUTED", "value": None}
    position = 0
    for i, match in enumerate(matches):
        gap = program[position:match.start()]
        if gap.strip() != ("," if i else ""):
            return {"contract_status": "REJECTED", "reason": "unconsumed_program_text", "execution_status": "NOT_EXECUTED", "value": None}
        position = match.end()
    if program[position:].strip():
        return {"contract_status": "REJECTED", "reason": "unconsumed_program_text", "execution_status": "NOT_EXECUTED", "value": None}
    text = "\n".join(case.get("pre_text", []) + case.get("post_text", []) + [" | ".join(map(str, r)) for r in case.get("table", [])])
    source_numbers = {Decimal(n.replace(",", "")) for n in re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text)}
    values = []; trace = []
    def operand(token):
        token = token.strip()
        if re.fullmatch(r"#\d+", token):
            ref = int(token[1:])
            if ref >= len(values) or isinstance(values[ref], str):
                raise ValueError("invalid_or_forward_reference")
            return values[ref]
        constants = {"const_1": Decimal(1), "const_m1": Decimal(-1), "const_100": Decimal(100)}
        if token in constants:
            return constants[token]
        if not re.fullmatch(r"-?\d+(?:\.\d+)?%?", token):
            raise ValueError("invalid_operand")
        number = Decimal(token.rstrip("%"))
        if number not in source_numbers:
            raise ValueError("number_absent_from_evidence")
        return number / 100 if token.endswith("%") else number
    try:
        for match in matches:
            op, x, y = match.groups(); left, right = operand(x), operand(y)
            if op == "divide" and right == 0:
                raise ValueError("division_by_zero")
            result = left + right if op == "add" else left - right if op == "subtract" else left * right if op == "multiply" else left / right if op == "divide" else "yes" if left > right else "no"
            if not isinstance(result, str) and (not result.is_finite() or abs(result) > Decimal("1e30")):
                raise ValueError("numeric_resource_limit")
            values.append(result); trace.append({"op": op, "arg1": x.strip(), "arg2": y.strip(), "value": str(result)})
        return {"contract_status": "ACCEPTED", "execution_status": "SUCCESS", "reason": None,
                "value": round(float(values[-1]), 5) if not isinstance(values[-1], str) else values[-1], "trace": trace,
                "groundedness_scope": "source-number presence only; not unit/period/semantic operand selection"}
    except (ValueError, InvalidOperation, ZeroDivisionError) as exc:
        return {"contract_status": "REJECTED", "execution_status": "NOT_EXECUTED", "reason": str(exc), "value": None, "trace": trace}


def semantic_answer(raw, condition, case):
    parsed = None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        pass
    if condition == "C8_ARITHMETIC_CONTRACT":
        program = parsed.get("program") if isinstance(parsed, dict) else None
        if program is None:
            # Format and task semantics are distinct: a completed source-bound program
            # can still be extracted from native text, without claiming strict JSON.
            native = re.fullmatch(r"\s*((?:add|subtract|multiply|divide|greater)\(.+\))\s*", raw)
            program = native.group(1) if native else None
        result = execute_program(program, case)
        return {"strict_json": isinstance(parsed, dict) and set(parsed) == {"program"} and isinstance(parsed["program"], str),
                "semantic_label_status": "PRESENT" if program else "MISSING", "program": program, **result}
    match = re.search(r"FINAL_ANSWER:\s*([-+]?\d+(?:,\d{3})*(?:\.\d+)?%?|yes|no)\s*$", raw, re.I)
    if not match:
        return {"strict_json": False, "semantic_label_status": "MISSING", "contract_status": "NOT_APPLICABLE", "execution_status": "NOT_APPLICABLE", "value": None}
    token = match.group(1).lower().replace(",", "")
    value = token if token in {"yes", "no"} else round(float(token.rstrip("%")) / (100 if token.endswith("%") else 1), 5)
    return {"strict_json": False, "semantic_label_status": "PRESENT", "contract_status": "NOT_APPLICABLE", "execution_status": "NOT_APPLICABLE", "value": value}


def parity(root=DEFAULT):
    out = root / "benchmark_adapter"
    out.mkdir(exist_ok=False)
    official = official_evaluator()
    case = {"pre_text": ["Numbers 10 5 2 0 25"], "post_text": [], "table": []}
    programs = ["add(10, 5)", "subtract(10, 5)", "multiply(10, 5)", "divide(10, 5)", "greater(10, 5)",
                "add(10, 5), divide(#0, 5)", "multiply(25, const_100)", "divide(10, 0)",
                "exp(10, 2)", "add(10, 99)", "add(10, 5) garbage", "add(#1, 5)"]
    rows = []
    for p in programs:
        invalid, value = official.eval_program(official.program_tokenization(p), [])
        ours = execute_program(p, case)
        rows.append({"program": p, "official_invalid": invalid, "official_value": value, "custom": ours,
            "parity_on_intersection": ours["value"] == value if ours["execution_status"] == "SUCCESS" and not invalid else "NOT_APPLICABLE",
            "scope_difference": "official allows source-unbound numbers, exp/table ops; custom strictly consumes text and restricts evidence operands"})
    jsonl(out / "official_custom_parity.jsonl", rows)
    old = a.unique(a.read(a.FROZEN / "finqa_runtime_200.jsonl"))
    protocol = json.loads((a.BASE / "mdpi_revision_2026_10_11/new_holdout_protocol.json").read_text())
    data = json.loads((SOURCE / "test.json").read_text())
    if a.digest(SOURCE / "test.json") != protocol["source_sha256"]:
        raise ValueError("Original FinQA source hash mismatch")
    selected = protocol["source_indices"]
    if len(set(selected)) != 200 or set(selected) & {r["source_index"] for r in old.values()}:
        raise ValueError("Duplicate/overlapping holdout indices")
    previous_docs = {r["filename"] for r in old.values()}; previous_companies = {s.split('/')[0] for s in previous_docs}
    lineage = []; representable = []
    for i in selected:
        row = data[i]; runtime = runtime_row(row, i); filename = row.get("filename", row["id"].rsplit('-', 1)[0])
        lineage.append({"source_index": i, "source_original_id": row["id"], "filename": filename,
            "row_sha256": hash_object(row), "document_seen_in_development": filename in previous_docs,
            "company_seen_in_development": filename.split('/')[0] in previous_companies})
        # Evaluation-only expressibility audit. No gold program goes to model input.
        result = execute_program(row["qa"]["program"], runtime)
        representable.append({"source_index": i, "contract_executable_gold": result["execution_status"] == "SUCCESS", "reason": result.get("reason"),
            "evidence_kind": "historical_reanalysis", "gold_program_used_only_in_scoring": True})
    jsonl(out / "holdout_lineage.jsonl", lineage)
    a.write_csv(out / "contract_expressibility_scoring_only.csv", representable)
    a.write_json(out / "adapter_verification.json", {"status": "PARITY_ON_SUPPORTED_INTERSECTION_ONLY",
        "N_parity_tests": len(rows), "N_intersection_tests": sum(r["parity_on_intersection"] != "NOT_APPLICABLE" for r in rows),
        "parity_failures": sum(r["parity_on_intersection"] is False for r in rows), "N_disjoint_indices": len(selected),
        "N_document_overlap": sum(r["document_seen_in_development"] for r in lineage), "N_company_overlap": sum(r["company_seen_in_development"] for r in lineage),
        "N_contract_executable_gold": sum(r["contract_executable_gold"] for r in representable),
        "official_evaluator_sha256": a.digest(SOURCE / "evaluate.py"), "dataset_sha256": a.digest(SOURCE / "test.json"),
        "unsupported_claims": "NOT_MEASURED", "holdout_semantics": "index-disjoint, not necessarily document/company-independent"})


from projects.uir_base.scripts.next_release import hash_object

if __name__ == "__main__":
    parity()
