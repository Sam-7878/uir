"""Fresh synthetic development-only format probe; never rescore old Phi runs."""
import json
import time
from pathlib import Path

import requests

from .common import TASK, load, rows, sha, write


def main():
    session=requests.Session();session.trust_env=False;endpoint='http://127.0.0.1:11434'
    info=next(m for m in session.get(endpoint+'/api/tags',timeout=15).json()['models'] if m['name']=='phi3.5:latest')
    corpus=[{'id':f'dev-{i:02}','language':'ko' if i%2 else 'en',
             'expected':{'entity':f'DEV_ENTITY_{i}','metric':'synthetic_measure','value':100+i,
                         'fiscal_year':2025,'citations':[f'dev-source-{i}']}} for i in range(12)]
    schema={'type':'object','properties':{'entity':{'type':'string'},'metric':{'type':'string'},
        'value':{'type':'integer'},'fiscal_year':{'type':'integer'},'citations':{'type':'array','items':{'type':'string'}}},
        'required':['entity','metric','value','fiscal_year','citations'],'additionalProperties':False}
    protocol={'id':'Phi-dev-format-V4-001','development_only':True,'dataset':corpus,'model':info,
              'script_sha256':sha(Path(__file__)),'variants':['generate_json','chat_schema'],
              'options':{'temperature':0,'seed':20261021,'num_predict':192,'num_ctx':4096},
              'limits':'synthetic transcription probe; no new held-out security or general utility claim'}
    path=TASK/'manifests/phi_dev_protocol.json'
    if path.exists() and load(path)!=protocol:raise RuntimeError('Protocol differs')
    write(path,protocol);output=TASK/'data/phi_dev_runs.jsonl'
    done={(r['case_id'],r['variant']) for r in rows(output)} if output.exists() else set()
    with output.open('a',encoding='utf-8') as stream:
        for variant in protocol['variants']:
            for case in corpus:
                if (case['id'],variant) in done:continue
                prompt=('다음 합성 자료를 그대로 JSON으로 출력하세요. 설명을 추가하지 마세요. ' if case['language']=='ko'
                        else 'Return this synthetic record as one JSON object without commentary. ')+json.dumps(case['expected'])
                system='You transform a trusted synthetic record into the exact required JSON contract. Do not invent values.'
                request={'model':'phi3.5:latest','stream':False,'keep_alive':'5m','options':protocol['options']}
                if variant=='generate_json':request.update(system=system,prompt=prompt,format='json');api='/api/generate'
                else:request.update(messages=[{'role':'system','content':system},{'role':'user','content':prompt}],format=schema);api='/api/chat'
                start=time.perf_counter();record={'case_id':case['id'],'language':case['language'],'variant':variant,'request':request,
                                                  'model_digest':info['digest'],'exact_success':False,'backend_failure':False}
                try:
                    response=session.post(endpoint+api,json=request,timeout=120);response.raise_for_status();raw=response.json()
                    record['response']=raw;text=raw.get('response',raw.get('message',{}).get('content',''))
                    try:parsed=json.loads(text);record['valid_json']=True
                    except ValueError:parsed=None;record['valid_json']=False
                    record['exact_success']=raw.get('done') is True and parsed==case['expected']
                except Exception as exc:record.update(backend_failure=True,error=repr(exc))
                record['latency_s']=time.perf_counter()-start
                stream.write(json.dumps(record,ensure_ascii=False)+'\n');stream.flush()
                print(variant,case['id'],record['exact_success'],record.get('error',''),flush=True)
    session.post(endpoint+'/api/generate',json={'model':'phi3.5:latest','keep_alive':0},timeout=30)
    records=list(rows(output));summary={v:{'n':sum(r['variant']==v for r in records),
        'exact':sum(r['variant']==v and r['exact_success'] for r in records),
        'backend_errors':sum(r['variant']==v and r['backend_failure'] for r in records)} for v in protocol['variants']}
    write(TASK/'data/phi_dev_summary.json',summary)
    write(TASK/'reports/PHI_DEV_FORMAT_PROBE.md','# Phi development-only format probe\n\n'+json.dumps(summary,indent=2)+'\n\n'
          'Twelve fresh synthetic transcription records (six KO/six EN) compare the installed native generate template + JSON mode '
          'with native chat messages + constrained JSON schema. This is a small development compatibility diagnostic, not a retuned V3.2 held-out result. '
          'Historical Phi 0/250 benign and 6/600 E2E remain unchanged. No prompt was selected on the original held-out outputs. '
          'Even an improved format probe would require a new independent security/utility evaluation before a broad performance claim.\n')


if __name__=='__main__':main()
