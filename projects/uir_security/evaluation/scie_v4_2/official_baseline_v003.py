"""Official CaMeL with an explicit developer->system local API role adapter.

The upstream AgentDojo OpenAI wrapper maps system to developer. The local Mistral
template did not consume that role in development (recorded prompt counters and
responses). Preserve content while adapting the unsupported provider role; no
CaMeL policy/interpreter code changes and no oracle information are introduced.
"""
from .common import *
from .external import ENDPOINT,MODELS,jsonable,get_suite
from .official_baseline import CapturedOfficialAgent,SELECT,ENGINES

import argparse
import time

import httpx
from openai import OpenAI,AsyncOpenAI
from agentdojo.agent_pipeline import InitQuery,AgentPipeline,OpenAILLM
from agentdojo.attacks.baseline_attacks import DirectAttack
from camel.pipeline_elements.privileged_llm import PrivilegedLLM
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


def translated(request,raw):
    original=json.loads(raw);payload=json.loads(raw);changes=[]
    for message in payload.get('messages',[]):
        if message.get('role')=='developer':message['role']='system';changes.append('developer_to_system_same_content')
    payload.setdefault('max_tokens',1024);payload.setdefault('seed',20261021)
    headers=dict(request.headers);headers.pop('content-length',None)
    req=httpx.Request(request.method,request.url,headers=headers,content=canonical(payload).encode(),extensions=request.extensions)
    return req,original,payload,changes


class Transport(httpx.BaseTransport):
    def __init__(self,log):self.log=log;self.inner=httpx.HTTPTransport()
    def handle_request(self,request):
        req,original,payload,changes=translated(request,request.read());start=time.perf_counter()
        response=self.inner.handle_request(req);response.read()
        self.log.append({'original_request':original,'transmitted_request':payload,'adaptations':changes,'status':response.status_code,
            'response':response.json() if response.headers.get('content-type','').startswith('application/json') else response.text,
            'latency_s':time.perf_counter()-start})
        return response


class AsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self,log):self.log=log;self.inner=httpx.AsyncHTTPTransport()
    async def handle_async_request(self,request):
        req,original,payload,changes=translated(request,await request.aread());start=time.perf_counter()
        response=await self.inner.handle_async_request(req);await response.aread()
        self.log.append({'original_request':original,'transmitted_request':payload,'adaptations':changes,'status':response.status_code,
            'response':response.json() if response.headers.get('content-type','').startswith('application/json') else response.text,
            'latency_s':time.perf_counter()-start})
        return response


class CompatibleOfficialAgent(CapturedOfficialAgent):
    def __init__(self,model,domain,requests_log):
        self.name=model+'+official_camel_backend_role_adapter';self.trace=[];self.before=None;self.after=None;self.messages=[]
        client=OpenAI(base_url=ENDPOINT+'/v1',api_key='local-ollama-placeholder',max_retries=0,timeout=120,
                      http_client=httpx.Client(transport=Transport(requests_log),trust_env=False))
        async_client=AsyncOpenAI(base_url=ENDPOINT+'/v1',api_key='local-ollama-placeholder',max_retries=0,timeout=120,
                      http_client=httpx.AsyncClient(transport=AsyncTransport(requests_log),trust_env=False))
        llm=OpenAILLM(client,model,temperature=0.)
        privileged=PrivilegedLLM(llm,ENGINES[domain],'openai:'+model,quarantined_llm_retries=1,max_attempts=2)
        privileged.quarantined_llm_model=OpenAIModel(model,provider=OpenAIProvider(openai_client=async_client))
        self.pipeline=AgentPipeline([InitQuery(),privileged])


def main(development=False):
    freeze(TASK/'manifests/OFFICIAL_BASELINE_PROTOCOL_003.json',{'id':'CaMeL-official-agent-local-V4.2-003',
        'source_sha256':sha(Path(__file__)),'inherited_trace_wrapper_sha256':sha(Path(__file__).with_name('official_baseline.py')),
        'upstream_source_modified':False,'domains_tasks':SELECT,'planned_trials':6,'model':MODELS[1],
        'backend_role_adapter':'developer->system, identical content; max_tokens1024, seed20261021',
        'context_tokens':16384,'max_code_attempts':2,'quarantined_retries':1,
        'development_ids':['banking/user_task_1'],'earlier_development_attempts_preserved':True,
        'fidelity':'official code/policies with local backend adapter; policy/agent interface differs from HETE; no superiority claim'})
    path=TASK/'experiments/official_baseline'/('DEV_OFFICIAL_AGENT_003.jsonl' if development else 'OFFICIAL_AGENT_CASE_TRACE_003.jsonl')
    done={r['run_id'] for r in rows(path)} if path.exists() else set()
    with path.open('a') as stream:
        for domain,id in ({'banking':'user_task_1'} if development else SELECT).items():
            suite=get_suite('v1.2.2',domain);task=suite.get_user_task_by_id(id);injection=suite.get_injection_task_by_id('injection_task_0')
            for method in (['benign'] if development else ['benign','official_direct']):
                identity=f'official-camel-v003/{domain}/{id}/{method}'
                if identity in done:continue
                calls=[];agent=CompatibleOfficialAgent(MODELS[1],domain,calls)
                changes={} if method=='benign' else DirectAttack(suite,agent).attack(task,injection)
                record={'run_id':identity,'domain':domain,'task_id':id,'method':method,'model':MODELS[1],
                    'official_agent_implementation':True,'development_only':development,'backend_failure':False}
                start=time.perf_counter()
                try:
                    utility,security=suite.run_task_with_pipeline(agent,task,injection if changes else None,changes)
                    record.update(utility=bool(utility),attack_success=bool(security) if changes else None)
                except Exception as exc:record.update(backend_failure=True,error=repr(exc),utility=False,attack_success=None)
                record.update(trace=agent.trace,calls=calls,pre_state=agent.before,post_state=agent.after,messages=agent.messages,
                              latency_s=time.perf_counter()-start)
                stream.write(canonical(record)+'\n');stream.flush();print(identity,record['utility'],record.get('error',''),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--development',action='store_true');args=p.parse_args();main(args.development)
