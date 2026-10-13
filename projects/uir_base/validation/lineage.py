"""R01 case-level reconstruction of oracle-like historical fixture construction."""
from collections import Counter
from .common import FIELDS, FROZEN, OUT, ROOT, check_frozen, csvfile, jsonl, object_sha, read, sha, write

SOURCES = {
    "frozen_v1": ROOT / "projects/uir_base/evaluation/uir_external/frozen_test_v1.jsonl",
    "frozen_v2": ROOT / "archive/uir_base/results/uir_phase3b/frozen_test_v2.jsonl",
    "real_fact": ROOT / "archive/uir_base/results/uir_phase3b/real_fact_subset.jsonl",
}
GENERATORS = {
    "frozen_v1": ("projects/uir_base/evaluation/uir_external/generate_frozen_sets.py", "base_case assigns expected_claims=fact.claims; context_claims not provided"),
    "frozen_v2": ("projects/uir_base/evaluation/uir_phase3b/review_and_freeze.py", "campaign_record writes required_claims into both expected_claims and context_claims"),
    "real_fact": ("projects/uir_base/evaluation/uir_phase3b/generate_real_fact_subset.py", "claims(fact) assigned to both expected_claims and context_claims from selected registry fact"),
}


def keys(claims):
    return {tuple(str(c.get(k, "")) for k in FIELDS) for c in claims}


def run():
    check_frozen()
    originals = {(name, object_sha(r)): (i, r) for name, p in SOURCES.items() for i, r in enumerate(read(p), 1)}
    runtime = {r["case_id"]: r for r in read(FROZEN / "strong_runtime_600.jsonl")}
    scoring = {r["case_id"]: r for r in read(FROZEN / "strong_scoring_600.jsonl")}
    rows = []; traces = []
    for cid, gold in sorted(scoring.items()):
        eligible = gold.get("expected_outcome") == "COMMIT" and not any(gold.get(k, False) for k in ("is_adversarial", "is_invalid_entity", "is_policy_violation"))
        if not eligible:
            continue
        case = runtime[cid]; dataset = case["source_dataset"]
        line, original = originals[dataset, case["source_row_hash"]]
        if original.get("context_claims", []) != case["context_claims"]:
            raise ValueError("Runtime source-context transformation not reproduced")
        if (original.get("expected_claims") or original.get("context_claims") or []) != gold["expected_claims"]:
            raise ValueError("Scoring source-expected transformation not reproduced")
        context, expected = keys(case["context_claims"]), keys(gold["expected_claims"])
        classification = "A_ORACLE_LIKE_PRESELECTED" if context == expected and expected else "D_EMPTY_EVIDENCE" if not context else "OTHER"
        source, process = GENERATORS[dataset]
        provenance = sorted({c["provenance"] for c in gold["expected_claims"]})
        rows.append({"case_id": cid, "source_dataset": dataset, "original_source_ref": f"{SOURCES[dataset].relative_to(ROOT)}#line={line}",
                     "original_source_sha256": sha(SOURCES[dataset]), "source_row_hash": case["source_row_hash"],
                     "source_original_case_id": original["case_id"], "generator_ref": source, "generator_sha256": sha(ROOT / source),
                     "context_construction": process, "slot_construction": "freeze_inputs_phase4d derives requested_* from expected_semantics, assisted not raw-only",
                     "runtime_context_N": len(context), "gold_required_N": len(expected), "context_equals_gold": context == expected,
                     "cohort": classification, "source_document_provenance": "|".join(provenance),
                     "independent_request_retrieval": False,
                     "source_fact_universe": "registry_v1.jsonl selected source fact" if dataset in {"frozen_v1", "real_fact"} else "constructed required/verified facts only; larger universe not retained",
                     "physical_document_bytes_verified": False, "facts_origin_known": True,
                     "evidence_kind": "historical_reanalysis"})
        traces.append({"case_id": cid, "runtime": case, "evaluation_only": gold, "original_case": original,
                       "construction_refs": [source, "projects/uir_base/evaluation/uir_phase4d/freeze_inputs_phase4d.py"],
                       "runtime_fact_selection_is_oracle_like": classification == "A_ORACLE_LIKE_PRESELECTED"})
    counts = Counter(r["cohort"] for r in rows)
    if len(rows) != 418 or counts != {"A_ORACLE_LIKE_PRESELECTED": 290, "D_EMPTY_EVIDENCE": 128}:
        raise ValueError(f"Unexpected fixture partition {counts}")
    csvfile(OUT / "fixture_lineage_audit.csv", rows)
    jsonl(OUT / "fixture_lineage_scoring_only.jsonl", traces)
    write(OUT / "fixture_lineage_summary.json", {"N_eligible": 418, "cohorts": dict(counts),
          "source_dataset_by_cohort": {f"{d}/{c}": sum(r["source_dataset"] == d and r["cohort"] == c for r in rows) for d in SOURCES for c in counts},
          "runtime_fixture_uses_preselected_answer_facts": True, "runtime_assisted_slots_derived_from_expected_semantics": True,
          "direct_runtime_gold_file_access_proven": False,
          "historical_272_complete_template_scope": "oracle-like trusted-slot output-layer execution, not independent retrieval/semantic grounding"})
    print(dict(counts))


if __name__ == "__main__":
    run()
