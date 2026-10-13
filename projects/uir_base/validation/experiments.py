"""R03--R06 preregistered engineering conformance, fair representation controls."""
import argparse
from collections import Counter
import json
import time
from uir_common.contracts import canonical_digest, reject_gold
from uir_common.representation import (TypedRequest, FULL_SCHEMA, REFERENCE_SCHEMA, FIELDS,
                                      accept, admissible, catalog, deterministic_candidate, eligible_facts)
from .common import DOC, OUT, ROOT, check_frozen, csvfile, jsonl, load, object_sha, read, sha, utc, write
from .frontends import compile_shared, specialized_plan

CONDITIONS = ("UIR_SHARED_TYPED", "SPECIALIZED_STRUCTURED_NO_SHARED_UIR")
MODES = ("raw_only_CNL", "trusted_slot_assisted", "unsupported_free_NL")


def build_packets():
    """Create fact universes before runtime selection; no gold-based retrieval."""
    cases = []; scoring = []
    for index in range(24):
        entity = f"RD{index:03d}"; period = "2025"; family = f"RFAMILY-{index:03d}"
        base = {"claim_type": "numeric_claim", "entity_id": entity, "attribute": "revenue", "value": str(1000 + index),
                "unit": "USD", "period": period, "provenance": f"fixture://r-stage/source/{entity}/rev"}
        universe = [base, {**base, "attribute": "net_income", "value": str(100 + index), "provenance": f"fixture://r-stage/source/{entity}/net"},
                    {**base, "entity_id": "DISTRACTOR", "value": "999"}, {**base, "period": "2024", "value": "700"},
                    {**base, "unit": "KRW", "value": "1500000"}]
        variant = index % 8
        policy = {"version": "PDEV1", "decision": "ALLOW", "approved": False}
        action = "read"; context = {"approval": True, "entity_verified": True, "verified_provenance": True, "value": "100"}
        if variant == 1: policy["decision"] = "DENY"
        if variant == 2: policy["decision"] = "REQUIRE_APPROVAL"
        if variant == 3: policy.update(decision="REQUIRE_APPROVAL", approved=True)
        if variant == 4: policy["decision"] = "READ_ONLY"; action = "write"
        if variant == 5: universe = universe[1:]
        if variant == 6: universe.append({**base, "value": "4321", "provenance": f"fixture://r-stage/source/{entity}/conflict"})
        if variant == 7: context["approval"] = False
        source = catalog(universe, "EDEV1")
        p1 = {"field": "approval", "op": "==", "type": "BOOLEAN", "value": True}
        p2 = {"field": "entity_verified", "op": "==", "type": "BOOLEAN", "value": True}
        predicate = {"op": "AND", "args": sorted([p1, p2], key=canonical_digest)}
        slots = {"entity": entity, "attribute": "revenue", "period": period, "unit": "USD", "predicate": predicate}
        expected_state = {0: "FULL_VERIFIED_ANSWER", 1: "DENY", 2: "APPROVAL_PENDING", 3: "FULL_VERIFIED_ANSWER",
                          4: "READ_ONLY", 5: "NO_VERIFIED_ANSWER", 6: "QUARANTINE", 7: "DENY"}[variant]
        for language, text in (("en", f"verify {entity} revenue {period} in USD if approval AND entity_verified"),
                               ("ko", f"{entity}의 {period}년 매출 검증 단위 USD 조건: 기업확인 그리고 승인")):
            for mode in MODES:
                cid = f"RDEV-{index:03d}-{language}-{mode}"
                request_text = text if mode != "unsupported_free_NL" else f"Could you reason about performance for {entity}?"
                runtime = {"case_id": cid, "source_family_id": family, "language": language, "input_mode": mode, "raw_request": request_text,
                           "source_catalog": source, "source_document_id": f"fixture://r-stage/source/{entity}", "policy": policy,
                           "condition_context": context, "action": action, "assisted_slots": slots if mode == "trusted_slot_assisted" else None,
                           "cohort": "B_NON_ORACLE_FIXED_CATALOG" if variant != 5 else "D_INCOMPLETE_EVIDENCE",
                           "evidence_kind": "synthetic_conformance", "split": "DEVELOPMENT_NOT_GENERALIZATION"}
                reject_gold(runtime); cases.append(runtime)
                scoring.append({"case_id": cid, "expected_slots": slots, "expected_state": expected_state if mode != "unsupported_free_NL" else "CLARIFICATION",
                                "expected_claims": [base] if expected_state == "FULL_VERIFIED_ANSWER" and mode != "unsupported_free_NL" else [],
                                "annotation_kind": "constructed executable fixture, not human gold"})
    return cases, scoring


def prepare():
    check_frozen()
    cases, scoring = build_packets()
    jsonl(OUT / "comparison_runtime.jsonl", cases)
    jsonl(OUT / "comparison_scoring_only.jsonl", scoring)
    csvfile(OUT / "comparison_case_manifest.csv", [{"case_id": r["case_id"], "family": r["source_family_id"], "mode": r["input_mode"],
                                                 "language": r["language"], "cohort": r["cohort"]} for r in cases])
    write(OUT / "non_oracle_dev_manifest.json", {"N_cases": len(cases), "N_source_families": 24, "runtime_sha256": sha(OUT / "comparison_runtime.jsonl"),
          "runtime_fact_selection": "only typed request and catalog; catalog contains unrelated entities/attributes/periods/units",
          "gold_generation": "evaluation file built after runtime packets; synthetic normative variant states",
          "human_gold": False, "new_unused_holdout": False})
    sources = [ROOT / "src/uir_common/representation.py", ROOT / "projects/uir_base/validation/frontends.py", ROOT / "projects/uir_base/validation/experiments.py"]
    write(OUT / "repr_ablation_protocol_v1.json", {"status": "FROZEN_BEFORE_EXECUTION", "created_at_utc": utc(),
          "conditions": CONDITIONS, "input_modes": MODES, "N_cases": len(cases), "replications": 5, "seed": 20261012,
          "primary_endpoint": "joint expected state + exact accepted claim set on all synthetic cases; unknown/invalid incorrect, never dropped",
          "primary_comparison_family": ["UIR-vs-equivalent-specialized_joint_conformance"],
          "secondary": ["pair AST/digest", "eligible authority set", "supported accepted coverage", "parser state", "deterministic latency"],
          "bootstrap": "paired family cluster, all language/mode rows retained, 10000 reps",
          "capability_control": "same lexical parser, condition evaluator, policy and exact support guard; no weaker control",
          "no_UIR_scope": "task-specific structured dict with equivalent fields, no shared public typed artifact; not unstructured pipeline",
          "claim_rule": "equal behavior is not superiority; compositional reuse is an explicit implementation/conformance property, not measured human development effort",
          "runtime_sha256": sha(OUT / "comparison_runtime.jsonl"),
          "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in sources},
          "inference_calls": 0, "confirmatory_status": "NO_FAMILY_DISJOINT_HOLDOUT", "evidence_kind": "synthetic_conformance"})
    csvfile(DOC / "matched_baseline_capability_matrix.csv", [{"condition": c, "lexical_parser": "shared CNL vNext",
            "catalog": "identical non-oracle fixed catalog", "policy": "identical authenticated context", "tools": "read/write sandbox opportunities",
            "output_guard": "same exact support validator", "renderer": "same deterministic bound-claim renderer",
            "public_shared_IR": c == CONDITIONS[0]} for c in CONDITIONS])
    write(DOC / "uir_contract_vNext.schema.json", {"version": "uir-representation-vNext-1", "full_claim_candidate": FULL_SCHEMA,
          "reference_candidate": REFERENCE_SCHEMA, "authority_fields": list(FIELDS), "numeric_unit_period_unknown": "REJECT"})
    print(f"Frozen {len(cases)} development cases / 24 families; no generalization holdout claim.")


def execute():
    protocol = load(OUT / "repr_ablation_protocol_v1.json")
    for rel, digest in protocol["source_sha256"].items():
        if sha(ROOT / rel) != digest: raise ValueError("FROZEN_REPRESENTATION_SOURCE_CHANGED")
    if sha(OUT / "comparison_runtime.jsonl") != protocol["runtime_sha256"]:
        raise ValueError("FROZEN_COMPARISON_COHORT_CHANGED")
    expected = {r["case_id"]: r for r in read(OUT / "comparison_scoring_only.jsonl")}
    results = []; raw = []; latencies = []; backends = []
    for case in read(OUT / "comparison_runtime.jsonl"):
        reject_gold(case)
        for condition in CONDITIONS:
            start = time.perf_counter_ns(); error = None; artifact = None
            try:
                if condition == CONDITIONS[0]:
                    request = compile_shared(case["raw_request"], case["policy"], case["source_catalog"], assisted=case["assisted_slots"], action=case["action"])
                    artifact = request.artifact({"language": case["language"], "case_id": case["case_id"]})
                    request = TypedRequest.from_artifact(artifact)
                    plan, identity = request.plan(), request.digest
                else:
                    plan = specialized_plan(case["raw_request"], case["policy"], case["source_catalog"], assisted=case["assisted_slots"], action=case["action"])
                    identity = canonical_digest(plan)
                gate = admissible(plan, case["source_catalog"], case["policy"], case["condition_context"])
                candidate = deterministic_candidate(plan, case["source_catalog"], identity) if gate == "ADMISSIBLE" else json.dumps({"contract_digest": identity, "fact_ids": []})
                observed = accept(plan, case["source_catalog"], case["policy"], case["condition_context"], candidate, identity=identity)
                # Second backend: serialize full seven-field claims through the same guard.
                full = json.dumps({"contract_digest": identity, "claims": list(eligible_facts(plan, case["source_catalog"]).values())}) if gate == "ADMISSIBLE" else json.dumps({"contract_digest": identity, "claims": []})
                other = accept(plan, case["source_catalog"], case["policy"], case["condition_context"], full, mode="full", identity=identity)
                backends.append({"case_id": case["case_id"], "condition": condition, "reference_state": observed["state"], "seven_field_state": other["state"],
                                 "authorization_equal": observed["authorization"] == other["authorization"],
                                 "accepted_sets_equal": observed["accepted_claims"] == other["accepted_claims"], "state_equal": observed["state"] == other["state"],
                                 "evidence_kind": "synthetic_conformance", "actual_model_calls": 0})
            except ValueError as exc:
                observed = {"state": "CLARIFICATION", "accepted_claims": [], "accepted_rendered_text": "", "contract_digest": None,
                            "eligible_fact_ids": [], "accepted_fact_ids": []}
                plan = None; candidate = None; error = str(exc)
            duration = (time.perf_counter_ns() - start) / 1e6
            gold = expected[case["case_id"]]
            match = observed["state"] == gold["expected_state"] and observed["accepted_claims"] == gold["expected_claims"]
            results.append({"case_id": case["case_id"], "family": case["source_family_id"], "condition": condition,
                "input_mode": case["input_mode"], "language": case["language"], "state": observed["state"], "expected_state": gold["expected_state"],
                "joint_conformance": match, "accepted_nonempty": bool(observed["accepted_claims"]), "complete": observed["state"] == "FULL_VERIFIED_ANSWER",
                "schema_or_parser_error": error, "contract_digest": observed["contract_digest"], "whole_output_scope": "DETERMINISTIC_BOUND_CLAIM_RENDERER",
                "native_prose_AUCR": "NOT_MEASURED", "evidence_kind": "synthetic_conformance"})
            raw.append({"case_id": case["case_id"], "condition": condition, "runtime_packet": case, "artifact": artifact, "specialized_plan": plan if artifact is None else None,
                        "candidate": candidate, "accepted_output": observed, "model_invoked": False, "evidence_kind": "synthetic_conformance"})
            latencies.append({"case_id": case["case_id"], "condition": condition, "repetition": 0, "duration_ms": duration,
                              "inference_calls": 0, "scope": "initial load-inclusive Python deterministic path"})
            if plan is not None:
                for repeat in range(1, protocol["replications"] + 1):
                    t = time.perf_counter_ns()
                    accept(plan, case["source_catalog"], case["policy"], case["condition_context"], candidate, identity=observed["contract_digest"])
                    latencies.append({"case_id": case["case_id"], "condition": condition, "repetition": repeat, "duration_ms": (time.perf_counter_ns() - t) / 1e6,
                                      "inference_calls": 0, "scope": "warm guard+renderer only; not whole frontend or transformer"})
    csvfile(OUT / "dev_matched_results.csv", results)
    jsonl(OUT / "dev_matched_raw.jsonl", raw)
    jsonl(OUT / "backend_conformance_results.jsonl", backends)
    jsonl(OUT / "latency_instrumentation.jsonl", latencies)
    csvfile(OUT / "repr_summary.csv", [{"condition": c, "N": len([r for r in results if r["condition"] == c]),
          "N_joint_conformant": sum(r["joint_conformance"] for r in results if r["condition"] == c),
          "N_nonempty_accepted": sum(r["accepted_nonempty"] for r in results if r["condition"] == c),
          "N_clarification": sum(r["state"] == "CLARIFICATION" for r in results if r["condition"] == c),
          "N_model_calls": 0, "general_NL_accuracy": "NOT_MEASURED"} for c in CONDITIONS])
    write(OUT / "repr_execution_manifest.json", {"status": "EXECUTED_SYNTHETIC_DEVELOPMENT", "created_at_utc": utc(),
          "protocol_sha256": sha(OUT / "repr_ablation_protocol_v1.json"), "N_rows": len(results),
          "N_conformant": sum(r["joint_conformance"] for r in results), "backend_N": len(backends),
          "backend_N_equal": sum(all(r[k] for k in ("authorization_equal", "accepted_sets_equal", "state_equal")) for r in backends),
          "raw_sha256": sha(OUT / "dev_matched_raw.jsonl"), "model_calls": 0, "physical_independence": False})
    print(Counter(r["state"] for r in results))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--prepare", action="store_true"); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.prepare: prepare()
    elif args.execute: execute()
    else: parser.error("Explicit --prepare or --execute")
