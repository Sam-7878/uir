"""Run/resume exact frozen units. This module never opens an oracle file."""
import argparse
import fcntl
import json
import time

from .adaptive import final_note
from .backend import Client, Probe
from .common import SOURCE, TASK, append, canon, digest, lines, load, now, sha, write
from .dataset import SYSTEM, runtime_prompt
from .engine import ABLATIONS, ARMS, Invalid, World, parse

P=TASK/'manifests/V4_4_PREREGISTRATION.json'
CASES=TASK/'raw_runs/final_cases.jsonl'
CALLS=TASK/'raw_runs/final_physical.jsonl'
INTENTS=TASK/'raw_runs/final_request_intents.jsonl'
STOPS=TASK/'raw_runs/final_stop_events.jsonl'
SYSTEMIC={'MODEL_ERROR','BACKEND_ERROR','TIMEOUT','CUDA_OOM','INTERRUPTED_NO_RECEIPT'}


def verify_runtime_lock(p):
    for relative,checksum in p['source_sha256'].items():
        if sha(SOURCE/relative)!=checksum:
            raise ValueError('Frozen source changed: '+relative)
    split=TASK/'manifests/V4_4_DATASET_SPLITS.json'
    if sha(split)!=p['splits_sha256'] or sha(TASK/'manifests/V4_4_MODEL_PROTOCOL.json')!=p['models_sha256']:
        raise ValueError('Frozen manifest changed')
    r=load(split)['files']['final_runtime']
    path=TASK/r['path']
    if sha(path)!=r['sha256']:
        raise ValueError('Frozen runtime dataset changed')
    return load(path)


class Recorder:
    def __init__(self,client,model,options,limits):
        self.client,self.model,self.options=client,model,options
        self.limits=limits
        self.records={r['id']:r for r in lines(CALLS)} if CALLS.exists() else {}
        self.intents={r['id']:r for r in lines(INTENTS)} if INTENTS.exists() else {}
        self.count=sum(r['model']==model['name'] for r in self.intents.values())
        self.wall=sum(r['wall_s'] for r in self.records.values() if r['model']==model['name'])

    def get(self,unit,turn,prompt):
        call_id=digest({'model':self.model['digest'],'unit':unit,'turn':turn,'prompt':prompt})
        if call_id in self.records:
            return self.records[call_id]
        if call_id not in self.intents:
            if self.count>=self.limits['max_calls'] or self.wall>=self.limits['wall_budget_s']:
                return None
            intent={'id':call_id,'unit':unit,'turn':turn,'model':self.model['name'],
                    'prompt_sha256':digest({'system':SYSTEM,'prompt':prompt}),'started_utc':now()}
            append(INTENTS,intent)
            self.intents[call_id]=intent
            self.count+=1
            rec=self.client.generate(self.model,SYSTEM,prompt,self.options)
        else:
            rec={'status':'INTERRUPTED_NO_RECEIPT','model':self.model['name'],'model_digest':self.model['digest'],
                 'physical_request_attempted':None,'wall_s':0,
                 'raw_error':'Durable intent exists without completion receipt; no retry'}
        result={**rec,'id':call_id,'unit':unit,'turn':turn}
        append(CALLS,result)
        self.records[call_id]=result
        self.wall+=rec['wall_s']
        return result


def _consume(rec):
    if rec is None:
        return 'BUDGET_NOT_INVOKED',None
    if rec['status']!='COMPLETED':
        return rec['status'],None
    try:
        return 'COMPLETED',parse(rec['response']['response'])
    except Invalid:
        return 'INVALID_OUTPUT',None


def model_observations(read):
    # Protected tool records stay in the mock store. A model may ask to egress
    # their reference, but the raw secret is never inserted into any LLM request.
    return [{**r} if r['record']['visibility']=='public' else
            {'ref':r['ref'],'visibility':'restricted','value_retained_in_tool':True}
            for r in read]


def run_unit(recorder,runtime,index,injection):
    unit=runtime['id']+f'/q{index}'
    initial_prompt=runtime_prompt(runtime,injection)
    for val in runtime['records'].values():
        if val['visibility']=='restricted' and val['value'] in initial_prompt:
            raise ValueError('Protected literal in initial request')
    first=recorder.get(unit,0,initial_prompt)
    first_status,proposal=_consume(first)
    arms={}
    order=(*ARMS,*ABLATIONS) if runtime.get('attack_surface') else ARMS
    for arm in order:
        started=time.perf_counter()
        infer_wall=0
        world=World(runtime,arm)
        try:
            status=first_status
            calls=[first['id']] if first else []
            used=[]
            if proposal:
                used.append(proposal)
                read=world.apply(proposal,unit+'/0')
                if read and proposal['answer']['mode']=='none':
                    next_context=canon(model_observations(read))
                    if any(r['value'] in next_context for r in runtime['records'].values() if r['visibility']=='restricted'):
                        raise ValueError('Protected literal in follow-up request')
                    begin=time.perf_counter()
                    nxt=recorder.get(unit,1,runtime_prompt(runtime,injection,next_context))
                    infer_wall=time.perf_counter()-begin
                    if nxt:
                        calls.append(nxt['id'])
                    status,follow=_consume(nxt)
                    if follow:
                        used.append(follow)
                        world.apply(follow,unit+'/1')
            actual=world.result()
        finally:
            world.close()
        arms[arm]={'status':status,'call_ids':calls,'proposals':used,'actual':actual,
                   'local_pipeline_s':max(0,time.perf_counter()-started-infer_wall)}
    return {'unit':unit,'case_id':runtime['id'],'query':index,'arms':arms,'injection':injection,
            'model':recorder.model['name'],'model_digest':recorder.model['digest'],
            'completed_utc':now(),'first_status':first_status}


def run(client,models,protocol,runtime):
    prior={(r['model'],r['unit']):r for r in lines(CASES)} if CASES.exists() else {}
    for model in models:
        name=model['name']
        if STOPS.exists() and any(r['model']==name for r in lines(STOPS)):
            print(name,'frozen stop already recorded',flush=True)
            continue
        rec=Recorder(client,model,protocol['options'],protocol['limits'][name])
        consecutive=0
        with Probe(5) as probe:
            for item in runtime:
                surface=item.get('attack_surface')
                previous=None
                for idx in range(surface['queries'] if surface else 1):
                    unit=item['id']+f'/q{idx}'
                    saved=prior.get((name,unit))
                    if saved:
                        previous=saved['arms']['C0_open']['actual']
                        consecutive=consecutive+1 if saved['first_status'] in SYSTEMIC else 0
                        continue
                    if rec.count>=rec.limits['max_calls'] or rec.wall>=rec.limits['wall_budget_s'] or consecutive>=4:
                        break
                    record=run_unit(rec,item,idx,final_note(surface,idx,previous) if surface else '')
                    append(CASES,record)
                    previous=record['arms']['C0_open']['actual']
                    consecutive=consecutive+1 if record['first_status'] in SYSTEMIC else 0
                    if rec.count%10==0 or consecutive:
                        print(name,rec.count,'physical intents',unit,record['first_status'],flush=True)
                else:
                    continue
                break
            loaded=client.request('/api/ps')
        write(TASK/'audits'/('final_gpu_'+name.split(':')[0]+'.json'),{'gpu_samples':probe.samples,'loaded':loaded})
        finished=sum(r['model']==name for r in lines(CASES)) if CASES.exists() else 0
        append(STOPS,{'model':name,'status':'PLANNED_COMPLETE' if finished==240 else 'CAP_OR_SYSTEMIC_STOP',
                      'units_recorded':finished,'planned_units':240,'physical_intents':rec.count,'inference_wall_s':rec.wall,
                      'consecutive_systemic_errors':consecutive,'ended_utc':now()})
        client.request('/api/generate',{'model':name,'keep_alive':0})
        print(name,finished,'/240 units',flush=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-registered-live',action='store_true',required=True)
    ap.parse_args()
    p=load(P)
    runtime=verify_runtime_lock(p)
    protocol=load(TASK/'manifests/V4_4_MODEL_PROTOCOL.json')
    client=Client(protocol['endpoint'])
    meta=client.metadata()
    tagged={r['name']:r['digest'] for r in meta['models']}
    if meta['version']!=protocol['backend_version'] or any(tagged.get(m['name'])!=m['digest'] for m in protocol['models']):
        raise SystemExit('Registered model or backend identity changed')
    with (TASK/'raw_runs/.final_runner.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(client,protocol['models'],protocol,runtime)


if __name__=='__main__':
    main()
