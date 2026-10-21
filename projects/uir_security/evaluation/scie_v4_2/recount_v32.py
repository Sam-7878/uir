"""Independent aggregation of the saved projection, without the V4 replay code."""
import math
from collections import defaultdict
from .common import *


def main():
    candidate=OLD/'resources/publication_candidate_local';saved=load(candidate/'REPLAY_RESULT.json')
    groups=defaultdict(list);mapping=[];adaptive=defaultdict(list)
    for record in rows(candidate/'per_case_records.jsonl'):
        groups[record['run']].append(record)
        if record['run']=='adaptive':adaptive[(record['campaign'],record['seed_case_id'])].append(record)
        mapping.append({'claim_population':record['run'],'case_id':record['case_id'],
            'input_record_hash':record['original_record_json_sha256'],
            'projection_hash':digest(record),'score_version':'frozen V3.2 recorded verdict; independently aggregated',
            'outcome_predicates':'MCR:behavior; E2E:class-specific effect/resource; utility:whole benign contract',
            'manuscript_target':'historical Table 3 and Supplement S1'})
    actual={};checks=[]
    for name,pop in groups.items():
        if name=='adaptive':continue
        attacks=[r for r in pop if r['is_attack']];benign=[r for r in pop if not r['is_attack']]
        result={'total_cases':len(pop),'attack_cases':len(attacks),'benign_cases':len(benign)}
        for metric,key,subset in [('mcr','model_compromised',attacks),('e2e','e2e_attack_succeeded',attacks),
                                 ('utility','complete_task_success',benign),('frr','false_rejection',benign)]:
            result[metric]={'count':sum(bool(r['verdict'][key]) for r in subset),'denominator':len(subset)}
        actual[name]=result
        checks.append({'population':name,'records':len(pop),'matched':result==saved['counts'][name]})
    hete={r['case_id']:r for r in groups['primary_5'] if r['is_attack']};tests=[]
    for name,pop in groups.items():
        if not name.startswith('primary_') or name=='primary_5':continue
        other={r['case_id']:r for r in pop if r['is_attack']}
        if set(other)!=set(hete):raise ValueError('Unpaired IDs')
        d=[(bool(other[i]['verdict']['e2e_attack_succeeded']),bool(hete[i]['verdict']['e2e_attack_succeeded'])) for i in hete]
        b=sum(a and not h for a,h in d);c=sum(h and not a for a,h in d);n=b+c
        p=min(1.,sum(math.comb(n,k) for k in range(min(b,c)+1))*2./(2**n)) if n else 1.
        tests.append({'system':pop[0]['system'],'b':b,'c':c,'exact_p':p})
    last=0.
    for rank,i in enumerate(sorted(range(len(tests)),key=lambda i:tests[i]['exact_p'])):
        last=max(last,min(1.,tests[i]['exact_p']*(len(tests)-rank)));tests[i]['holm_p']=last
    for test in tests:
        ref=next(t for t in saved['exact_tests'] if t['system']==test['system'])
        if not all(math.isclose(test[k],ref[k],rel_tol=1e-12) for k in ('exact_p','holm_p')):raise ValueError(test)
    campaigns={c:{'seeds':sum(k[0]==c for k in adaptive),'queries':sum(len(rs) for k,rs in adaptive.items() if k[0]==c),
        'mcr_seeds':sum(any(r['verdict']['model_compromised'] for r in rs) for k,rs in adaptive.items() if k[0]==c),
        'e2e_seeds':sum(any(r['verdict']['e2e_attack_succeeded'] for r in rs) for k,rs in adaptive.items() if k[0]==c)}
        for c,_ in adaptive}
    if campaigns!=saved['adaptive']:raise ValueError('Adaptive aggregates differ')
    if sum(map(len,groups.values()))!=19900 or not all(r['matched'] for r in checks):raise ValueError('Recount differs')
    csvwrite(TASK/'data/RAW_TO_CLAIM_MAP.csv',mapping);csvwrite(TASK/'data/statistics/INDEPENDENT_RECOUNT.csv',checks)
    write(TASK/'data/statistics/LEGACY_RECOUNT.json',{'passed':True,'records':19900,'configurations':len(groups),
        'counts':actual,'exact_tests':tests,'adaptive':campaigns,'scope':'independent aggregate of saved scoring projection, not new inference or reconstructed transport'})
    # Check the explicitly declared byte scope; never repair old files in place.
    entries=load(FROZEN/'ARTIFACT_MANIFEST.json')['artifacts'];bad=[];science=[]
    for e in entries:
        p=FROZEN/e['path'];ok=p.is_file() and sha(p)==e['sha256']
        if not ok:bad.append(e['path'])
        if e['path'].endswith('.pyc'):continue
        overlay=OLD/'resources/recovered_v32_overlay'/e['path'];selected=overlay if overlay.is_file() else p
        science.append(selected.is_file() and sha(selected)==e['sha256'])
    if len(science)!=418 or not all(science):raise ValueError('Science scope changed')
    write(TASK/'reports/LEGACY_INTEGRITY_REPORT.md',f'# Independent V4.2 legacy audit\n\n19,900 records in {len(groups)} configurations; aggregate metrics and exact McNemar/Holm match the saved replay. '
        f'Original full manifest: {len(entries)} entries, {len(bad)} mismatches. Explicit overlay verifies all 418 non-bytecode entries; 54 bytecode entries remain unrecovered. '
        'The current local input ZIPs contain nonzero PDFs (see INPUT_PACKAGE_INSPECTION.json); the earlier uploaded-copy 0-byte finding is preserved as the reviewer observation and not retroactively denied. '
        'This is scoring-projection aggregation and byte checking, not historical inference or original transport replay.\n')
    write(TASK/'reports/ATTRITION_AND_AMENDMENT.md',(OLD/'reports/lineage.md').read_text()+'\nOriginal interrupted bodies/timestamps remain unavailable. No fabricated recovery. Source amendment data and interruption ledger remain locked in the old task; the V4.2 claim map does not turn excluded attempts into completed cases.\n')
    print('records',19900,'groups',len(groups),'original mismatches',len(bad),'science verified',sum(science))


if __name__=='__main__':main()
