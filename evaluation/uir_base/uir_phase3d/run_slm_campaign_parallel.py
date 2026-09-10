#!/usr/bin/env python3
"""Case-parallel Phase3D runner; B5/B6 reuse each case's B4 generation."""
from __future__ import annotations
import argparse,json,sys,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SLM=Path(__file__).resolve().parents[1]/"uir_slm";EXT=Path(__file__).resolve().parents[1]/"uir_external"
sys.path.insert(0,str(SLM));sys.path.insert(0,str(EXT))
from baselines import PIPELINES,build_request
from claim_metrics import evaluate_claims,numeric_dimensions,parse_output,validate_against_facts
from ollama_client import OllamaClient
from registry_adapter import FrozenRegistry
from run_slm_campaign import filter_and_render,initial_output_state,parse_fact_reference_output,render_verified_claims,resolve_fact_references,verified_answer_state

def read(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--dataset",type=Path,required=True);ap.add_argument("--suite",required=True);ap.add_argument("--registry",type=Path,default=Path("evaluation/uir_external/registry_v1.jsonl"));ap.add_argument("--uir-records",type=Path,required=True);ap.add_argument("--config",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);ap.add_argument("--run-id",required=True);ap.add_argument("--workers",type=int,default=4);ap.add_argument("--limit",type=int);ap.add_argument("--pipelines",nargs="+",choices=PIPELINES,default=PIPELINES);a=ap.parse_args()
    cases=read(a.dataset);cases=cases[:a.limit] if a.limit else cases;registry=FrozenRegistry(a.registry);uir={x["case_id"]:x for x in read(a.uir_records)};client=OllamaClient(a.config);config=client.config["deterministic"].copy()
    def process(case):
        local={};records=[]
        for pipeline in a.pipelines:
            request=build_request(pipeline,case,registry,uir.get(case["case_id"]));reused=False;model_fact_refs=[];finish_reason="not_invoked"
            if not request.invoke_renderer:
                raw="";answer="";generated=[];error=None;lat={"total_us":0,"prompt_eval_us":0,"generation_us":0,"load_us":0,"prompt_tokens":0,"output_tokens":0};actual="REJECT"
            else:
                source=local.get("B4_UIR_POLICY_SLM") if pipeline in {"B5_FULL_UIR_OUTPUT_VALIDATION","B6_UIR_FILTER_AND_RENDER"} else None
                if source:
                    raw=source["raw_output"];answer=source["answer"];model_fact_refs=source["model_fact_refs"];error=source["format_error"];finish_reason=source["finish_reason"];lat=source["latency"].copy();reused=True
                else:
                    result=client.generate(request.prompt,request.system,config,request.response_schema);raw=result.text;finish_reason=str(result.raw.get("done_reason","unknown"));lat={"total_us":result.latency_us,"prompt_eval_us":result.prompt_eval_us,"generation_us":result.generation_us,"load_us":result.load_us,"prompt_tokens":result.prompt_tokens,"output_tokens":result.output_tokens}
                    if request.output_mode=="fact_refs":answer,model_fact_refs,error=parse_fact_reference_output(raw)
                    else:answer,generated,error=parse_output(raw)
                if request.output_mode=="fact_refs":resolved,invalid=resolve_fact_references(model_fact_refs,request.fact_catalog or {});generated=[*resolved,*invalid]
                actual="ABORT" if error else "COMMIT"
            expected=case.get("expected_claims",[]);started=time.perf_counter_ns();supported,rejected=validate_against_facts(generated,expected);validator_us=(time.perf_counter_ns()-started)//1000;lat["validator_us"]=validator_us if pipeline in {"B5_FULL_UIR_OUTPUT_VALIDATION","B6_UIR_FILTER_AND_RENDER"} else 0;lat["pipeline_total_us"]=lat["total_us"]+lat["validator_us"]
            accepted=generated;validation="not_applied";state=initial_output_state(pipeline,request.invoke_renderer)
            if pipeline=="B5_FULL_UIR_OUTPUT_VALIDATION" and request.invoke_renderer:
                validation="rejected" if rejected or error else "accepted";accepted=[] if rejected or error else supported;actual="REJECT" if rejected or error else "COMMIT";state=verified_answer_state(accepted,expected)
            elif pipeline=="B6_UIR_FILTER_AND_RENDER" and request.invoke_renderer:
                accepted,answer,validation=filter_and_render(generated,expected,error);answer=render_verified_claims(accepted);state=verified_answer_state(accepted,expected);actual="COMMIT" if accepted or not expected else "REJECT"
            metrics=evaluate_claims(expected,generated,accepted);numeric=numeric_dimensions(expected,accepted) if a.suite=="real_fact" else {};target=(case.get("expected_semantics") or {}).get("target");expected_outcome=case.get("expected_outcome","REJECT")
            record={"run_id":a.run_id,"suite":a.suite,"case_id":case["case_id"],"pipeline":pipeline,"model":client.config["model"],"seed":config["seed"],"temperature":config["temperature"],"language":case.get("language"),"category":case.get("category"),"split":case.get("split"),"attack_type":case.get("attack_type"),"numeric_type":case.get("numeric_type"),"expected_outcome":expected_outcome,"policy_valid":case.get("policy_valid",True),"entity_valid":case.get("entity_valid",False),"actual_outcome":actual,"correct_outcome":actual==expected_outcome,"renderer_invoked":request.invoke_renderer,"renderer_reused":reused,"rejection_reason":request.rejection_reason,"output_validation":validation,"output_state":state,"raw_output":raw,"answer":answer,"model_fact_refs":model_fact_refs,"generated_claims_data":generated,"accepted_claims_data":accepted,"format_error":error,"finish_reason":finish_reason,"generation_budget_tokens":config["max_new_tokens"],"json_truncated":finish_reason=="length" or (bool(error) and lat["output_tokens"]>=config["max_new_tokens"]),"latency":lat,"metrics":{**metrics,**numeric},"partial_answer":state=="PARTIAL_VERIFIED_ANSWER","attack_success":expected_outcome=="REJECT" and bool(accepted),"policy_bypass":not case.get("policy_valid",True) and request.invoke_renderer,"entity_lock_violation":any(target and c.get("entity_id")!=target for c in accepted),"renderer_invocation_on_reject_path":pipeline in {"B4_UIR_POLICY_SLM","B5_FULL_UIR_OUTPUT_VALIDATION","B6_UIR_FILTER_AND_RENDER"} and expected_outcome=="REJECT" and request.invoke_renderer}
            records.append(record);local[pipeline]=record
        return records
    a.out.parent.mkdir(parents=True,exist_ok=True);done=0;started=time.monotonic()
    # Only publish a complete campaign.  executor.map preserves dataset order while
    # still evaluating cases concurrently, which makes hashes reproducible.
    temporary=a.out.with_name(a.out.name+".partial")
    with temporary.open("w",encoding="utf-8",newline="\n") as handle,ThreadPoolExecutor(max_workers=a.workers) as pool:
        for records in pool.map(process,cases):
            for record in records:handle.write(json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
            handle.flush();done+=1
            if done%25==0:print(json.dumps({"cases_completed":done,"cases_total":len(cases),"elapsed_s":round(time.monotonic()-started,1)}),flush=True)
    temporary.replace(a.out)
if __name__=="__main__":main()
