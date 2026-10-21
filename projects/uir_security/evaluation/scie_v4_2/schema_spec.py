"""Closed JSON wire schema and executable finite authority-state validation."""
from .common import *
from .typed_engine import *
from .mechanism import instance

import itertools
from dataclasses import replace


def spec():
    def obj(properties):return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
    string={'type':'string'};identifier={'type':'string','minLength':1}
    integer={'type':'integer','minimum':0};boolean={'type':'boolean'}
    strings={'type':'array','items':string};nullable={'type':['string','null']}
    ref=lambda name:{'$ref':'#/$defs/'+name}
    definitions={
      'PolicyRevision':obj({'value':integer}),
      'Capability':obj({'tool':{'type':'string','pattern':'^[a-z][a-z0-9_]*$'},'resource':string,'approval_required':boolean}),
      'Budget':obj({'max_steps':integer,'max_model_tokens':integer,'max_egress_bytes':integer}),
      'TrustedSession':obj({'id':identifier,'principal':identifier,'revision':ref('PolicyRevision'),
          'capabilities':{'type':'array','items':ref('Capability')},'owned_resources':strings,'approved_resources':strings,'budget':ref('Budget')}),
      'EvidenceRef':obj({'id':identifier,'content_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},
          'signer':identifier,'claim_scope':identifier,'key_epoch':integer,'signature':{'type':'string','pattern':'^[0-9a-f]{64}$'}}),
      'UntrustedObservation':obj({'id':identifier,'origin_tool':identifier,'content_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},'serialized_data':string}),
      'ProposedAction':obj({'id':identifier,'tool':identifier,'arguments_json':string,'nonce':identifier,'evidence_ids':strings}),
      'ApprovedAction':obj({'id':identifier,'proposal_id':identifier,'session_id':identifier,'principal':identifier,'tool':identifier,
          'arguments_json':string,'revision':ref('PolicyRevision'),'nonce':identifier,'evidence_ids':strings,
          'capability':ref('Capability'),'proof':{'type':'string','pattern':'^[0-9a-f]{64}$'}}),
      'CanonicalOutput':obj({'id':identifier,'contract':{'enum':['task_text','numeric_v4_1']},'content_json':string}),
    }
    definitions['AuditEvent']=obj({'run_id':identifier,'event_id':identifier,'principal':identifier,'policy_revision':integer,
        **{name:boolean for name in ('proposed','admitted','executor_invoked','state_mutated','egress_released')},
        'policy_verdict':{'enum':['ALLOW','DENY']},'reason':string,'proposal_id':nullable,'approved_action_id':nullable,
        'capability_proof_digest':nullable,'evidence_ids':strings,'stages':strings,'tool':nullable,'arguments_digest':nullable,
        'result':{},'output_id':nullable})
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:hete:proposal:4.2',
        'title':'HETE V4.2 untrusted proposal wire and internal record definitions',
        **obj({'tool':{'type':'string','pattern':'^[a-z][a-z0-9_]*$'},'args':{'type':'object'}}),'$defs':definitions,
        '$comment':'JSON validity never grants authority. TrustedSession, EvidenceRef and ApprovedAction are application-owned runtime constructors.'}
    old=TASK/'source/UIR_TYPED_SCHEMA_V4_2.json'
    if old.exists() and 'runtime_types' in load(old):write(TASK/'source/UIR_TYPED_TYPE_INVENTORY_V4_2.json',load(old))
    write(old,schema);return schema


def main():
    schema=spec();Draft202012Validator.check_schema(schema)
    states=list(itertools.product(['alice','bob','reader'],['alice','bob'],[False,True],[False,True],[False,True],[False,True]))
    freeze(TASK/'manifests/BOUNDED_MODEL_PROTOCOL.json',{'id':'HETE-bounded-authority-V4.2-001','states':len(states),
        'axes':['principal','owner','approved','signer_active','revision_current','nonce_fresh'],'systems':['minimal','typed'],
        'source_sha256':sha(Path(__file__)),'engine_sha256':sha(Path(__file__).with_name('typed_engine.py')),
        'specification':'permit iff writer role AND own resource AND approved AND signer active AND revision current AND nonce fresh',
        'scope':'bounded executable model/code comparison; not an unbounded formal proof'})
    records=[]
    for number,(principal,owner,approved,active,current,fresh) in enumerate(states):
        expect=principal!='reader' and principal==owner and approved and active and current and fresh
        for name in ('minimal','typed'):
            e,db=instance(name,principal,approved)
            e.store.owners['report-1']=owner
            if principal=='reader':e.store.session=replace(e.store.session,capabilities=(Capability('read_document'),))
            if not active:e.store.revoked.add(('fixture_curator',1))
            if not current:e.store.update_revision(5)
            if not fresh:e.store.nonces.add('n')
            event=e.submit('write_report',{'id':'report-1','body':'authorized'},'n',['doc-1'])
            actual=db.execute('SELECT count(*) FROM reports').fetchone()[0]>0;db.close()
            Draft202012Validator({'$ref':'#/$defs/AuditEvent','$defs':schema['$defs']}).validate(event)
            records.append({'case_id':f'bounded-{number:03}','system':name,'principal':principal,'owner':owner,
                'approved':approved,'signer_active':active,'revision_current':current,'nonce_fresh':fresh,
                'specified_permit':expect,'actual_mutation':actual,'matched':actual==expect,'trace':event})
    write(TASK/'experiments/typed_semantics/BOUNDED_MODEL_TRACE.jsonl',''.join(canonical(r)+'\n' for r in records))
    failures=[r for r in records if not r['matched']]
    write(TASK/'reports/MODEL_CHECK_REPORT.md',f'# Bounded authority-state comparison\n\n{len(states)} authority states x two execution systems = {len(records)} actual SQLite trials; {len(failures)} specification mismatches. '
        'All resulting typed decision records validate against the explicit closed AuditEvent schema. The application controls roles, ownership, approval, key state, revision and nonce state. '
        'This finite model includes neither arbitrary natural language nor compromised host code/distributed transactions. It is not an unbounded proof.\n')
    write(TASK/'manifests/BOUNDED_MODEL_RESULT.json',{'states':len(states),'trials':len(records),'failures':failures,'passed':not failures})
    print('bounded states',len(states),'trials',len(records),'failures',len(failures))
    return int(bool(failures))


if __name__=='__main__':raise SystemExit(main())
