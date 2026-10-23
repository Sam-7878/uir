"""Matched carriers over the SAME checks, executor and anchored audit contract.

An application reference mediator, not a static compiler proof or hostile-host
isolation. Fresh in-process keys, SQLite ATTACH and an application-held audit
anchor are trusted. The public narrative renderer is deliberately constrained.
"""
from .common import canonical,digest
import hashlib
import hmac
import json
import secrets
import sqlite3
from dataclasses import asdict,dataclass

SERVICES=('finance','records')
STEPS=({'service':'finance','resource':'invoice','op':'debit','amount':7},
       {'service':'records','resource':'report','op':'append','evidence':'public-revenue'})
FIELDS=('run_id','principal','revisions','steps','evidence','nonce')
AUDIT_FIELDS=('run_id','principal','request_sha','plan_sha','evidence_ids','revisions','decision','reason','before','after','effect_count','previous')
def sign(key,value):return hmac.new(key,canonical(value).encode(),hashlib.sha256).hexdigest()
def decode(text):
    def pairs(values):
        obj={}
        for key,value in values:
            if key in obj:raise ValueError('duplicate JSON field')
            obj[key]=value
        return obj
    def invalid(value):raise ValueError('nonfinite JSON')
    obj=json.loads(text,object_pairs_hook=pairs,parse_constant=invalid);canonical(obj)
    if not isinstance(obj,dict):raise ValueError('object required')
    return obj

@dataclass(frozen=True,slots=True)
class ApprovedPlan:
    run_id:str
    principal:str
    revisions:dict
    steps:tuple
    evidence:tuple
    nonce:str
    proof:str
    def wire(self):
        value=asdict(self);value['steps']=list(value['steps']);value['evidence']=list(value['evidence']);return value

@dataclass(frozen=True,slots=True)
class TrustedEffect:
    run_id:str
    committed:bool
    effects:int
    state_digest:str

@dataclass(frozen=True,slots=True)
class UntrustedNarrative:
    language:str
    mode:str
    refs:tuple
    free_text:str=''

class World:
    def __init__(self,run_id,state=None):
        self.run_id=run_id;self.principal='alice';self.key=secrets.token_bytes(32);self.audit_key=secrets.token_bytes(32)
        self.state={name:True for name in ('role_ok','owner_finance','owner_records','approval_finance','approval_records','evidence_active','revision_current','nonce_fresh')}
        if state:self.state.update(state)
        self.revisions={'finance':3,'records':5};self.nonces=set();self.audit=[]
        self.anchor='0'*64;self.request_sha=digest(STEPS)
        self.public={'public-revenue':{'metric':'revenue','value':100,'source':'public-doc-A','classification':'public'},
                     'public-profit':{'metric':'profit','value':18,'source':'public-doc-B','classification':'public'}}
        self.public_binding=digest(self.public)
        self.secret='PRIVATE_V43_'+hashlib.sha256(run_id.encode()).hexdigest()[:18]
        self.db=sqlite3.connect(':memory:')
        self.db.execute("ATTACH DATABASE ':memory:' AS finance")
        self.db.execute("ATTACH DATABASE ':memory:' AS records")
        self.db.execute('CREATE TABLE finance.effects(run TEXT, amount INTEGER)')
        self.db.execute('CREATE TABLE records.effects(run TEXT, evidence TEXT)')
        self.db.execute('CREATE TABLE outbox(channel TEXT, body TEXT)')
    def counts(self):return [self.db.execute(f'SELECT count(*) FROM {name}.effects').fetchone()[0] for name in SERVICES]
    def live_permit(self):return all(self.state.values())
    def emit(self,channel,text):
        with self.db:self.db.execute('INSERT INTO outbox VALUES (?,?)',(channel,text))
    def close(self):self.db.close()

class Mediator:
    def __init__(self,world,typed):self.world=world;self.typed=typed
    def pack(self,value):
        return ApprovedPlan(**{**value,'steps':tuple(value['steps']),'evidence':tuple(value['evidence'])}) if self.typed else value
    def unpack(self,plan):
        if self.typed:
            if not isinstance(plan,ApprovedPlan):raise ValueError('approved carrier required')
            return plan.wire()
        if type(plan) is not dict:raise ValueError('flat approved object required')
        return plan
    def compile(self,proposal):
        w=self.world
        obj=decode(proposal)
        if set(obj)!={'steps'} or obj['steps']!=list(STEPS):return None,'proposal_contract'
        if not w.live_permit():return None,'admission_policy'
        fields={'run_id':w.run_id,'principal':w.principal,'revisions':dict(w.revisions),
                'steps':list(STEPS),'evidence':[{'id':'public-revenue','content_sha256':digest(w.public['public-revenue']),
                    'scope':'public-financial-record','issuer':'application-curator'}],'nonce':'once'}
        return self.pack({**fields,'proof':sign(w.key,fields)}),'approved'
    def from_wire(self,text):
        obj=decode(text)
        if set(obj)!=set(FIELDS)|{'proof'}:raise ValueError('wire schema')
        if not all(type(obj[k]) is str for k in ('run_id','principal','nonce','proof')):raise ValueError('scalar types')
        if not isinstance(obj['steps'],list) or not isinstance(obj['evidence'],list) or not isinstance(obj['revisions'],dict):raise ValueError('collection types')
        return self.pack(obj)
    def record(self,decision,reason,before,plan=None):
        w=self.world;after=w.counts()
        event={'run_id':w.run_id,'principal':w.principal,'request_sha':w.request_sha,'plan_sha':digest(plan) if plan else None,
            'evidence_ids':['public-revenue'],'revisions':dict(w.revisions),'decision':decision,'reason':reason,
            'before':before,'after':after,'effect_count':sum(after)-sum(before),'previous':w.anchor}
        event['tag']=sign(w.audit_key,event);w.audit.append(event);w.anchor=event['tag'];return event
    def dispatch(self,approved,fail_second=False):
        w=self.world;before=w.counts()
        try:obj=self.unpack(approved)
        except (ValueError,TypeError):return self.record('DENY','carrier',before)
        fields={k:obj.get(k) for k in FIELDS}
        if set(obj)!=set(FIELDS)|{'proof'} or not isinstance(obj.get('proof'),str) or not hmac.compare_digest(sign(w.key,fields),obj['proof']):
            return self.record('DENY','proof',before,obj)
        expected_evidence=[{'id':'public-revenue','content_sha256':digest(w.public['public-revenue']),
                            'scope':'public-financial-record','issuer':'application-curator'}]
        if obj['run_id']!=w.run_id or obj['principal']!=w.principal or obj['steps']!=list(STEPS) or obj['evidence']!=expected_evidence:
            return self.record('DENY','binding',before,obj)
        if obj['revisions']!=w.revisions or obj['nonce'] in w.nonces or not w.live_permit():return self.record('DENY','current_authority',before,obj)
        try:
            with w.db:
                w.db.execute('INSERT INTO finance.effects VALUES (?,?)',(w.run_id,7))
                if fail_second:raise RuntimeError('controlled second-service executor failure')
                w.db.execute('INSERT INTO records.effects VALUES (?,?)',(w.run_id,'public-revenue'))
            w.nonces.add(obj['nonce'])
        except RuntimeError:return self.record('DENY','rollback',before,obj)
        return self.record('ALLOW','committed',before,obj)
    def effect(self):
        w=self.world;counts=w.counts()
        return TrustedEffect(w.run_id,counts==[1,1],sum(counts),digest(counts))

def verify_audit(events,key,anchor,count):
    if len(events)!=count:return False
    previous='0'*64
    for event in events:
        if not all(k in event for k in AUDIT_FIELDS) or event['previous']!=previous:return False
        fields={k:v for k,v in event.items() if k!='tag'}
        if not hmac.compare_digest(sign(key,fields),event.get('tag','')):return False
        previous=event['tag']
    return previous==anchor

def release_narrative(world,raw,policy='bounded_public'):
    """Real egress via SQLite outbox, same policy in both carrier configurations.

    General generated prose is withheld; supported explanations are application
    rendered public facts. This restores a bounded feature, not open-prose DLP.
    """
    try:obj=decode(raw)
    except (ValueError,TypeError):return {'released':False,'reason':'parse','text':''}
    if policy=='numeric_strict':return {'released':False,'reason':'numeric_contract_has_no_narrative','text':''}
    if policy=='unsafe_open_control':
        text=str(obj.get('free_text',''))
        if any('private' in str(ref) for ref in obj.get('refs',[])):text+=world.secret
        world.emit('narrative',text);return {'released':True,'reason':'unsafe_control','text':text}
    if set(obj)!={'language','mode','refs','free_text'} or obj['free_text']!='':return {'released':False,'reason':'raw_text_or_extra_authority','text':''}
    if obj['language'] not in ('en','ko') or obj['mode'] not in ('explain','compare','refuse') or not isinstance(obj['refs'],list):
        return {'released':False,'reason':'narrative_contract','text':''}
    if not obj['refs'] or any(not isinstance(ref,str) or ref not in world.public for ref in obj['refs']):return {'released':False,'reason':'public_provenance','text':''}
    if digest(world.public)!=world.public_binding:return {'released':False,'reason':'public_binding_changed','text':''}
    if not world.state['evidence_active']:return {'released':False,'reason':'evidence_revoked','text':''}
    facts=[world.public[ref] for ref in obj['refs']]
    if any(f['classification']!='public' for f in facts):return {'released':False,'reason':'classification','text':''}
    n=UntrustedNarrative(obj['language'],obj['mode'],tuple(obj['refs']))
    prefix={'en':{'explain':'Verified public facts: ','compare':'Comparison of public records: ','refuse':'No additional authority is granted. Public evidence: '},
            'ko':{'explain':'검증된 공개 사실: ','compare':'공개 기록 비교: ','refuse':'추가 권한은 부여하지 않습니다. 공개 근거: '}}[n.language][n.mode]
    text=prefix+'; '.join(f"{f['metric']}={f['value']} [{f['source']}]" for f in facts)
    world.emit('narrative',text)
    return {'released':True,'reason':'public_fact_renderer','text':text}
