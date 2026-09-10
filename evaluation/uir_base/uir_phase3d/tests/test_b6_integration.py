import importlib.util,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"evaluation/uir_slm"))
spec=importlib.util.spec_from_file_location("campaign",ROOT/"evaluation/uir_slm/run_slm_campaign.py")
campaign=importlib.util.module_from_spec(spec);spec.loader.exec_module(campaign)
spec2=importlib.util.spec_from_file_location("baselines",ROOT/"evaluation/uir_slm/baselines.py")
baselines=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(baselines)

def claim(value,attribute="revenue"):
    return {"claim_type":"numeric_claim","entity_id":"AAPL","attribute":attribute,"value":value,"unit":"USD","period":"2025","provenance":"sec-companyfacts://source#sha256=abc"}

def test_b6_keeps_supported_subset():
    a,c=claim("10"),claim("20","assets")
    accepted,_,_=campaign.filter_and_render([a,c],[a,c],None)
    assert accepted==[a,c]

def test_b6_removes_unsupported_subset():
    a,b,c=claim("10"),claim("999","invented"),claim("20","assets")
    accepted,text,status=campaign.filter_and_render([a,b,c],[a,c],None)
    assert accepted==[a,c] and "999" not in text and status=="filtered"

def test_b6_partial_answer_state():
    a,c=claim("10"),claim("20","assets")
    assert campaign.verified_answer_state([a],[a,c])=="PARTIAL_VERIFIED_ANSWER"

def test_b6_rejects_when_no_supported_claim():
    a,b=claim("10"),claim("999","invented")
    accepted,_,_=campaign.filter_and_render([b],[a],None)
    assert accepted==[] and campaign.verified_answer_state(accepted,[a])=="NO_VERIFIED_ANSWER"

def test_b6_policy_rejection_has_no_verified_answer_state():
    assert campaign.initial_output_state("B6_UIR_FILTER_AND_RENDER",False)=="NO_VERIFIED_ANSWER"

def test_b6_unsupported_acceptance_zero():
    a,b=claim("10"),claim("999","invented")
    accepted,_,_=campaign.filter_and_render([a,b],[a],None)
    assert b not in accepted

def test_compact_fact_ids_resolve_authoritative_numeric_unit_and_provenance():
    expected=[claim("9007199254740993.00")]
    prompt,catalog=baselines.fact_reference_prompt("verify",expected)
    assert "9007199254740993.00" not in prompt and "sha256" not in prompt
    supported,rejected=campaign.resolve_fact_references(["fact_001"],catalog)
    assert rejected==[] and supported==expected

def test_actual_audit_ingestion_rejects_script_only_judgment(tmp_path):
    spec3=importlib.util.spec_from_file_location("ingest",ROOT/"evaluation/uir_phase3d/ingest_actual_ai_reviews.py")
    ingest=importlib.util.module_from_spec(spec3);spec3.loader.exec_module(ingest)
    record={"reviewer_id":"AI-R1","engine":"AntiGravity Gemini 3.5 Flash","case_id":"C1","prompt_template_sha256":"p","judgment":{f:"1" for f in ingest.FIELDS}}
    path=tmp_path/"review.jsonl";path.write_text(__import__("json").dumps(record)+"\n")
    import pytest
    with pytest.raises(ValueError,match="provenance"):
        ingest.validate_file(path,"AI-R1","AntiGravity Gemini 3.5 Flash","p",{"C1"})
