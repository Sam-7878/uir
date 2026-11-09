"""Local-only trust boundary. No experiment labels, gold, dataset or model I/O."""
from dataclasses import asdict, dataclass
import hmac
import json
import re
import secrets
import sqlite3

from .common import canon, digest

OPERATIONS={'pay':4,'append':3,'draft':4,'send':4,'book':4,'read':2}
ARMS=('C0_open','C1_flat','C2_typed')
ABLATIONS=('K1_no_provenance','K2_no_capability','K3_no_egress')
ASCII_ID=re.compile(r'[A-Za-z0-9@.\-_:]{1,120}\Z',re.ASCII)


class Invalid(ValueError):
    pass


def _unique(pairs):
    obj={}
    for k,v in pairs:
        if k in obj:
            raise Invalid('duplicate_key')
        obj[k]=v
    return obj


def parse(text):
    try:
        obj=json.loads(text,object_pairs_hook=_unique,parse_constant=lambda _: None)
        if type(obj) is not dict or set(obj)!={'actions','answer'}:
            raise Invalid('proposal_keys')
        if type(obj['actions']) is not list or len(obj['actions'])>3:
            raise Invalid('action_cardinality')
        for a in obj['actions']:
            if type(a) is not list or not a or type(a[0]) is not str or OPERATIONS.get(a[0])!=len(a):
                raise Invalid('action_shape')
            for i,v in enumerate(a[1:],1):
                if a[0]=='pay' and i==3:
                    if type(v) is not int or not 0<v<=10000:
                        raise Invalid('amount')
                elif type(v) is not str or not ASCII_ID.fullmatch(v):
                    raise Invalid('identifier')
        b=obj['answer']
        if (type(b) is not dict or not {'mode','refs','language'}<=set(b) or set(b)-{'mode','refs','language','text'}
           or b['mode'] not in ('single','compare','insufficient','none') or b['language'] not in ('en','ko')
           or type(b['refs']) is not list or len(b['refs'])>2
           or any(type(ref) is not str or not ASCII_ID.fullmatch(ref) for ref in b['refs'])
           or type(b.get('text','')) is not str or len(b.get('text',''))>2048):
            raise Invalid('answer_shape')
        return obj
    except (ValueError,TypeError,RecursionError) as e:
        raise Invalid(str(e)) from e


@dataclass(frozen=True)
class Approved:
    session: str
    principal: str
    revision: int
    nonce: str
    approval: str
    actions: tuple
    snapshot: str


class World:
    def __init__(self, runtime, arm):
        if arm not in (*ARMS,*ABLATIONS,'K4_no_live_recheck'):
            raise ValueError('Unknown arm')
        self.arm=arm
        self.id=runtime['id']
        self.principal=runtime['principal']
        self.approval=runtime['approval']
        self.rev=runtime['revision']
        self.records=json.loads(canon(runtime['records']))
        self.grants=json.loads(canon(runtime['grants']))
        self.sources={k:digest(v) for k,v in self.records.items()}
        self.used=set()
        self.key=secrets.token_bytes(32)
        self.audit=[]
        self.db=sqlite3.connect(':memory:')
        self.db.executescript("""
          CREATE TABLE effects (seq INTEGER PRIMARY KEY, op TEXT, resource TEXT, args TEXT, UNIQUE(op,resource));
          CREATE TABLE outbox (seq INTEGER PRIMARY KEY, channel TEXT, destination TEXT, text TEXT, facts TEXT);
        """)

    def close(self):
        self.db.close()

    def _tag(self,value):
        return hmac.digest(self.key,canon(value).encode(),'sha256').hex()

    def snapshot(self):
        return digest({'principal':self.principal,'approval':self.approval,'revision':self.rev,
                       'records':self.records,'grants':self.grants})

    def log(self,reason,**kwargs):
        ev={'reason':reason,'session':self.id,'principal':self.principal,'revision':self.rev,
            'previous':self.audit[-1]['tag'] if self.audit else None,'sequence':len(self.audit),**kwargs}
        self.audit.append({**ev,'tag':self._tag(ev)})

    def _public(self,ref):
        r=self.records.get(ref)
        return r if r and r['visibility']=='public' and self.sources.get(ref)==digest(r) else None

    def _admit(self,actions):
        if len({tuple(a) for a in actions})!=len(actions):
            return 'duplicate_action'
        if self.arm=='C0_open':
            return None
        for op,rid,*args in actions:
            if op=='read':
                if self.arm!='K1_no_provenance' and not self._public(rid):
                    return 'read_provenance'
                if rid not in self.records:
                    return 'missing_record'
                continue
            if op in ('append','draft','send') and self.arm!='K1_no_provenance' and not self._public(args[-1]):
                return 'effect_provenance'
            if self.arm!='K2_no_capability':
                matches=[g for g in self.grants if (g['op'],g['resource'],g['principal'],g['approval'])==
                         (op,rid,self.principal,self.approval) and (op=='append' or g['recipient']==args[0])]
                if not any((op!='pay' or args[-1]<=g['ceiling']) and
                           (op!='book' or args[-1]==g['slot']) for g in matches):
                    return 'capability'
        return None

    def compile(self,actions,nonce):
        failure=self._admit(actions)
        if failure:
            self.log(failure,stage='admission',proposal_sha256=digest(actions))
            return None
        a=Approved(self.id,self.principal,self.rev,nonce,self.approval,tuple(map(tuple,actions)),self.snapshot())
        fields=asdict(a)
        carrier=a if self.arm=='C2_typed' else fields
        return carrier,self._tag(fields)

    def dispatch(self,carrier,proof):
        fields=asdict(carrier) if isinstance(carrier,Approved) else carrier
        try:
            valid=hmac.compare_digest(self._tag(fields),proof)
        except (TypeError,ValueError):
            valid=False
        if not valid or fields['session']!=self.id or fields['nonce'] in self.used:
            self.log('proof_session_or_nonce',stage='dispatch')
            return None
        if self.arm!='K4_no_live_recheck' and (fields['snapshot']!=self.snapshot() or self._admit(fields['actions'])):
            self.log('live_recheck',stage='dispatch')
            return None
        observations=[]
        try:
            with self.db:
                for op,rid,*args in fields['actions']:
                    if op=='read':
                        r=self.records.get(rid)
                        if not r:
                            raise Invalid('missing_record')
                        observations.append({'ref':rid,'record':r})
                        continue
                    self.db.execute('INSERT INTO effects(op,resource,args) VALUES (?,?,?)',(op,rid,canon(args)))
                    if op in ('append','draft','send'):
                        r=self.records.get(args[-1])
                        if not r:
                            raise Invalid('missing_record')
                        if op=='send':
                            self.db.execute('INSERT INTO outbox(channel,destination,text,facts) VALUES (?,?,?,?)',
                                            ('mock_send',args[0],str(r['value']),canon([{'ref':args[-1],**r}])))
        except (sqlite3.Error,Invalid):
            self.log('transaction_rollback',stage='dispatch')
            return None
        self.used.add(fields['nonce'])
        if any(a[0]!='read' for a in fields['actions']):
            self.rev+=1
        self.log('committed' if fields['actions'] else 'no_actions',stage='dispatch',action_sha256=digest(fields['actions']),
                 approved_snapshot=fields['snapshot'],actual_effect_count=self.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0])
        return observations

    def render(self,answer):
        mode=answer['mode']
        lang=answer['language']
        refs=answer['refs']
        open_egress=self.arm in ('C0_open','K3_no_egress')
        if mode=='none' and not answer.get('text') and not refs:
            return
        expected={'single':1,'compare':2,'insufficient':0}.get(mode,-1)
        facts=[]
        if open_egress and answer.get('text'):
            text=answer['text']
        else:
            if (len(refs)!=expected or len(set(refs))!=len(refs) or answer.get('text')):
                self.log('answer_contract_denial',stage='egress')
                return
            for ref in refs:
                r=self.records.get(ref) if open_egress else self._public(ref)
                if not r:
                    self.log('answer_provenance_denial',stage='egress')
                    return
                facts.append({'ref':ref,**r})
            if mode=='compare' and not (
                all(k in r for r in facts for k in ('entity','metric','unit','period')) and
                all(facts[0][k]==facts[1][k] for k in ('entity','metric','unit')) and facts[0]['period']<facts[1]['period']
            ):
                self.log('answer_comparability_denial',stage='egress')
                return
            parts=[]
            for r in facts:
                if 'period' in r:
                    parts.append(f"{r['entity']} {r['period']} — {r['metric']}: {r['value']} {r['unit']} [{r['ref']}]")
                else:
                    parts.append(f"{r['value']} [{r['ref']}]")
            if mode=='compare':
                delta=facts[1]['value']-facts[0]['value']
                parts.append((f'변화: {delta:+d} ' if lang=='ko' else f'Change: {delta:+d} ')+facts[0]['unit'])
            if mode=='insufficient':
                parts.append('공개 근거가 부족합니다.' if lang=='ko' else 'Public evidence is insufficient.')
            text='; '.join(parts)
        with self.db:
            self.db.execute('INSERT INTO outbox(channel,destination,text,facts) VALUES (?,?,?,?)',
                            ('narrative:'+mode+':'+lang,'requesting_user',text,canon(facts)))
        self.log('rendered',stage='egress',output_sha256=digest(text))

    def apply(self,proposal,nonce,*,render=True):
        proof=self.compile(proposal['actions'],nonce)
        read=self.dispatch(*proof) if proof else None
        if render:
            self.render(proposal['answer'])
        return read

    def result(self):
        return {'effects':[[op,rid,*json.loads(args)] for op,rid,args in self.db.execute(
                    'SELECT op,resource,args FROM effects ORDER BY seq')],
                'outbox':[{'channel':c,'to':d,'text':t,'facts':json.loads(f)} for c,d,t,f in self.db.execute(
                    'SELECT channel,destination,text,facts FROM outbox ORDER BY seq')],
                'audit':self.audit,'terminal_tag':self.audit[-1]['tag'] if self.audit else None}
