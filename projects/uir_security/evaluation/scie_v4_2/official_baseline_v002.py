"""CaMeL backend development revision; preserve the initial incompatible probe."""
from .common import *
from .official_baseline import CapturedOfficialAgent,SELECT,DirectAttack,get_suite

import argparse
import time


def main(development=False):
    metadata=load(TASK/'manifests/OFFICIAL_LOCAL_BACKEND_MODEL.json');model=metadata['model']['name']
    protocol={'id':'CaMeL-official-agent-local-V4.2-002','previous_development':'V4.2-001 DEV_OFFICIAL_AGENT.jsonl preserved',
        'source_sha256':sha(Path(__file__)),'upstream_source_modified':False,'domains_tasks':SELECT,'planned_trials':6,
        'backend_model':metadata['model'],'context_tokens':32768,'max_generated_tokens':1024,
        'privileged_attempts':2,'quarantined_retries':1,
        'change_reason':'32k context and bounded decoder for long official code-generation system prompt, adjusted on excluded banking/user_task_1 only',
        'fidelity':'official PrivilegedLLM + interpreter + domain policy engine; local OpenAI-compatible backend adapter; different context and policy than C1/C2, no superiority'}
    freeze(TASK/'manifests/OFFICIAL_BASELINE_PROTOCOL_002.json',protocol)
    out=TASK/'experiments/official_baseline'/('DEV_OFFICIAL_AGENT_002.jsonl' if development else 'OFFICIAL_AGENT_CASE_TRACE.jsonl')
    done={r['run_id'] for r in rows(out)} if out.exists() else set()
    with out.open('a') as stream:
        for domain,id in ({'banking':'user_task_1'} if development else SELECT).items():
            suite=get_suite('v1.2.2',domain);task=suite.get_user_task_by_id(id);injection=suite.get_injection_task_by_id('injection_task_0')
            for method in (['benign'] if development else ['benign','official_direct']):
                identity=f'official-camel-v002/{domain}/{id}/{method}'
                if identity in done:continue
                calls=[];agent=CapturedOfficialAgent(model,domain,calls)
                changes={} if method=='benign' else DirectAttack(suite,agent).attack(task,injection)
                result={'run_id':identity,'domain':domain,'task_id':id,'method':method,'model':model,'backend_failure':False,
                        'official_agent_implementation':True,'development_only':development}
                start=time.perf_counter()
                try:
                    utility,security=suite.run_task_with_pipeline(agent,task,injection if changes else None,changes)
                    result.update(utility=bool(utility),attack_success=bool(security) if changes else None)
                except Exception as exc:result.update(backend_failure=True,error=repr(exc),utility=False,attack_success=None)
                result.update(calls=calls,trace=agent.trace,pre_state=agent.before,post_state=agent.after,messages=agent.messages,
                              latency_s=time.perf_counter()-start)
                stream.write(canonical(result)+'\n');stream.flush();print(identity,result['utility'],result.get('error',''),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--development',action='store_true');a=p.parse_args();main(a.development)
