"""Protocol-directed boundary probes; no gold is passed to either interpreter."""
from copy import deepcopy
import json
import subprocess

from uir_common.contracts import canonical_digest
from projects.uir_base.representation_research.dataset import source_first
from projects.uir_base.representation_research.evaluation import packet_for
from projects.uir_base.representation_research.interpreter_python import interpret
from .policy import ROOT, sha, utc


def cases():
    source, _ = source_first()
    row = {"raw_user_request": "show CIRRUS assets for 2024 in USD.", "source": source,
           "authority": {"version": "P1", "decision": "ALLOW", "approved": False},
           "context": {"active": True}, "action": "read"}
    base = packet_for(row)
    output = []
    def add(name, mutate, expected, *, reseal=True):
        packet = deepcopy(base)
        mutate(packet)
        if reseal:
            artifact = packet["artifact"]
            ex = artifact["execution_contract"]
            packet["current_evidence_sha256"] = canonical_digest({"version": ex["evidence_version"], "facts": ex["facts"], "trusted_provenance": ex["trusted_provenance"]})
            artifact["semantic_digest"] = canonical_digest({k: artifact[k] for k in
                ("semantics", "policy_constraints", "execution_contract", "output_contract")})
        output.append({"case_id": name, "packet": packet, "oracle_state": expected,
                       "split": "SYNTHETIC_CONFORMANCE", "oracle_basis": "DECLARED_FINITE_S1_BOUNDARIES_NOT_HUMAN_GOLD"})
    add("valid", lambda p: None, "FULL_VERIFIED_ANSWER")
    for value in (1, "true", "false"):
        add("approval_nonbool_" + str(value), lambda p, v=value: p["authority"].update(decision="APPROVAL", approved=v), "APPROVAL_PENDING")
    add("approval_true", lambda p: p["authority"].update(decision="APPROVAL", approved=True), "FULL_VERIFIED_ANSWER")
    add("unicode_integer", lambda p: p["artifact"]["execution_contract"]["facts"][0].update(value="２０００"), "QUARANTINE")
    for operation in (None, "", False):
        add("invalid_operation_" + str(operation), lambda p, op=operation: p["artifact"]["execution_contract"]["facts"][0].update(operation=op), "QUARANTINE")
    add("untyped_predicate_field", lambda p: p["artifact"]["semantics"].update(predicate={"op": "EQ_BOOL", "field": [], "value": True}), "CLARIFICATION")
    def derived(p, numerator, denominator, value):
        p["artifact"]["semantics"].update(metric="margin", unit="percent")
        for fact in p["artifact"]["execution_contract"]["facts"]:
            if fact["id"] == "CIRRUS_2024_profit": fact["value"] = str(numerator)
            if fact["id"] == "CIRRUS_2024_revenue": fact["value"] = str(denominator)
            if fact["id"] == "CIRRUS_2024_margin": fact["value"] = str(value)
    add("exact_large_integer_percent", lambda p: derived(p, 10**30 + 1, 100, 10**30 + 1), "FULL_VERIFIED_ANSWER")
    add("checked_intermediate_overflow", lambda p: derived(p, 2**126, 100, 2**126), "QUARANTINE")
    add("nonintegral_percent", lambda p: derived(p, 1, 3, 33), "QUARANTINE")
    add("zero_denominator", lambda p: derived(p, 1, 0, 0), "QUARANTINE")
    add("stale_policy", lambda p: p["authority"].update(version="revoked"), "QUARANTINE")
    add("stale_evidence", lambda p: p.update(current_evidence_version="revoked"), "QUARANTINE")
    add("digest_tamper", lambda p: p["artifact"].update(semantic_digest="0" * 64), "QUARANTINE", reseal=False)
    add("evidence_tamper", lambda p: p["artifact"]["execution_contract"]["facts"][0].update(value="999"), "QUARANTINE", reseal=False)
    add("duplicate_ids", lambda p: p["artifact"]["execution_contract"]["facts"].append(deepcopy(p["artifact"]["execution_contract"]["facts"][0])), "QUARANTINE")
    add("untrusted_provenance", lambda p: p["artifact"]["execution_contract"]["facts"][0].update(provenance="untrusted"), "QUARANTINE")
    add("unknown_schema", lambda p: p["artifact"]["execution_contract"].update(version="S2_UNSUPPORTED"), "QUARANTINE")
    add("deny", lambda p: p["authority"].update(decision="DENY"), "DENY")
    return output


def evaluate():
    probes = cases()
    binary = ROOT / "target/debug/uir_contract_eval"
    process = subprocess.run([str(binary)], input="".join(json.dumps(c["packet"]) + "\n" for c in probes),
                             text=True, capture_output=True, check=True, timeout=60)
    rust = [json.loads(line) for line in process.stdout.splitlines()]
    if len(rust) != len(probes):
        raise ValueError("RUST_ROW_COUNT_MISMATCH")
    records = []
    for case, other in zip(probes, rust, strict=True):
        python = interpret(case["packet"])
        records.append({**case, "python": python, "rust": other, "implementations_agree": python == other,
                        "both_match_oracle": python["state"] == other["state"] == case["oracle_state"],
                        "timestamp_utc": utc(), "model_digest": "NOT_APPLICABLE_NO_MODEL",
                        "independent_human_review": False})
    return {"N": len(records), "agreement": sum(r["implementations_agree"] for r in records),
            "oracle_matches": sum(r["both_match_oracle"] for r in records), "records": records,
            "python_source_sha256": sha(ROOT / "projects/uir_base/representation_research/interpreter_python.py"),
            "rust_binary_sha256": sha(binary), "rust_source_sha256": sha(ROOT / "crates/poa-uir/src/bin/uir_contract_eval.rs"),
            "scope": "FINITE_SYNTHETIC_S1_SINGLE_AGENT_NOT_CONFIRMATORY_NOT_DISTRIBUTED_SAFETY"}
