"""Application-owned typed effect boundary. No benchmark gold/oracle imports.

Python object isolation is a TCB assumption, not protection against hostile host
code. Only JSON proposals/observations cross the adversarial input boundary.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from jsonschema import Draft202012Validator

from .common import canonical, digest


def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate key')
        result[key]=value
    return result


def decode(raw):
    def invalid(value):raise ValueError('nonfinite JSON')
    value=json.loads(raw,object_pairs_hook=unique_object,parse_constant=invalid)
    canonical(value)  # reject overflowing nonfinite floats too
    if not isinstance(value,dict):raise ValueError('expected object')
    return value


@dataclass(frozen=True,slots=True)
class PolicyRevision:
    value:int
    def __post_init__(self):
        if type(self.value) is not int or self.value<0:raise ValueError('revision must be a nonnegative exact integer')


@dataclass(frozen=True,slots=True)
class Capability:
    tool:str
    resource:str='*'
    approval_required:bool=False


@dataclass(frozen=True,slots=True)
class Budget:
    max_steps:int=10
    max_model_tokens:int=12000
    max_egress_bytes:int=20000


@dataclass(frozen=True,slots=True)
class TrustedSession:
    id:str
    principal:str
    revision:PolicyRevision
    capabilities:tuple[Capability,...]
    owned_resources:frozenset[str]=frozenset()
    approved_resources:frozenset[str]=frozenset()
    budget:Budget=Budget()


@dataclass(frozen=True,slots=True)
class EvidenceRef:
    id:str
    content_sha256:str
    signer:str
    claim_scope:str
    key_epoch:int
    signature:str


@dataclass(frozen=True,slots=True)
class UntrustedObservation:
    id:str
    origin_tool:str
    content_sha256:str
    serialized_data:str


@dataclass(frozen=True,slots=True)
class ProposedAction:
    id:str
    tool:str
    arguments_json:str
    nonce:str
    evidence_ids:tuple[str,...]=()


@dataclass(frozen=True,slots=True)
class ApprovedAction:
    id:str
    proposal_id:str
    session_id:str
    principal:str
    tool:str
    arguments_json:str
    revision:PolicyRevision
    nonce:str
    evidence_ids:tuple[str,...]
    capability:Capability
    proof:str


@dataclass(frozen=True,slots=True)
class CanonicalOutput:
    id:str
    contract:str
    content_json:str


@dataclass(slots=True)
class AuditEvent:
    run_id:str
    event_id:str
    principal:str
    policy_revision:int
    proposed:bool=False
    admitted:bool=False
    executor_invoked:bool=False
    state_mutated:bool=False
    egress_released:bool=False
    policy_verdict:str='DENY'
    reason:str=''
    proposal_id:str|None=None
    approved_action_id:str|None=None
    capability_proof_digest:str|None=None
    evidence_ids:list[str]=field(default_factory=list)
    stages:list[str]=field(default_factory=list)
    tool:str|None=None
    arguments_digest:str|None=None
    result:Any=None
    output_id:str|None=None
    def record(self):return asdict(self)


class AuthorityStore:
    """Application-managed authority, signing material, evidence and live revision."""
    def __init__(self,session:TrustedSession):
        self.session=session;self.revision=session.revision.value
        self.proof_key=secrets.token_bytes(32)
        self.signer_keys:dict[tuple[str,int],bytes]={};self.revoked:set[tuple[str,int]]=set()
        self.evidence:dict[str,tuple[EvidenceRef,str]]={}
        self.owners={r:session.principal for r in session.owned_resources}
        self.nonces=set()

    def update_revision(self,value):
        if type(value) is not int or value<=self.revision:raise ValueError('policy rollback/non-advance')
        self.revision=value

    def add_signer(self,name,epoch):
        if (name,epoch) in self.signer_keys:raise ValueError('key epoch already exists')
        self.signer_keys[name,epoch]=secrets.token_bytes(32)

    def endorse(self,id,content,signer,scope,epoch=1):
        key=self.signer_keys[signer,epoch]
        payload={'id':id,'sha256':hashlib.sha256(content.encode()).hexdigest(),'scope':scope,'epoch':epoch,'signer':signer}
        ref=EvidenceRef(id,payload['sha256'],signer,scope,epoch,hmac.new(key,canonical(payload).encode(),hashlib.sha256).hexdigest())
        self.evidence[id]=(ref,content);return ref

    def verify_evidence(self,id,scope):
        if id not in self.evidence:return False
        ref,content=self.evidence[id];slot=(ref.signer,ref.key_epoch)
        if slot not in self.signer_keys or slot in self.revoked or ref.claim_scope!=scope:return False
        payload={'id':ref.id,'sha256':ref.content_sha256,'scope':ref.claim_scope,'epoch':ref.key_epoch,'signer':ref.signer}
        expected=hmac.new(self.signer_keys[slot],canonical(payload).encode(),hashlib.sha256).hexdigest()
        return hashlib.sha256(content.encode()).hexdigest()==ref.content_sha256 and hmac.compare_digest(expected,ref.signature)


@dataclass(frozen=True,slots=True)
class Gates:
    capability:bool=True
    arguments:bool=True
    evidence:bool=True
    revalidation:bool=True
    proof:bool=True
    replay:bool=True
    output:bool=True
    budget:bool=True


class TypedInterpreter:
    def __init__(self,store:AuthorityStore,schemas:dict,executor:Callable,
                 argument_policy:Callable=lambda t,a,s:True,resource_for:Callable=lambda t,a:'*',
                 evidence_scope:dict|None=None,gates:Gates=Gates()):
        self.store=store;self.schemas=schemas;self.executor=executor;self.argument_policy=argument_policy
        self.resource_for=resource_for;self.evidence_scope=evidence_scope or {};self.gates=gates
        self.events=[];self.observations=[];self.steps=0;self.model_tokens=0

    def event(self):
        s=self.store.session
        return AuditEvent(s.id,f'{s.id}:event:{len(self.events)}',s.principal,self.store.revision)

    def finish(self,event,reason,allowed=False):
        event.reason=reason;event.policy_verdict='ALLOW' if allowed else 'DENY'
        record=event.record();self.events.append(record);return record

    def observe(self,tool,result):
        obs=UntrustedObservation(f'{self.store.session.id}:obs:{len(self.observations)}',tool,digest(result),canonical(result))
        self.observations.append(obs);return obs

    def policy(self,tool,args):
        resource=self.resource_for(tool,args);s=self.store.session
        caps=[c for c in s.capabilities if c.tool==tool and c.resource in ('*',resource)]
        if self.gates.capability and not caps:return None,'capability'
        cap=caps[0] if caps else Capability(tool,resource)
        if self.gates.capability and cap.approval_required and resource not in s.approved_resources:return None,'approval'
        if self.gates.arguments and not self.argument_policy(tool,args,self.store):return None,'arguments'
        return cap,''

    def compile(self,raw,nonce,evidence_ids=()):
        e=self.event();e.stages.append('parse')
        try:
            obj=decode(raw)
            if set(obj)!={'tool','args'} or not isinstance(obj['tool'],str) or not isinstance(obj['args'],dict):raise ValueError('proposal shape')
            if not re.fullmatch('[a-z][a-z0-9_]*',obj['tool']):raise ValueError('identifier')
            if not isinstance(nonce,str) or not nonce:raise ValueError('nonce')
        except (ValueError,TypeError,OverflowError):return None,self.finish(e,'parse_or_type')
        e.proposed=True;e.tool=obj['tool'];e.arguments_digest=digest(obj['args']);e.stages.append('typecheck')
        if obj['tool'] not in self.schemas:return None,self.finish(e,'registry')
        if not Draft202012Validator(self.schemas[obj['tool']]).is_valid(obj['args']):return None,self.finish(e,'tool_schema')
        p=ProposedAction(f'{self.store.session.id}:proposal:{len(self.events)}',obj['tool'],canonical(obj['args']),nonce,tuple(evidence_ids))
        e.proposal_id=p.id;e.evidence_ids=list(evidence_ids);e.stages.append('policy')
        cap,reason=self.policy(p.tool,obj['args'])
        if cap is None:return None,self.finish(e,reason)
        e.stages.append('arguments')
        scope=self.evidence_scope.get(p.tool)
        if self.gates.evidence and scope and (not evidence_ids or not all(self.store.verify_evidence(i,scope) for i in evidence_ids)):
            return None,self.finish(e,'evidence')
        e.stages.append('evidence')
        s=self.store.session
        if self.gates.budget and (self.steps>=s.budget.max_steps or self.model_tokens>s.budget.max_model_tokens):return None,self.finish(e,'budget')
        fields={'id':p.id+':approved','proposal_id':p.id,'session_id':s.id,'principal':s.principal,'tool':p.tool,
                'arguments_json':p.arguments_json,'revision':asdict(s.revision),'nonce':p.nonce,
                'evidence_ids':p.evidence_ids,'capability':asdict(cap)}
        proof=hmac.new(self.store.proof_key,canonical(fields).encode(),hashlib.sha256).hexdigest()
        approved=ApprovedAction(fields['id'],p.id,s.id,s.principal,p.tool,p.arguments_json,s.revision,p.nonce,p.evidence_ids,cap,proof)
        e.admitted=True;e.approved_action_id=approved.id;e.capability_proof_digest=hashlib.sha256(proof.encode()).hexdigest()
        return approved,e

    def dispatch(self,approved,event=None):
        e=event if isinstance(event,AuditEvent) else self.event();e.stages.append('revalidate')
        if not isinstance(approved,ApprovedAction):return self.finish(e,'approved_type')
        fields=asdict(approved);proof=fields.pop('proof')
        expected=hmac.new(self.store.proof_key,canonical(fields).encode(),hashlib.sha256).hexdigest()
        if self.gates.proof and not hmac.compare_digest(proof,expected):return self.finish(e,'proof')
        s=self.store.session;args=json.loads(approved.arguments_json)
        if self.gates.revalidation:
            if approved.principal!=s.principal or approved.session_id!=s.id or approved.revision.value!=self.store.revision:
                return self.finish(e,'revision_or_principal')
            # Dispatch independently checks current ownership/approval/capability,
            # even if admission was accidentally removed.
            live_caps=[c for c in s.capabilities if c.tool==approved.tool and c.resource in ('*',self.resource_for(approved.tool,args))]
            if not live_caps or (live_caps[0].approval_required and self.resource_for(approved.tool,args) not in s.approved_resources):
                return self.finish(e,'current_permission')
            if not self.argument_policy(approved.tool,args,self.store):return self.finish(e,'current_arguments')
            scope=self.evidence_scope.get(approved.tool)
            if scope and (not approved.evidence_ids or not all(self.store.verify_evidence(i,scope) for i in approved.evidence_ids)):
                return self.finish(e,'current_evidence')
        if self.gates.replay and approved.nonce in self.store.nonces:return self.finish(e,'replay')
        if self.gates.budget and (self.steps>=s.budget.max_steps or self.model_tokens>s.budget.max_model_tokens):return self.finish(e,'budget')
        self.store.nonces.add(approved.nonce);self.steps+=1;e.executor_invoked=True;e.stages.append('effect_commit')
        try:
            result,mutated=self.executor(approved.tool,args)
        except Exception as exc:
            return self.finish(e,'executor_error:'+type(exc).__name__)
        e.result=result;e.state_mutated=bool(mutated);self.observe(approved.tool,result)
        return self.finish(e,'committed',True)

    def submit(self,tool,args,nonce,evidence_ids=(),before_dispatch=None):
        approved,event=self.compile(canonical({'tool':tool,'args':args}),nonce,evidence_ids)
        if approved is None:return event
        if before_dispatch:before_dispatch(self.store)
        return self.dispatch(approved,event)

    def release(self,value,contract='task_text',verified_record=None):
        e=self.event();e.stages=['canonical_egress'];s=self.store.session
        if self.gates.budget and self.model_tokens>s.budget.max_model_tokens:return self.finish(e,'post_call_budget')
        if contract=='numeric_v4_1':
            allowed={'entity','metric','value','fiscal_year','citations'}
            if self.gates.output and (not isinstance(value,dict) or set(value)!=allowed or value!=verified_record):
                return self.finish(e,'canonical_contract')
            payload=verified_record if self.gates.output else value
        else:
            # External AgentDojo utility needs arbitrary task text. Serialization
            # here is an output type boundary, not semantic/DLP verification.
            if not isinstance(value,str):return self.finish(e,'text_type')
            payload={'kind':'authenticated_user_task_result','text':value}
        text=canonical(payload)
        if self.gates.budget and len(text.encode())>s.budget.max_egress_bytes:return self.finish(e,'output_bytes')
        output=CanonicalOutput(f'{s.id}:output:{len(self.events)}',contract,text)
        e.output_id=output.id;e.egress_released=True;e.result=asdict(output)
        return self.finish(e,'released',True)


class MinimalGuard(TypedInterpreter):
    """Same application policy/schema/revalidation without compiled typed actions.

    Shares the policy definition for a matched comparison, but does not call the
    typed compiler, construct ApprovedAction, or validate its proof token.
    """
    def submit(self,tool,args,nonce,evidence_ids=(),before_dispatch=None):
        e=self.event();e.proposed=True;e.tool=tool;e.arguments_digest=digest(args)
        e.evidence_ids=list(evidence_ids);e.stages=['schema','policy']
        if tool not in self.schemas or not Draft202012Validator(self.schemas[tool]).is_valid(args):return self.finish(e,'tool_schema')
        cap,reason=self.policy(tool,args)
        if cap is None:return self.finish(e,reason)
        scope=self.evidence_scope.get(tool)
        if scope and not all(self.store.verify_evidence(i,scope) for i in evidence_ids):return self.finish(e,'evidence')
        if scope and not evidence_ids:return self.finish(e,'evidence')
        e.admitted=True
        if before_dispatch:before_dispatch(self.store)
        if self.store.revision!=self.store.session.revision.value:return self.finish(e,'revision_or_principal')
        cap,reason=self.policy(tool,args)
        if cap is None:return self.finish(e,'current_'+reason)
        if scope and not all(self.store.verify_evidence(i,scope) for i in evidence_ids):return self.finish(e,'current_evidence')
        if nonce in self.store.nonces:return self.finish(e,'replay')
        if self.steps>=self.store.session.budget.max_steps or self.model_tokens>self.store.session.budget.max_model_tokens:return self.finish(e,'budget')
        self.store.nonces.add(nonce);self.steps+=1;e.executor_invoked=True;e.stages.append('effect_commit')
        try:result,mutated=self.executor(tool,args)
        except Exception as exc:return self.finish(e,'executor_error:'+type(exc).__name__)
        e.result=result;e.state_mutated=bool(mutated);self.observe(tool,result)
        return self.finish(e,'committed',True)
