"""Fail-closed checks of measured evidence, independent of desired outcomes."""
from collections import Counter
from datetime import datetime
import json

from .adaptive import final_note
from .aggregate import derive
from .common import FREEZE, ROOT, TASK, digest, lines, load, sha, write
from .dataset import SYSTEM
from .engine import ARMS, ABLATIONS
from .run_frozen_campaign import run_unit, verify_runtime_lock

OUT=TASK/'results/PUBLICATION_EVIDENCE_VALIDATION.json'


def native_summary():
    path=TASK/'raw_runs/native_cases.jsonl'
    if not path.is_file():
        return {'status':'NOT_RUN','fidelity':'UNVERIFIED','planned':18,'recorded':0,'physical_receipts':0,'groups':[]}
    rows=list(lines(path))
    calls=list(lines(TASK/'raw_runs/native_physical.jsonl'))
    controls=load(TASK/'audits/NATIVE_ORACLE_CONTROLS.json')
    plan=load(TASK/'manifests/V4_4_AGENTDOJO_NATIVE_PROTOCOL.json')
    groups=[]
    for arm in plan['arms']:
        for attack,n in [(False,2),(True,4)]:
            group=[r for r in rows if r['arm']==arm and bool(r['injection_task'])==attack]
            groups.append({'arm':arm,'population':'attack' if attack else 'benign','planned':n,'n':len(group),
                           'model_called':sum(bool(r['calls']) for r in group),
                           'completed':sum(r['status']=='COMPLETED' for r in group),
                           'native_utility':sum(r['native_utility'] is True for r in group),
                           'native_attack_success':sum(r['native_attack_success'] is True for r in group),
                           'unknown':sum(r['status']!='COMPLETED' for r in group),
                           'actual_exposure':sum(r['injected_text_in_actual_prompt'] for r in group),
                           'state_changes':sum(any(t['state_changed'] for t in r['trace']) for r in group)})
    valid=(len(rows)==18 and len({(r['unit'],r['arm']) for r in rows})==18 and len(controls)==4
           and all(list(c.values())[-1] is True for c in controls)
           and 0<len(calls)<=plan['request_cap'] and len({c['id'] for c in calls})==len(calls)
           and all(set(r['calls'])<={c['id'] for c in calls} for r in rows))
    return {'status':'COMPLETE' if valid else 'INCOMPLETE','fidelity':'NATIVE_ENGINE_CUSTOM_FRONTEND_SCOPED' if valid else 'UNVERIFIED',
            'planned':18,'recorded':len(rows),'physical_receipts':len(calls),'controls':controls,
            'protocol_sha256':sha(TASK/'manifests/V4_4_AGENTDOJO_NATIVE_PROTOCOL.json'),'groups':groups,
            'failures':dict(Counter(r['status'] for r in rows)),'source_version':plan['official']['wheel_distribution_version'],
            'task_ids':plan['task_ids'],'limitations':'two read-only workspace tasks; no external service, official CaMeL, baseline rank, population generalization, or matched narrative egress'}


def check_replay(raw,calls,runtime,models):
    class Offline:
        def __init__(self,row):
            self.model=models[row['model']]
        def get(self,unit,turn,prompt):
            key=digest({'model':self.model['digest'],'unit':unit,'turn':turn,'prompt':prompt})
            r=calls.get(key)
            if not r:
                return None
            if 'request' in r and (r['request']['prompt']!=prompt or r['request']['system']!=SYSTEM):
                raise ValueError('Saved model request does not match reconstructed prompt')
            return r
    def projection(arms):
        norm={}
        for arm,row in arms.items():
            x={k:v for k,v in row.items() if k not in ('local_pipeline_s','actual')}
            result=row['actual']
            x['actual']={'effects':result['effects'],'outbox':result['outbox'],
                         'audit':[ {k:v for k,v in a.items() if k not in ('tag','previous')} for a in result['audit']]}
            norm[arm]=x
        return norm
    last={}
    issues=[]
    for row in raw:
        r=runtime[row['case_id']]
        key=(row['model'],row['case_id'])
        i=row['query']
        s=r.get('attack_surface')
        expected=final_note(s,i,last.get(key)) if s else ''
        if expected!=row['injection']:
            issues.append([key,i,'adaptive note mismatch'])
        rebuilt=run_unit(Offline(row),r,i,expected)
        if projection(rebuilt['arms'])!=projection(row['arms']):
            issues.append([key,i,'offline state/egress/admission mismatch'])
        for arm in row['arms'].values():
            event=arm['actual']['audit']
            if any(a['sequence']!=k or a['previous']!=(event[k-1]['tag'] if k else None) for k,a in enumerate(event)) or (
                arm['actual']['terminal_tag']!=(event[-1]['tag'] if event else None)):
                issues.append([key,i,'audit linkage'])
        last[key]=row['arms']['C0_open']['actual']
    return issues


def validate(*,local_only=False):
    hold={'science_valid':False,'evidence_valid':False,'release_authorized':False,'publication_rights_approved':False,
          'preprint_posted':False,'journal_submitted':False,'submission_allowed':False,'status':'IN_PROGRESS_OR_INPUT_FAILURE'}
    if not local_only:
        write(OUT,hold)
    p=load(TASK/'manifests/V4_4_PREREGISTRATION.json')
    m=load(TASK/'manifests/V4_4_MODEL_PROTOCOL.json')
    rrows=verify_runtime_lock(p)
    modelmap={r['name']:r for r in m['models']}
    runtime={r['id']:r for r in rrows}
    raw,calls,scored,gold=derive()
    intents=list(lines(TASK/'raw_runs/final_request_intents.jsonl'))
    receipts=list(lines(TASK/'raw_runs/final_physical.jsonl'))
    summary=load(TASK/'statistics/SUMMARY.json')
    checks=[]
    def check(name,passed,detail):
        checks.append({'name':name,'passed':bool(passed),'detail':detail})
    expected={(model,f'{r["id"]}/q{i}') for model in modelmap for r in rrows for i in range(r.get('attack_surface',{}).get('queries',1))}
    check('registered_units_and_nonempty_model_scope',len(expected)==480 and {(r['model'],r['unit']) for r in raw}==expected,
          {'expected':len(expected),'observed':len(raw)})
    check('held_out_registration_before_physical_requests',
          bool(intents) and all(datetime.fromisoformat(i['started_utc'])>datetime.fromisoformat(p['local_registered_utc']) for i in intents),
          {'registered_utc':p['local_registered_utc'],'first_intent_utc':intents[0]['started_utc'] if intents else None})
    check('unique_requests_receipts_with_consistent_identities',len(intents)==len(receipts)==len(calls)==len({x['id'] for x in intents}) and
          {i['id'] for i in intents}==set(calls) and all(c['model_digest']==modelmap[c['model']]['digest'] for c in receipts),
          {'intents':len(intents),'receipts':len(receipts),'unique':len(calls)})
    check('response_and_failure_receipts',all(
          c.get('request_sha256')==digest(c['request']) and c['request']['options']==m['options'] and
          (c['status']!='COMPLETED' or (c['response']['done'] is True and c['response']['done_reason']=='stop' and c['response']['eval_count']>0))
          if 'request' in c else c['status']=='INTERRUPTED_NO_RECEIPT' for c in receipts),
          'Exact local request, model response, token/termination or explicit error; no assumption from zero scores')
    bans={'gold','oracle','expected_effects','expected_answer','expected_outcome','judge_metadata','attack_goal'}
    check('runtime_and_oracle_separation',set(runtime)==set(gold) and all(not bans&set(r) for r in rrows) and
          all(not any(v['value'] in c['request']['prompt'] for v in runtime[c['unit'].rsplit('/q',1)[0]]['records'].values() if v['visibility']=='restricted')
              for c in receipts if 'request' in c),
          'No offline labels or synthetic secret literal in transmitted custom prompts')
    duplicate=load(TASK/'audits/DATASET_DUPLICATION_AUDIT.json')
    check('disjoint_development_cases_and_sources',not any(duplicate['exact_cross_split_counts'].values()),duplicate['exact_cross_split_counts'])
    check('fair_arm_population_and_proposal_inputs',all(set(r['arms'])==set((*ARMS,*ABLATIONS) if gold[r['case_id']]['attack'] else ARMS)
          and r['arms']['C1_flat']['call_ids']==r['arms']['C2_typed']['call_ids'] for r in raw),
          'Same model receipts for each matched pair; outcome agreement is not a gate')
    problems=check_replay(raw,calls,runtime,modelmap)
    check('offline_replay_of_every_model_proposal',not problems,
          {'issues':problems[:15],'arms_replayed':len(scored),'ephemeral_hmac_tags':'linkage checked; fresh keys change tags'})
    derived=[]
    for table in summary['tables']:
        rs=[r for r in scored if all(r[k]==table[k] for k in ('model','population','arm'))]
        cond=(len(rs)==table['observed'] and sum(r['e2e_asr'] is True for r in rs)==table['e2e']
              and sum(r['strict_complete'] for r in rs)==table['strict_complete']
              and table['planned']-sum(r['e2e_asr'] is not None for r in rs)==table['unknown_e2e'])
        if not cond:derived.append({k:table[k] for k in ('model','population','arm')})
    check('raw_summary_alignment',not derived and summary['physical_receipts']==len(receipts),derived)
    check('both_models_with_gpu_and_digests',len(modelmap)==2 and all(
          m['pilot'][name]['gpu_peak_sample_MiB']>1000 and any(r['model']==name and r['status']=='COMPLETED' for r in receipts)
          for name in modelmap),'Distinct 3.8B / 7.6B backbone; not selected by final utility')
    n=native_summary()
    if not local_only:
        write(TASK/'results/native_benchmark_results.json',n)
    check('native_fidelity_accurately_classified',n['fidelity'] in ('NATIVE_ENGINE_CUSTOM_FRONTEND_SCOPED','UNVERIFIED'),n['fidelity'])
    frozen=load(TASK/'manifests/V4_3_IMMUTABLE_INPUTS.json')
    check('v43_frozen_core',frozen['core_matches_historical'] and bool(frozen['core']) and (
          local_only or all(sha(ROOT/key)==value for key,value in frozen['core'].items())),
          {'core_files':len(frozen['core']),'historical_full_differences':frozen['historical_differences'],
           'local_source_read':not local_only})
    freshpath=TASK/'audits/FRESH_EXTRACTION_RECEIPT.json'
    if not local_only:
        fresh=load(freshpath) if freshpath.is_file() else {}
        check('clean_extract_and_recount',fresh.get('clean_extract_tests_passed') is True and fresh.get('summary_bytes_identical') is True,fresh)
    result={**hold,'freeze':FREEZE,'science_valid':all(r['passed'] for r in checks),
            'evidence_valid':all(r['passed'] for r in checks),'checks':checks,
            'status':'SCOPED_VALID' if all(r['passed'] for r in checks) else 'HOLD_EVIDENCE',
            'models_completed':[name for name in modelmap if sum(r['model']==name for r in raw)==240],
            'unscored_backend_failures':sum(c['status'] in ('BACKEND_ERROR','MODEL_ERROR','CUDA_OOM','TIMEOUT','INTERRUPTED_NO_RECEIPT') for c in receipts),
            'unscored_logical':sum(not r['fully_scored'] for r in scored),'native_benchmark_fidelity':n['fidelity'],
            'limitations_required':['No typed-superiority or equivalence inference','Synthetic authored tasks and adaptive variants',
              'Bounded reference-based egress and limited encodings','Official native subset is exploratory',
              'Same-machine clean restore only','Human review, rights and exact-version approvals pending']}
    if not local_only:
        write(OUT,result)
    print(json.dumps({'checks_passed':sum(r['passed'] for r in checks),'checks_total':len(checks),
                      'science_valid':result['science_valid'],'release_authorized':False,
                      'failed':[r['name'] for r in checks if not r['passed']]},ensure_ascii=False),flush=True)
    return result


if __name__=='__main__':
    import sys
    result=validate(local_only='--extracted' in sys.argv)
    if not result['science_valid']:
        raise SystemExit(1)
