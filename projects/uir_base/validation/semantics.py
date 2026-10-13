"""Synthetic minimal pairs/dependency projection, not human NL judgments."""
import json
from uir_common.representation import TypedRequest, accept, catalog, deterministic_candidate
from .common import OUT, csvfile, jsonl, write
from .frontends import compile_shared


def run():
    source = catalog([], "EPAIR")
    policy = {"version": "PPAIR", "decision": "ALLOW"}
    pairs = [
        ("equivalent", "verify D001 revenue 2025 in USD", "D001의 2025년 매출 검증 단위 USD"),
        ("equivalent", "verify D001 revenue 2025 if approval AND entity_verified", "D001의 2025년 매출 검증 조건: 기업확인 그리고 승인"),
        ("equivalent", "verify D001 revenue 2025 unless NOT approval", "D001의 2025년 매출 검증 조건: 승인"),
        ("equivalent", "verify D001 revenue 2025 if value > 10", "D001의 2025년 매출 검증 조건: 값 > 10"),
        ("different", "verify D001 revenue 2025 if approval AND entity_verified", "verify D001 revenue 2025 if approval OR entity_verified"),
        ("different", "verify D001 revenue 2025 if NOT approval", "verify D001 revenue 2025 if approval"),
        ("different", "verify D001 revenue 2025 in USD", "verify D001 revenue 2025 in KRW"),
        ("different", "verify D001 revenue 2025", "verify D001 revenue 2024"),
        ("different", "verify D001 revenue 2025", "verify D002 revenue 2025"),
        ("different", "verify D001 revenue 2025 if value > 10", "verify D001 revenue 2025 if value >= 10"),
        ("clarification", "verify D001 revenue 2025 if approval", "verify D001 revenue 2025 if invented_predicate"),
        ("clarification", "verify D001 revenue 2025", "Tell me everything about D001"),
    ]
    records = []
    for index, (relation, left, right) in enumerate(pairs):
        observed = []
        for text in (left, right):
            try:
                request = compile_shared(text, policy, source)
                observed.append({"state": "COMPILED", "ast": request.plan(), "digest": request.digest})
            except ValueError as exc:
                observed.append({"state": "CLARIFICATION", "ast": None, "digest": None, "reason": str(exc)})
        equal = observed[0]["digest"] == observed[1]["digest"]
        passed = equal if relation == "equivalent" else not equal if relation == "different" else observed[1]["state"] == "CLARIFICATION"
        records.append({"pair_id": f"PAIR-R-{index}", "expected_relation": relation, "raw_left": left, "raw_right": right,
                        "observed": observed, "passed": passed, "expected_source": "prespecified executable CNL relation, not human semantic gold",
                        "evidence_kind": "synthetic_conformance"})
    jsonl(OUT / "bilingual_raw_only_conformance.jsonl", records)
    csvfile(OUT / "semantic_pair_manifest.csv", [{"pair_id": r["pair_id"], "expected_relation": r["expected_relation"], "passed": r["passed"]} for r in records])
    # Explicit dependency graph traces, including a missing denominator projection.
    base = {"claim_type": "numeric_claim", "entity_id": "D001", "attribute": "revenue", "value": "100", "unit": "USD",
            "period": "2025", "provenance": "fixture://semantic/revenue"}
    graph = catalog([base, {**base, "attribute": "net_income", "value": "10", "provenance": "fixture://semantic/income"},
                     {**base, "claim_type": "derived_claim", "attribute": "ratio", "value": "0.1", "unit": "1", "provenance": "derived://semantic/divide"}], "E1")
    ids = {v["attribute"]: k for k, v in graph["facts"].items()}
    graph["dependencies"][ids["ratio"]] = [ids["net_income"], ids["revenue"]]
    graph["derivations"][ids["ratio"]] = {"op": "divide", "args": [ids["net_income"], ids["revenue"]]}
    request = TypedRequest("D001", "ratio", "2025", "1", None, "read", "P1", "E1")
    authority = {"version": "P1", "decision": "ALLOW"}
    tests = []
    for refs, partial in ((list(ids.values()), True), ([ids["ratio"], ids["net_income"]], True), ([ids["ratio"]], True),
                          ([ids["ratio"], ids["net_income"]], False)):
        candidate = json.dumps({"contract_digest": request.digest, "fact_ids": refs})
        result = accept(request.plan(), graph, authority, {}, candidate, identity=request.digest, partial=partial)
        tests.append({"raw_candidate": candidate, "partial_enabled": partial, "dependency_graph": graph["dependencies"], "result": result,
                      "evidence_kind": "synthetic_conformance"})
    jsonl(OUT / "dependency_projection_tests.jsonl", tests)
    write(OUT / "semantic_conformance_summary.json", {"N_pairs": len(records), "N_pass": sum(r["passed"] for r in records),
          "general_free_NL_accuracy": "NOT_MEASURED", "human_validation": False,
          "dependency_outcomes": [t["result"]["state"] for t in tests]})
    print(f"{sum(r['passed'] for r in records)}/{len(records)} synthetic minimum pairs passed.")


if __name__ == "__main__":
    run()
