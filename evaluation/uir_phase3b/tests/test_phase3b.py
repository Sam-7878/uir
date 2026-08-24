import hashlib
import importlib.util
import json
import sys
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def load(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def jsonl(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]


def test_candidate_has_200_real_ko_en_pairs_without_case_deletion():
    rows = jsonl(ROOT / "evaluation/uir_phase3b/candidate_v2_0.jsonl")
    pairs = {}
    for row in rows:
        if row["category"] == "parallel_semantic": pairs.setdefault(row["pair_id"], []).append(row)
    assert len(rows) == 1200 and len(pairs) == 200
    assert all({x["language"] for x in pair} == {"ko", "en"} for pair in pairs.values())
    assert all(pair[0]["required_claims"] == pair[1]["required_claims"] for pair in pairs.values())


def test_real_fact_subset_is_balanced_and_hash_bound_to_frozen_sec():
    path = ROOT / "results/uir_phase3b/real_fact_subset.jsonl"
    rows = jsonl(path); manifest = json.loads((path.parent / "real_fact_subset_manifest.json").read_text())
    assert len(rows) == 200 and Counter(x["language"] for x in rows) == {"ko": 100, "en": 100}
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["dataset_sha256"]
    assert all(x["expected_claims"][0]["provenance"].startswith("sec-companyfacts://") for x in rows)


def test_b6_drops_unsupported_claim_and_discards_model_prose():
    module = load(ROOT / "evaluation/uir_slm/run_slm_campaign.py", "phase3b_campaign")
    verified = {"claim_type":"numeric_claim","entity_id":"AAPL","attribute":"assets","value":"10","unit":"USD","period":"2025","provenance":"sec"}
    unsupported = dict(verified, value="999")
    accepted, answer, status = module.filter_and_render([verified, unsupported], [verified], None)
    assert accepted == [verified] and "999" not in answer and status == "filtered"


def test_legacy_script_review_is_not_actual_model_provenance():
    fields = ("source_text_valid","language_valid","intent_valid","target_valid","conditions_valid","policy_valid","outcome_valid","claims_valid")
    import csv
    for reviewer in ("R1", "R2"):
        with (ROOT / f"evaluation/uir_phase3b/review/review_{reviewer}.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 1200
        assert all(row[field] in {"1", "0", "NA"} for row in rows for field in fields)
        assert "generation_interface" not in rows[0]
        assert "raw_response_sha256" not in rows[0]


def test_final_aggregator_emits_separated_statistics(tmp_path):
    dataset=[]; core=[]; raw=[]
    pipelines=["B0_DIRECT_SLM","B1_SLM_WITH_PROMPT_GUARD","B2_NAIVE_RAG_SLM","B3_RAG_WITH_ENTITY_VALIDATION","B4_UIR_POLICY_SLM","B5_FULL_UIR_OUTPUT_VALIDATION","B6_UIR_FILTER_AND_RENDER"]
    for language in ("ko","en"):
        cid=f"PAIR-{language}"; dataset.append({"case_id":cid,"pair_id":"PAIR-1"})
        core.append({"case_id":cid,"category":"parallel_semantic","language":language,"exact_structural_match":True,"semantic_match":True,"condition_ast_exact_match":True,"semantic_digest":"same","expected_policy_decision":"PERMIT","actual_policy_decision":"PERMIT","expected_outcome":"COMMIT","actual_outcome":"COMMIT","correct":True})
        for pipeline in pipelines:
            raw.append({"case_id":cid,"pipeline":pipeline,"suite":"frozen_v2","expected_outcome":"COMMIT","actual_outcome":"COMMIT","correct_outcome":True,"renderer_invoked":True,"generated_claims_data":[],"accepted_claims_data":[],"partial_answer":False,"entity_valid":True,"policy_valid":True,"attack_success":False,"policy_bypass":False,"entity_lock_violation":False,"renderer_invocation_on_reject_path":False,"format_error":None,"metrics":{"generated_claims":0,"supported_claims":0,"required_claims":0,"recalled_claims":0,"accepted_claims":0,"accepted_unsupported_claims":0},"latency":{"pipeline_total_us":10,"total_us":9,"validator_us":1}})
    def dump(path, rows): path.write_text("".join(json.dumps(x)+"\n" for x in rows),encoding="utf-8")
    data=tmp_path/"data.jsonl"; core_path=tmp_path/"core.jsonl"; raw_path=tmp_path/"raw.jsonl"; out=tmp_path/"out"
    dump(data,dataset);dump(core_path,core);dump(raw_path,raw)
    subprocess.run([sys.executable,str(ROOT/"evaluation/uir_phase3b/aggregate_final.py"),"--raw",str(raw_path),"--core",str(core_path),"--dataset",str(data),"--out",str(out)],check=True)
    assert (out/"stat_safety_final.csv").exists()
    assert (out/"stat_utility_final.csv").exists()
    assert (out/"stat_latency_final.csv").exists()
