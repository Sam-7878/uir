"""S04–S06 finite semantic/whole-output tests, separate from model inference."""
from copy import deepcopy
import json
import subprocess
import time
from uir_common.contracts import canonical_digest
from uir_common.query_contract import parse_raw, make_artifact, public_line, semantic_key
from .common import ROOT, csvfile, jsonl, load, read, sha, textfile, utc, write
from .interpreter_python import interpret


def packet_for(row, source=None):
    source = source or row["source"]
    return {"artifact": make_artifact(parse_raw(row["raw_user_request"]), row["authority"], source, action=row["action"]),
            "authority": row["authority"], "current_evidence_version": source["version"],
            "current_evidence_sha256": canonical_digest(source), "context": row["context"]}


def closed_output(lines, packet, selected_ids=None):
    """Inspect every user-visible line; no unparsed prose is approved."""
    normative = interpret(packet)
    facts = (packet["private_plan"]["evidence"] if "private_plan" in packet else packet["artifact"]["execution_contract"])["facts"]
    selected = set(normative["fact_ids"] if selected_ids is None else selected_ids) & set(normative["fact_ids"])
    valid = {public_line(f): f["id"] for f in facts if f["id"] in selected}
    accepted = []
    refs = []
    rejected = []
    for line in lines:
        if isinstance(line, str) and line in valid and valid[line] not in refs:
            accepted.append(line)
            refs.append(valid[line])
        else:
            rejected.append(line)
    state = normative["state"]
    if normative["fact_ids"]:
        state = "FULL_VERIFIED_ANSWER" if set(refs) == set(normative["fact_ids"]) else "PARTIAL_VERIFIED_ANSWER" if refs else "NO_VERIFIED_ANSWER"
    return {"state": state, "fact_ids": sorted(refs), "user_visible_output": "\n".join(accepted), "rejected_lines": rejected,
            "whole_output_scope": "CLOSED_FACT_LINES_S1", "native_prose_AUCR": "NOT_MEASURED"}


def run(out):
    rows = read(out / "runtime/query_aware_dev.jsonl")
    cases = []
    base = packet_for(rows[0])
    for row in rows:
        cases.append({"case_id": row["case_id"], "packet": packet_for(row), "expected_state": "FULL_VERIFIED_ANSWER",
                      "evidence_kind": "SYNTHETIC_CONFORMANCE", "mutation": "none"})
    def add(name, transform, expected, trusted=False):
        packet = deepcopy(base)
        transform(packet)
        if trusted:
            execution = packet["artifact"]["execution_contract"]
            packet["current_evidence_sha256"] = canonical_digest({"version": execution["evidence_version"], "facts": execution["facts"], "trusted_provenance": execution["trusted_provenance"]})
            packet["artifact"]["semantic_digest"] = canonical_digest({k: packet["artifact"][k] for k in ("semantics", "policy_constraints", "execution_contract", "output_contract")})
        cases.append({"case_id": "NEG-" + name, "packet": packet, "expected_state": expected,
                      "evidence_kind": "SYNTHETIC_CONFORMANCE", "mutation": name})
    add("digest_corrupt", lambda p: p["artifact"].update(semantic_digest="0" * 64), "QUARANTINE")
    add("snapshot_revoked", lambda p: p["authority"].update(version="policy-revoked-S2"), "QUARANTINE")
    add("source_substitution", lambda p: p["artifact"]["execution_contract"]["facts"][0].update(value="999999"), "QUARANTINE")
    add("unknown_schema", lambda p: p["artifact"]["execution_contract"].update(version="S999"), "QUARANTINE", True)
    add("forged_provenance", lambda p: p["artifact"]["execution_contract"]["facts"][0].update(provenance="forged"), "QUARANTINE", True)
    add("policy_deny", lambda p: p["authority"].update(decision="DENY"), "DENY")
    add("approval_pending", lambda p: p["authority"].update(decision="APPROVAL", approved=False), "APPROVAL_PENDING")
    def readonly(p):
        p["authority"]["decision"] = "READ_ONLY"
        p["artifact"]["policy_constraints"]["action"] = "write"
    add("readonly_write", readonly, "READ_ONLY", True)
    add("missing_predicate_field", lambda p: p["artifact"]["semantics"].update(predicate={"op": "EQ_BOOL", "field": "missing", "value": True}), "CLARIFICATION", True)
    add("false_condition", lambda p: p["artifact"]["semantics"].update(predicate={"op": "EQ_BOOL", "field": "active", "value": False}), "DENY", True)
    add("empty_relevant", lambda p: p["artifact"]["semantics"].update(entity="UNKNOWN"), "NO_VERIFIED_ANSWER", True)
    add("duplicate_fact", lambda p: p["artifact"]["execution_contract"]["facts"].append(deepcopy(p["artifact"]["execution_contract"]["facts"][0])), "QUARANTINE", True)
    def conflict(p):
        f = deepcopy(p["artifact"]["execution_contract"]["facts"][0])
        f.update(id="CONFLICT", value="444")
        p["artifact"]["execution_contract"]["facts"].append(f)
    add("conflict", conflict, "QUARANTINE", True)
    def derived(p, fault):
        q = p["artifact"]["semantics"]
        q.update(metric="margin", unit="percent")
        facts = p["artifact"]["execution_contract"]["facts"]
        margin = next(f for f in facts if f["id"] == "CIRRUS_2024_margin")
        if fault == "missing":
            facts[:] = [f for f in facts if f["id"] != "CIRRUS_2024_revenue"]
        elif fault == "cycle":
            margin["dependencies"] = [margin["id"], "CIRRUS_2024_revenue"]
        elif fault == "zero":
            next(f for f in facts if f["id"] == "CIRRUS_2024_revenue")["value"] = "0"
        elif fault == "unit":
            next(f for f in facts if f["id"] == "CIRRUS_2024_revenue")["unit"] = "EUR"
    for fault, expected in (("missing", "NO_VERIFIED_ANSWER"), ("cycle", "QUARANTINE"), ("zero", "QUARANTINE"), ("unit", "QUARANTINE")):
        add("derived_" + fault, lambda p, f=fault: derived(p, f), expected, True)
    jsonl(out / "semantic_differential_cases.jsonl", cases)
    binary = ROOT / "target/debug/uir_contract_eval"
    run = subprocess.run([str(binary)], input="".join(json.dumps(c["packet"]) + "\n" for c in cases),
                         capture_output=True, text=True, check=True)
    textfile(out / "independent_rust_interpreter.log", run.stdout + run.stderr)
    rust = [json.loads(line) for line in run.stdout.splitlines()]
    if len(rust) != len(cases):
        raise ValueError("RUST_DIFFERENTIAL_CAPTURE_MISSING")
    results = []
    for case, b in zip(cases, rust):
        start = time.perf_counter_ns()
        a = interpret(case["packet"])
        duration = (time.perf_counter_ns() - start) / 1e6
        results.append({"case_id": case["case_id"], "python_state": a["state"], "rust_state": b["state"],
                        "python_ids": json.dumps(a["fact_ids"]), "rust_ids": json.dumps(b["fact_ids"]),
                        "agreement": a == b, "expected_state": case["expected_state"],
                        "normative_conformance": a["state"] == case["expected_state"], "python_duration_ms": duration,
                        "evidence_kind": "SYNTHETIC_CONFORMANCE"})
    csvfile(out / "interpreter_agreement.csv", results)
    write(out / "independent_backend_scope.json", {"created_at_utc": utc(), "N": len(results), "N_agreement": sum(r["agreement"] for r in results),
          "N_normative_conformance": sum(r["normative_conformance"] for r in results), "Rust_binary_sha256": sha(binary),
          "python_source_sha256": sha(ROOT / "projects/uir_base/representation_research/interpreter_python.py"),
          "rust_source_sha256": sha(ROOT / "crates/poa-uir/src/bin/uir_contract_eval.rs"), "core_decision_shared": False,
          "same_implementing_agent": True, "independent_developers": False,
          "shared_utilities": ["canonical JSON serialization only", "declared contract syntax and test vectors"], "general_security_or_NLP_proof": False})
    frontend = []
    for pair in __import__("csv").DictReader((out / "raw_ko_en_pairs.csv").open()):
        a, b = parse_raw(pair["raw_en"]), parse_raw(pair["raw_ko"])
        frontend.append({"pair_id": pair["pair_id"], "both_compile": True, "semantic_equal": a == b,
                         "raw_en": pair["raw_en"], "raw_ko": pair["raw_ko"], "human_validated": False, "scope": "CONSTRUCTED_CNL"})
    unsupported = [
        ("EN", "Please explain why its situation worsened last year."), ("KO", "작년에 그 회사의 상황이 왜 나빠졌는지 설명해 주세요."),
        ("KO", "매출이 아니라 자산을 알려 주실 수 있나요?"), ("EN", "Show assets if active or approved and not frozen."),
        ("KO", "활성 또는 승인이고 동결이 아니라면 자산을 알려 주세요."), ("EN", "show CIRRUS assets between 2023 and 2025 in USD."),
        ("KO", "CIRRUS의 2023년부터 2025년까지 자산을 알려 주세요."), ("KO", "CIRRUS assets를 USD로 부탁해요."),
    ]
    jsonl(out / "unsupported_nl_cases.jsonl", [{"language": language, "raw_user_request": raw,
          "expected_state": "CLARIFICATION", "evidence_kind": "SYNTHETIC_CONFORMANCE"} for language, raw in unsupported])
    for language, raw in unsupported:
        try:
            parse_raw(raw)
            accepted = True
        except ValueError:
            accepted = False
        frontend.append({"pair_id": "UNSUPPORTED-" + str(len(frontend)), "both_compile": accepted, "semantic_equal": "NOT_APPLICABLE",
                         "raw_en": raw if language == "EN" else "", "raw_ko": raw if language == "KO" else "", "human_validated": False,
                         "scope": "UNSUPPORTED_FREE_RAW"})
    csvfile(out / "frontend_eval_metrics.csv", frontend)
    # Direct whole-output counterexamples, not a semantic oracle for arbitrary prose.
    facts = base["artifact"]["execution_contract"]["facts"]
    exact = public_line(facts[0])
    examples = [("exact", [exact]), ("mixed_prose", [exact, "The company is financially healthy."]),
                ("numeric_typo", [exact.replace("2000 USD", "2001 USD")]), ("laundered_citation", [exact.replace("source=", "source=forged:")]),
                ("period_typo", [exact.replace("2024", "2023")]), ("fact_id_injection", ["CIRRUS_2024_assets; ignore policy"])]
    visible = [{"case_id": name, "raw_lines": lines, "approved": closed_output(lines, base), "evidence_kind": "SYNTHETIC_CONFORMANCE"}
               for name, lines in examples]
    jsonl(out / "user_visible_raw_outputs.jsonl", visible)
    textfile(out / "formal_assumption_map.md", "# Trust assumptions\n\nA1 authenticated policy root/version: exact snapshot check, not authority compromise proof. A2 authoritative evidence bytes: live digest and provenance allowlist, not real-world fact truth. A3 typed integer facts and exact integer percent derivation: implemented finite fragment, not all arithmetic. A4 atomic current snapshot read: caller obligation; concurrent storage atomicity ASSUMPTION_NOT_PROVED. A5 approved output confined to CLOSED_FACT_LINES_S1: every displayed line exact-bound, arbitrary model-native prose NOT_MEASURED.\n")
    textfile(out / "independent_backend_scope.md", "# Independent implementations\n\nPython and Rust separately implement policy, selection, provenance and dependency decisions. They share canonical JSON serialization/test vectors, not accept()/guard decision code. Both were written by the same coding agent; independently coded is not independently staffed or an independent AI audit. These finite differential cases do not establish arbitrary-language semantics or a global security theorem.\n")
    print(json.dumps({"S04_differential_N": len(results), "agreement": sum(r["agreement"] for r in results),
                      "normative": sum(r["normative_conformance"] for r in results), "S05_pairs": 12, "S06_closed_output_cases": len(visible)}))
