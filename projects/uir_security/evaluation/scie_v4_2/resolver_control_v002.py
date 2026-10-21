"""Post-hoc transport correction; original C3 failures remain immutable.

Only the no-LLM development diagnostic uses recursive BaseModel serialization.
The confirmatory C0/C1/C2 study is unchanged. These 12 seen IDs are explicitly
development IDs for this corrected adapter, not a new held-out comparison.
"""
from .common import *
from . import external
from .resolver_control import Resolver

import time
from unittest.mock import patch


def structured(value):
    if hasattr(value,'model_dump'):return structured(value.model_dump(mode='json'))
    if isinstance(value,dict):return {str(k):structured(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [structured(v) for v in value]
    if value is None or type(value) in (str,int,float,bool):return value
    return str(value)


class StructuredResolver(Resolver):
    def generate(self,system,prompt):
        request=json.loads(prompt)
        for entry in request['observations']:
            result=entry.get('result',{})
            if isinstance(result,dict) and isinstance(result.get('data'),str):
                try:result['data']=json.loads(result['data'])
                except ValueError:pass
        return super().generate(system,canonical(request))


def main():
    plan=load(TASK/'manifests/AGENTDOJO_V4_2_PROTOCOL_002.json')
    freeze(TASK/'manifests/C3_TRANSPORT_AMENDMENT_002.json',{'id':'HETE-C3-V4.2-002-posthoc',
        'source_sha256':sha(Path(__file__)),'original_protocol':sha(TASK/'manifests/NO_LLM_V4_2_PROTOCOL.json'),
        'original_runs_preserved':True,'original_failure':'42/72 trials raised str.get AttributeError from repr-serialized typed tool results',
        'change':'recursive BaseModel JSON transport; parse JSON text before deterministic rules; no rule/policy/oracle changes',
        'post_hoc':True,'development_ids':[t['domain']+'/'+t['task_id'] for t in plan['tasks']],
        'confirmatory_comparison':False,'planned_trials':72})
    out=TASK/'experiments/policy_incremental/no_llm_transport_diagnostic_v002.jsonl'
    done={r['run_id'] for r in rows(out)} if out.exists() else set()
    with patch.object(external,'jsonable',structured),out.open('a') as stream:
        for task_plan in plan['tasks']:
            domain=task_plan['domain'];id=task_plan['task_id'];suite=external.get_suite('v1.2.2',domain)
            task=suite.get_user_task_by_id(id);injection=suite.get_injection_task_by_id('injection_task_0')
            for method in external.METHODS:
                identity=f'C3-v002-dev/{domain}/{id}/{method}'
                if identity in done:continue
                changes={} if method=='benign' else task_plan['payloads'][method]
                agent=external.LocalAgent('no_model','C3_no_llm',domain,id,StructuredResolver(),identity,changes);start=time.perf_counter()
                record={'run_id':identity,'config':'C3_v002_posthoc','model':None,'domain':domain,'task_id':id,'method':method,
                        'attack':method!='benign','post_hoc':True,'write_task':task_plan['write_required_by_user_scope'],'backend_failure':False}
                try:
                    utility,security=suite.run_task_with_pipeline(agent,task,injection if changes else None,changes)
                    record.update(utility=bool(utility),attack_success=bool(security) if changes else None)
                except Exception as exc:record.update(backend_failure=True,error=repr(exc),utility=False,attack_success=None)
                record.update(trace=agent.trace,pre_state=agent.before,post_state=agent.after,final_output=agent.final,
                    injected_content_observed=agent.exposed,latency_s=time.perf_counter()-start,model_tokens=0)
                stream.write(canonical(record)+'\n');stream.flush()
                print(identity,record['utility'],record.get('error',''),flush=True)


if __name__=='__main__':main()
