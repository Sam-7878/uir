"""R08/R06 development diagnostics and honest document/company holdout eligibility."""
from collections import Counter
import importlib.util
import json
import re
from decimal import Decimal
from evaluation.uir_phase4c.pipelines import lexical_context
from projects.uir_base.scripts.next_benchmark_adapter import SOURCE, execute_program, runtime_row, official_evaluator
from .arithmetic import execute_ast, marker_diagnostic
from .common import FROZEN, OLD, OUT, csvfile, load, read, sha, write


def number_set(text):
    return {Decimal(x.replace(",", "")) for x in re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text)}


def identities(row):
    identifier = row["id"]
    document = identifier.split(".pdf")[0] + ".pdf"
    company = identifier.split("/")[0]
    return document, company


def run():
    data = load(SOURCE / "test.json")
    previous = {r["source_index"] for r in read(FROZEN / "finqa_runtime_200.jsonl")}
    used = previous | set(load(OLD / "finqa_holdout_v2/protocol.json")["source_indices"])
    used_docs = {identities(data[i])[0] for i in used}; used_companies = {identities(data[i])[1] for i in used}
    lineage = []
    for i, row in enumerate(data):
        doc, company = identities(row)
        lineage.append({"source_index": i, "document_id": doc, "company": company, "previous_index_used": i in used,
                        "document_overlaps_development": doc in used_docs, "company_overlaps_development": company in used_companies,
                        "eligible_document_disjoint": i not in used and doc not in used_docs,
                        "eligible_company_document_disjoint": i not in used and doc not in used_docs and company not in used_companies,
                        "template_family_verified_disjoint": False})
    csvfile(OUT / "new_holdout_lineage.csv", lineage)
    write(OUT / "confirmatory_protocol.json", {"status": "NO_FAMILY_DISJOINT_HOLDOUT", "dataset_sha256": sha(SOURCE / "test.json"),
          "N_index_unused": sum(not r["previous_index_used"] for r in lineage),
          "N_document_disjoint_available": sum(r["eligible_document_disjoint"] for r in lineage),
          "N_company_document_disjoint_available": sum(r["eligible_company_document_disjoint"] for r in lineage),
          "template_independence_verified": False, "executed": False,
          "reason": "No verified family-disjoint pool spanning document/company/template; remaining rows are availability audit only, not a selected confirmatory set."})
    rows = []
    for i in sorted(used):
        row = data[i]; runtime = runtime_row(row, i)
        lexical = "\n".join(lexical_context(runtime))
        whole = "\n".join(row["pre_text"] + row["post_text"] + [" | ".join(map(str, r)) for r in row["table"]])
        literals = {Decimal(n.replace(",", "")) for n in re.findall(r"(?<![\w#])-?\d+(?:\.\d+)?(?=%|,|\))", row["qa"]["program"])}
        lexical_numbers, whole_numbers = number_set(lexical), number_set(whole)
        rows.append({"source_index": i, "source_id": row["id"], "gold_operand_literals_N": len(literals),
                     "lexical_all_operand_numbers_present": literals <= lexical_numbers,
                     "full_document_all_operand_numbers_present": literals <= whole_numbers,
                     "lexical_missing_operands": "|".join(str(v) for v in sorted(literals - lexical_numbers)),
                     "full_source_missing_operands": "|".join(str(v) for v in sorted(literals - whole_numbers)),
                     "gold_program": row["qa"]["program"], "evaluation_only": True,
                     "semantic_operand_selection_or_unit_sufficiency": "NOT_MEASURED",
                     "answer_display": row["qa"].get("answer"), "exe_ans": row["qa"].get("exe_ans"),
                     "display_has_percent": "%" in str(row["qa"].get("answer", ""))})
    csvfile(OUT / "retrieval_sufficiency_audit.csv", rows)
    transitions = []
    for row in read(OLD / "finqa_holdout_v2/raw_requests_responses.jsonl"):
        raw = (row["response"] or {}).get("message", {}).get("content", "")
        diag = marker_diagnostic(raw)
        condition = row["condition"]
        parsed = None
        try: parsed = json.loads(raw)
        except (ValueError, TypeError): pass
        program = parsed.get("program") if isinstance(parsed, dict) else None
        taxonomy = "NATIVE_LITERAL_DIAGNOSTIC" if condition == "C1_NATIVE_ANSWER" else "MISSING_PROGRAM" if not program else "PROGRAM_PROSE_OR_UNSUPPORTED_OPERATOR" if not re.match(r"(add|subtract|multiply|divide|greater)\(", program) else "DSL_PARSE_OR_EXECUTION_CHECK_REQUIRED"
        transitions.append({"case_id": row["case_id"], "condition": condition, "model": row["model"], "diagnostic_literal_state": diag["status"],
                            "taxonomy": taxonomy, "finish_reason": (row["response"] or {}).get("done_reason", "MISSING"),
                            "percent_auto_division_vNext": False, "old_primary_changed": False,
                            "unsupported_factual_claim_rate": "NOT_MEASURED", "evidence_kind": "historical_reanalysis"})
    csvfile(OUT / "dev_parse_transition.csv", transitions)
    official = official_evaluator(); parity = []
    facts = {"a": {"value": "10", "unit": "1"}, "b": {"value": "5", "unit": "1"}, "c": {"value": "2", "unit": "1"},
             "d": {"value": "25", "unit": "percent"}}
    programs = [("add", "a", "b"), ("subtract", "a", "b"), ("multiply", "a", "b"), ("divide", "a", "b"),
                ("greater", "a", "b"), ("exp", "c", "b"), ("add", "d", "c")]
    for op, x, y in programs:
        left = facts[x]["value"] + ("%" if facts[x]["unit"] == "percent" else "")
        right = facts[y]["value"] + ("%" if facts[y]["unit"] == "percent" else "")
        text = f"{op}({left}, {right})"
        bad, val = official.eval_program(official.program_tokenization(text), [])
        ours = execute_ast({"steps": [{"op": op, "operands": [{"source_id": x}, {"source_id": y}]}]}, facts)
        equal = ours["value"] == val if isinstance(val, str) else round(float(ours["value"]), 5) == val
        parity.append({"program": text, "official_invalid": bad, "official_value": val, "typed_value": ours["value"], "typed_unit": ours["unit"],
                       "parity": equal, "scope": "declared typed operands; FinQA source units not automatically known"})
    for op in ("table_sum", "table_average", "table_min", "table_max"):
        text = f"{op}(Revenue, none)"
        bad, val = official.eval_program(official.program_tokenization(text), [["Revenue", "10", "5", "2"]])
        ours = execute_ast({"steps": [{"op": op, "operands": [{"source_id": k} for k in ("a", "b", "c")]}]}, facts)
        parity.append({"program": text, "official_invalid": bad, "official_value": val, "typed_value": ours["value"], "typed_unit": ours["unit"],
                       "parity": round(float(ours["value"]), 5) == val, "scope": "explicit table-cell source refs"})
    csvfile(OUT / "parity_matrix.csv", parity)
    write(OUT / "finqa_development_summary.json", {"N_retrieval_cases": len(rows),
          "lexical_numeric_operand_presence": sum(r["lexical_all_operand_numbers_present"] for r in rows),
          "full_numeric_operand_presence": sum(r["full_document_all_operand_numbers_present"] for r in rows),
          "presence_not_semantic_sufficiency": True, "N_raw_diagnostics": len(transitions), "N_parity_cases": len(parity),
          "N_parity_pass": sum(r["parity"] for r in parity), "official_evaluator_sha256": sha(SOURCE / "evaluate.py"),
          "new_FinQA_inference": False, "old_primary_unchanged": True})
    print(load(OUT / "confirmatory_protocol.json"))


if __name__ == "__main__":
    run()
