"""Independent raw-evidence auditor; unfavorable outcomes never invalidate experiments."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from collections import Counter
REPO=Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:sys.path.insert(0,str(REPO))
from evaluation.llm_security_v3_2.closure_campaign import SYSTEMS, ABLATIONS, CAMPAIGNS, rows, summarize, digest, write, source_hashes
from evaluation.llm_security_v3_2.schema.oracle_case import OracleCase
from evaluation.llm_security_v3_2.judges.security_evaluator import SecurityEvaluatorV32
from evaluation.llm_security_v3_2.stats.exact_mcnemar import exact_mcnemar_test,holm_bonferroni_correction

class Auditor:
    def __init__(self,path):self.path=Path(path);self.failures=[];self.observed={};self.evaluator=SecurityEvaluatorV32()
    def check(self,test,condition):
        if not condition:self.failures.append(test)
    def read(self,name):
        try:return json.loads((self.path/name).read_text())
        except (OSError,ValueError):self.failures.append('Missing or invalid '+name);return {}
    def raw(self,name):
        try:return rows(self.path/'raw_runs'/f'{name}.jsonl')
        except (OSError,ValueError):self.failures.append('Malformed raw '+name);return []
    def same(self,name,actual,expected):
        self.check(name,actual==expected)
    def check_record(self,r,oracles,label):
        cid=r.get('oracle_case_id');oc=oracles.get(cid)
        self.check(label+': known oracle',oc is not None)
        if not oc:return
        self.same(label+': class',r.get('attack_class'),oc.attack_class)
        self.same(label+': is_attack',r.get('is_attack'),oc.is_attack)
        execution=r.get('execution',{});calls=r.get('calls',[])
        self.same(label+': replayed verdict',r.get('verdict'),self.evaluator.evaluate_case(execution,oc))
        self.same(label+': runtime hash',r.get('runtime_hash'),digest(r.get('runtime_case',{})))
        self.same(label+': invocation evidence',execution.get('llm_invoked'),bool(calls))
        self.check(label+': fallback explicitly false',execution.get('fallback_used') is False)
        if execution.get('terminal_status') in {'ALLOWED','SUCCESS','RESPONDED'}:
            self.check(label+': allowed needs real call',bool(calls))
        for c in calls:
            response=c.get('response',{})
            self.check(label+': live response',bool(response.get('done')) and 'error' not in response and c.get('fallback_used') is False)
            self.same(label+': raw output',c.get('model_output'),response.get('response'))
            self.same(label+': request binding',c.get('request_hash'),digest({'prompt':c.get('prompt'),'system_prompt':c.get('system_prompt')}))
            self.same(label+': input count',c.get('input_tokens'),response.get('prompt_eval_count'))
            self.same(label+': output count',c.get('output_tokens'),response.get('eval_count'))
            self.check(label+': model error flags',not any(response.get(k) for k in ('fallback','synthetic','error','timeout','oom')))
        if calls:self.same(label+': final raw output',execution.get('model_output'),'\n'.join(c['model_output'] for c in calls))
        else:self.check(label+': no fabricated generation',not execution.get('model_output'))
        self.check(label+': finite latency',isinstance(execution.get('latency_ms'),(float,int)) and math.isfinite(execution['latency_ms']) and execution['latency_ms']>=0)
        for call in execution.get('executed_tool_calls',[]):
            mutation=call.get('result',{}).get('mutation')
            if mutation:self.check(label+': mutation audit',mutation in execution.get('mock_state_mutations',[]))
        self.check(label+': no backend-error outcome',execution.get('terminal_status') not in {'MODEL_ERROR','BACKEND_ERROR','TIMEOUT','OOM'})

    def group(self,name,ids,oracles,runtime):
        records=self.raw(name);got=[r.get('case_id') for r in records]
        self.check(name+': complete unique case set',len(got)==len(ids) and len(set(got))==len(got) and set(got)==set(ids))
        for i,r in enumerate(records):
            self.check_record(r,oracles,f'{name}/{i}')
            if r.get('case_id') in runtime:self.same(f'{name}/{i}: frozen stimulus',r.get('runtime_case'),runtime[r['case_id']])
        return records

    def run(self):
        manifest=self.read('dataset_manifest_v3_2.json');protocol=self.read('campaign_protocol.json')
        rt=self.read('datasets/runtime.json');ot=self.read('datasets/oracle.json')
        if not isinstance(rt,list) or not isinstance(ot,list):return self.result()
        runtime={x['case_id']:x for x in rt};oracles={x['case_id']:OracleCase.from_dict(x) for x in ot};ids=set(runtime)
        self.check('full 850 heldout IDs',len(rt)==len(ot)==len(runtime)==len(oracles)==850 and ids==set(oracles))
        self.same('manifest actual classes',manifest.get('class_counts'),dict(Counter(x['attack_class'] for x in ot)))
        self.same('full primary protocol',protocol.get('primary_n'),850)
        self.check('human claims disabled',protocol.get('human_validation') is False and manifest.get('human_validation') is False)
        self.check('public AgentDojo claim disabled',protocol.get('public_agentdojo') is False and manifest.get('public_agentdojo') is False)
        for p in self.path.rglob('*'):
            if p.is_file() and any(x in p.name for x in ('reviewer_r1','reviewer_r2','adjudicated_labels','human_judge_validation')):
                self.failures.append('Unexpected human source/claim in Option B package: '+p.name)
        for x in rt:
            secret=x.get('session_metadata',{}).get('session_secret')
            if secret:self.check('Protected secret absent from attacker input: '+x['case_id'],secret not in x['user_input'] and secret not in json.dumps(x.get('retrieved_context',[])))
        primary={k:self.group(f'primary_{i}',ids,oracles,runtime) for i,k in enumerate(SYSTEMS)}
        observed={k:summarize(v) for k,v in primary.items()};self.observed=observed
        self.same('primary raw-summary consistency',self.read('baseline_comparison.json'),observed)
        phi=self.group('multimodel_phi',ids,oracles,runtime)
        self.same('multimodel summary',self.read('multi_model_results.json'),{'qwen2.5:7b':observed['HETE'],'phi3.5:latest':summarize(phi)})
        absums={}
        for name in ABLATIONS:absums[name]=summarize(self.group('ablation_'+name,ids,oracles,runtime))
        self.same('ablation summary',self.read('ablation_results.json'),absums)
        subset=protocol.get('stochastic_ids',[]);self.check('preregistered stochastic subset',len(subset)>=30 and len(set(subset))==len(subset) and set(subset)<=ids)
        stoch={}
        for seed in (11,22,33,44,55):
            rr=self.group(f'stochastic_{seed}',subset,oracles,runtime);stoch[str(seed)]=summarize(rr)
            self.check(f'stochastic {seed}: actual sampling',all(c.get('options',{}).get('temperature')==.7 and c['options'].get('top_p')==.9 and c['options'].get('seed')==seed for r in rr for c in r['calls']))
        self.same('stochastic summary',self.read('stochastic_results.json'),stoch)
        adaptive=self.raw('adaptive');counts=Counter(r.get('campaign') for r in adaptive)
        self.same('adaptive six campaigns x 30 seeds',dict(counts),{c:30 for c in CAMPAIGNS})
        self.check('adaptive unique seed/campaign pairs',len({(r.get('campaign'),r.get('seed_case_id')) for r in adaptive})==len(adaptive))
        for i,seed in enumerate(adaptive):
            queries=seed.get('queries',[]);n=len(queries)
            self.check(f'adaptive {i}: B20 or early E2E',n==20 or (0<n<20 and queries[-1].get('verdict',{}).get('e2e_attack_succeeded') is True))
            self.same(f'adaptive {i}: consecutive queries',[q.get('query_number') for q in queries],list(range(1,n+1)))
            hashes=[]
            for q in queries:
                self.check_record(q,oracles,f'adaptive {i}/{q.get("query_number")}')
                rc=q.get('runtime_case',{})
                h=digest({'user_input':rc.get('user_input'),'retrieved_context':rc.get('retrieved_context')});hashes.append(h)
                self.same(f'adaptive {i}: actual mutation hash',q.get('input_hash'),h)
                self.same(f'adaptive {i}: knowledge',q.get('attacker_knowledge'),'A2')
            self.check(f'adaptive {i}: no repeated inputs',len(set(hashes))==n)
            for key,verdict in [('first_mcr_query','model_compromised'),('first_e2e_query','e2e_attack_succeeded')]:
                self.same(f'adaptive {i}: {key}',seed.get(key),next((q['query_number'] for q in queries if q['verdict'][verdict]),None))
        stats=self.read('statistical_tests.json');tests=[]
        hete={r['case_id']:r for r in primary['HETE'] if r['is_attack']}
        if len(hete)==sum(o.is_attack for o in oracles.values()):
            for name,recs in primary.items():
                if name=='HETE':continue
                other={r['case_id']:r for r in recs if r['is_attack']}
                if set(other)!=set(hete):continue
                ordered=sorted(hete)
                tests.append({'system':name,**exact_mcnemar_test([int(other[i]['verdict']['e2e_attack_succeeded']) for i in ordered],[int(hete[i]['verdict']['e2e_attack_succeeded']) for i in ordered])})
            adj,sig=holm_bonferroni_correction([r['p_value'] for r in tests],family_alpha=.05)
            for r,p,f in zip(tests,adj,sig):r.update(holm_p=p,holm_p_text=f'{p:.12e}',significant=f)
            self.same('exact McNemar and Holm',stats,{'method':'exact two-sided binomial McNemar','alpha':.05,'pairs':tests})
        artifact=self.read('ARTIFACT_MANIFEST.json');entries=artifact.get('artifacts',[])
        listed={e.get('path') for e in entries}
        required={str(p.relative_to(self.path)) for p in self.path.rglob('*') if p.is_file() and p.name not in {'ARTIFACT_MANIFEST.json','publication_evidence_validation.json'}}
        self.same('complete artifact coverage',listed,required)
        for e in entries:
            path=self.path/e['path']
            self.check('artifact '+e['path'],path.is_file() and path.stat().st_size==e['size'] and hashlib.sha256(path.read_bytes()).hexdigest()==e['sha256'])
        self.same('executed source frozen',artifact.get('source_hashes'),protocol.get('source_hashes'))
        self.same('current source matches frozen source',source_hashes(),protocol.get('source_hashes'))
        # Do not infer methodological closure merely from favorable or complete metric tables.
        closure=self.read('methodology_acceptance.json')
        required_methods=['resource_runtime_validation','tool_authorization_validation','output_guard_validation','dataset_independence_audit','manuscript_evidence_audit','latex_clean_build']
        for requirement in required_methods:
            entry=closure.get(requirement,{})
            self.check('methodology '+requirement,entry.get('passed') is True and entry.get('evidence_path') in listed)
        return self.result()
    def result(self):
        return {'publication_evidence_valid':not self.failures,'human_validation':False,'public_agentdojo':False,
                'scientific_integrity_failures':self.failures,'observed_results':self.observed}

def main():
    p=argparse.ArgumentParser();p.add_argument('--results-dir',type=Path,default=REPO/'results/llm_security_v3_2_closure');p.add_argument('--strict',action='store_true');p.add_argument('--output-json',type=Path)
    args=p.parse_args();audit=Auditor(args.results_dir)
    try:report=audit.run()
    except Exception as exc:
        audit.failures.append('Audit could not complete: '+repr(exc));report=audit.result()
    write(args.output_json or args.results_dir/'publication_evidence_validation.json',report)
    print(json.dumps({'publication_evidence_valid':report['publication_evidence_valid'],'failure_count':len(report['scientific_integrity_failures'])}))
    raise SystemExit(0 if report['publication_evidence_valid'] else 1)
if __name__=='__main__':main()
