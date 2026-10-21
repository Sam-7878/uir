"""Post-hoc trusted-resolver control on the already observed V3.2 fixtures.

No LLM, no oracle access in resolve(), no claim of an unseen holdout experiment.
"""
import json
import time

from evaluation.llm_security_v3_2.provenance import ProvenanceVerifier
from evaluation.llm_security_v3_2.judges.security_evaluator import SecurityEvaluatorV32
from evaluation.llm_security_v3_2.schema.oracle_case import OracleCase
from llm_trust.security.output_guard import OutputGuard

from .common import FROZEN, TASK, csv_write, load, write


def resolve(runtime):
    start=time.perf_counter();result={'model_output':'','final_output':'[NO_VERIFIED_RECORD]',
        'terminal_status':'BLOCKED','llm_invoked':False,'executed_tool_calls':[],
        'mock_state_mutations':[],'resource_usage':{'input_tokens':0,'output_tokens':0,'retrieval_ops':0}}
    verifier=ProvenanceVerifier()
    for doc in runtime['retrieved_context']:
        result['resource_usage']['retrieval_ops']+=1
        evidence=verifier.verify_record(raw_source_id=doc['source_id'],content=doc['content'],
            provided_sha256=doc.get('sha256'),signer_id=doc.get('signer'),signature=doc.get('signature'))
        if not evidence.is_authoritative():continue
        try:claim=json.loads(doc['content'])
        except ValueError:continue
        if not isinstance(claim,dict) or not {'entity','metric','value','fiscal_year'}<=set(claim):continue
        candidate={k:claim[k] for k in ('entity','metric','value','fiscal_year')}
        candidate['citations']=[doc['source_id']]
        raw=json.dumps(candidate)
        verdict=OutputGuard().validate(raw,expected_schema_id='financial_summary_v3_2',
            admissible_evidence_ids={doc['source_id']},evidence_claims={doc['source_id']:claim})
        if verdict.is_safe:
            result.update(final_output=verdict.sanitized_output,terminal_status='ALLOWED');break
    result['latency_ms']=(time.perf_counter()-start)*1000
    return result


def main():
    runtime=load(FROZEN/'datasets/runtime.json');oracles={r['case_id']:r for r in load(FROZEN/'datasets/oracle.json')}
    evaluator=SecurityEvaluatorV32();records=[]
    for rc in runtime:
        execution=resolve(rc);verdict=evaluator.evaluate_case(execution,OracleCase.from_dict(oracles[rc['case_id']]))
        records.append({'case_id':rc['case_id'],'is_attack':oracles[rc['case_id']]['is_attack'],
                        'execution':execution,'verdict':verdict,'mcr_applicable':False})
    benign=[r for r in records if not r['is_attack']];attacks=[r for r in records if r['is_attack']]
    summary={'control':'trusted resolver + deterministic JSON validator; no LLM','observational_scope':'post-hoc previously observed V3.2 fixture population',
             'attack_n':len(attacks),'benign_n':len(benign),'mcr':None,
             'e2e_count':sum(r['verdict']['e2e_attack_succeeded'] for r in attacks),
             'complete_benign':sum(r['verdict']['complete_task_success'] for r in benign),
             'false_rejections':sum(r['verdict']['false_rejection'] for r in benign),
             'latency_mean_ms':sum(r['execution']['latency_ms'] for r in records)/len(records),
             'limitation':'original attack oracle is not a general usefulness oracle for this deterministic lookup; no exposed-model MCR exists'}
    write(TASK/'data/no_llm_control_runs.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    write(TASK/'data/no_llm_control_summary.json',summary)
    historic=load(FROZEN/'baseline_comparison.json')['HETE']
    csv_write(TASK/'data/incremental_value.csv',[
        {'system':'trusted_resolver_no_llm','scope':'posthoc V3.2','benign_n':250,'complete_utility':summary['complete_benign'],
         'e2e_count':summary['e2e_count'],'mcr_count':'not applicable','mean_latency_ms':summary['latency_mean_ms']},
        {'system':'HETE_Qwen_historical','scope':'frozen V3.2','benign_n':250,'complete_utility':historic['utility']['count'],
         'e2e_count':historic['e2e']['count'],'mcr_count':historic['mcr']['count'],'mean_latency_ms':historic['latency_mean_ms']}])
    write(TASK/'reports/NO_LLM_CONTROL.md','# Deterministic resolver control\n\n'+json.dumps(summary,indent=2)+'\n\n'
          'This diagnostic highlights that the existing fixture has trusted numeric answers already encoded in authenticated evidence. '
          'It cannot establish a semantic incremental benefit from inserting an LLM. Latency is measured on the current hardware; historical HETE latency is from a different environment and is not a controlled speedup comparison. '
          'Minimal-envelope and typed-adapter comparisons use the same new AgentDojo tasks and local models, rather than recycling incompatible historical prompts.\n')
    print(json.dumps(summary))


if __name__=='__main__':main()
