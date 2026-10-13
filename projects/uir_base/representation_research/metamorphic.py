"""Actual fixed-catalog query/distractor/removal relations; development only."""
from copy import deepcopy
from .common import read, jsonl
from .evaluation import packet_for
from .interpreter_python import interpret


def run(out):
    original = read(out / "runtime/query_aware_dev.jsonl")[0]
    pairs = []
    a = deepcopy(original)
    b = deepcopy(a)
    b["raw_user_request"] = "show CIRRUS revenue for 2024 in USD."
    left, right = interpret(packet_for(a)), interpret(packet_for(b))
    pairs.append({"relation": "fixed_catalog_query_metric_changes_subset", "left": left, "right": right,
                  "passed": left["fact_ids"] != right["fact_ids"], "evidence_kind": "SYNTHETIC_CONFORMANCE"})
    b = deepcopy(a)
    distractor = deepcopy(b["source"]["facts"][0])
    distractor.update(id="IRRELEVANT_NEW", entity="NOT_REQUESTED", value="42")
    b["source"]["facts"].append(distractor)
    right = interpret(packet_for(b))
    pairs.append({"relation": "new_distractor_does_not_change_requested_subset", "left": left, "right": right,
                  "passed": left == right, "evidence_kind": "SYNTHETIC_CONFORMANCE"})
    b = deepcopy(a)
    b["source"]["facts"] = [f for f in b["source"]["facts"] if f["id"] != "CIRRUS_2024_assets"]
    right = interpret(packet_for(b))
    pairs.append({"relation": "remove_requested_evidence_safe_none", "left": left, "right": right,
                  "passed": right["state"] == "NO_VERIFIED_ANSWER", "evidence_kind": "SYNTHETIC_CONFORMANCE"})
    jsonl(out / "metamorphic_pairs.jsonl", pairs)
    if not all(pair["passed"] for pair in pairs):
        raise ValueError("METAMORPHIC_RELATION_FAILED")
