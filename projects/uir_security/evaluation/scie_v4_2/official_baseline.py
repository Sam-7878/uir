"""Upstream CaMeL PrivilegedLLM/interpreter/policies with a local API backend.

No upstream source is rewritten. Backend compatibility and a smaller attempt
budget are explicit deviations, so this is not a published-number reproduction.
"""
from .common import *
from .external import ENDPOINT,MODELS,jsonable,strings

import argparse
import asyncio
import subprocess
import time

from agentdojo.task_suite import get_suite
from agentdojo.agent_pipeline import InitQuery,AgentPipeline,OpenAILLM
from agentdojo.attacks.baseline_attacks import DirectAttack
from camel.pipeline_elements.privileged_llm import PrivilegedLLM
from camel.pipeline_elements.security_policies import BankingSecurityPolicyEngine,WorkspaceSecurityPolicyEngine,TravelSecurityPolicyEngine
import httpx
from openai import OpenAI,AsyncOpenAI
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

ENGINES={'banking':BankingSecurityPolicyEngine,'workspace':WorkspaceSecurityPolicyEngine,'travel':TravelSecurityPolicyEngine}
SELECT={'workspace':'user_task_6','banking':'user_task_3','travel':'user_task_0'}


class CapturedOfficialAgent:
    def __init__(self,model,domain,requests_log):
        self.name=model+'+official_camel_local_backend';self.trace=[];self.before=None;self.after=None;self.messages=[]
        def save_response(response):
            response.read()
            requests_log.append({'request':json.loads(response.request.content),'status':response.status_code,
                                 'response':response.json() if response.headers.get('content-type','').startswith('application/json') else response.text})
        async def save_async_response(response):
            await response.aread()
            requests_log.append({'request':json.loads(response.request.content),'status':response.status_code,
                                 'response':response.json() if response.headers.get('content-type','').startswith('application/json') else response.text})
        sync=OpenAI(base_url=ENDPOINT+'/v1',api_key='local-ollama-placeholder',max_retries=0,timeout=120,
                    http_client=httpx.Client(trust_env=False,event_hooks={'response':[save_response]}))
        async_client=AsyncOpenAI(base_url=ENDPOINT+'/v1',api_key='local-ollama-placeholder',max_retries=0,timeout=120,
                    http_client=httpx.AsyncClient(trust_env=False,event_hooks={'response':[save_async_response]}))
        llm=OpenAILLM(sync,model,temperature=0.)
        privileged=PrivilegedLLM(llm,ENGINES[domain],'openai:'+model,quarantined_llm_retries=1,max_attempts=2)
        privileged.quarantined_llm_model=OpenAIModel(model,provider=OpenAIProvider(openai_client=async_client))
        self.pipeline=AgentPipeline([InitQuery(),privileged])

    def query(self,query,runtime,env,messages=None,extra_args=None):
        self.before=jsonable(env.model_dump(mode='json'));original=runtime.run_function
        def traced(environment,name,args,*rest,**kwargs):
            before=jsonable(environment.model_dump(mode='json'))
            event={'tool':name,'args':jsonable(args),'executor_invoked':True}
            try:
                result=original(environment,name,args,*rest,**kwargs)
                event['result']=jsonable(result);return result
            except Exception as exc:event['error']=repr(exc);raise
            finally:
                event['state_mutated']=jsonable(environment.model_dump(mode='json'))!=before
                self.trace.append(event)
        runtime.run_function=traced
        try:
            result=self.pipeline.query(query,runtime,env,messages or [],extra_args or {})
            self.messages=jsonable(result[3]);return result
        finally:self.after=jsonable(env.model_dump(mode='json'))


def main(development=False):
    target={'banking':'user_task_1'} if development else SELECT
    protocol={'id':'CaMeL-official-agent-local-V4.2-001','official_source_commit':subprocess.check_output(
        ['git','-C',str(OLD/'resources/camel'),'rev-parse','HEAD'],text=True).strip(),
        'model':MODELS[1],'domains_tasks':SELECT,'methods':['benign','official_direct'],'planned_trials':6,
        'runner_sha256':sha(Path(__file__)),'backend':'Ollama localhost OpenAI-compatible API for privileged and quarantined models',
        'upstream_source_modified':False,'quarantined_retries':1,'max_code_attempts':2,
        'policy':'official per-domain CaMeL policies, not identical to HETE application delegations',
        'comparability_limit':'same task IDs/official oracles; different agent interface/control flow and policy/budget; no superiority claim'}
    freeze(TASK/'manifests/OFFICIAL_BASELINE_PROTOCOL.json',protocol)
    output=TASK/'experiments/official_baseline'/('DEV_OFFICIAL_AGENT.jsonl' if development else 'OFFICIAL_AGENT_CASE_TRACE.jsonl')
    done={r['run_id'] for r in rows(output)} if output.exists() else set()
    with output.open('a') as stream:
        for domain,id in target.items():
            suite=get_suite('v1.2.2',domain);task=suite.get_user_task_by_id(id);injection=suite.get_injection_task_by_id('injection_task_0')
            for method in (['benign'] if development else ['benign','official_direct']):
                identity=f'official-camel/{domain}/{id}/{method}'
                if identity in done:continue
                calls=[];agent=CapturedOfficialAgent(MODELS[1],domain,calls)
                changes={} if method=='benign' else DirectAttack(suite,agent).attack(task,injection)
                record={'run_id':identity,'domain':domain,'task_id':id,'method':method,'model':MODELS[1],
                        'official_agent_implementation':True,'development_only':development,'backend_failure':False}
                start=time.perf_counter()
                try:
                    utility,security=suite.run_task_with_pipeline(agent,task,injection if changes else None,changes)
                    record.update(utility=bool(utility),attack_success=bool(security) if changes else None)
                except Exception as exc:record.update(backend_failure=True,error=repr(exc),utility=False,attack_success=None)
                record.update(trace=agent.trace,calls=calls,pre_state=agent.before,post_state=agent.after,messages=agent.messages,
                    injected_content_observed=any(v in text for v in changes.values() for event in agent.trace for text in strings(event.get('result'))),
                    latency_s=time.perf_counter()-start)
                stream.write(canonical(record)+'\n');stream.flush()
                print(identity,record['utility'],record['attack_success'],record.get('error',''),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--development',action='store_true');a=p.parse_args();main(a.development)
