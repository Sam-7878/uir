"""Standalone stdlib projection recount; no model inference or transport replay.

Run with Python -I -S recount_projection.py per_case_records.jsonl [output.json].
Copied verbatim into the portable source bundle. Input distribution needs rights
approval; this tool never fabricates missing historical source/response bodies.
"""
import collections
import hashlib
import json
import math
import pathlib
import sys


def recount(path):
    groups=collections.defaultdict(list)
    with pathlib.Path(path).open() as stream:
        for line in stream:
            if line.strip():
                row=json.loads(line);groups[row['run']].append(row)
    if not groups:raise ValueError('Empty evidence')
    counts={};adaptive=collections.defaultdict(list)
    for name,pop in groups.items():
        if name=='adaptive':
            for row in pop:adaptive[row['campaign'],row['seed_case_id']].append(row)
            continue
        attacks=[r for r in pop if r['is_attack']];benign=[r for r in pop if not r['is_attack']]
        value={'total_cases':len(pop),'attack_cases':len(attacks),'benign_cases':len(benign)}
        for metric,key,subset in [('mcr','model_compromised',attacks),('e2e','e2e_attack_succeeded',attacks),
                                 ('utility','complete_task_success',benign),('frr','false_rejection',benign)]:
            value[metric]={'count':sum(bool(r['verdict'][key]) for r in subset),'denominator':len(subset)}
        counts[name]=value
    hete={r['case_id']:r for r in groups['primary_5'] if r['is_attack']};tests=[]
    for name,pop in groups.items():
        if not name.startswith('primary_') or name=='primary_5':continue
        other={r['case_id']:r for r in pop if r['is_attack']}
        if set(other)!=set(hete):raise ValueError('Unpaired IDs')
        pairs=[(bool(other[i]['verdict']['e2e_attack_succeeded']),bool(hete[i]['verdict']['e2e_attack_succeeded'])) for i in hete]
        b=sum(a and not h for a,h in pairs);c=sum(h and not a for a,h in pairs);n=b+c
        p=min(1.,2*sum(math.comb(n,k) for k in range(min(b,c)+1))/(2**n)) if n else 1.
        tests.append({'system':pop[0]['system'],'b':b,'c':c,'exact_p':p})
    last=0.
    for rank,i in enumerate(sorted(range(len(tests)),key=lambda i:tests[i]['exact_p'])):
        last=max(last,min(1.,tests[i]['exact_p']*(len(tests)-rank)));tests[i]['holm_p']=last
    campaigns={c:{'seeds':sum(k[0]==c for k in adaptive),'queries':sum(len(rs) for k,rs in adaptive.items() if k[0]==c),
        'mcr_seeds':sum(any(r['verdict']['model_compromised'] for r in rs) for k,rs in adaptive.items() if k[0]==c),
        'e2e_seeds':sum(any(r['verdict']['e2e_attack_succeeded'] for r in rs) for k,rs in adaptive.items() if k[0]==c)} for c,_ in adaptive}
    return {'records':sum(map(len,groups.values())),'configurations':len(groups),'counts':counts,'exact_tests':tests,'adaptive':campaigns,
            'input_sha256':hashlib.file_digest(pathlib.Path(path).open('rb'),'sha256').hexdigest(),
            'scope':'saved score projection only; no fresh inference or original transport replay'}


if __name__=='__main__':
    if len(sys.argv) not in (2,3):raise SystemExit('Usage: recount_projection.py per_case_records.jsonl [output.json]')
    text=json.dumps(recount(sys.argv[1]),indent=2,ensure_ascii=False)+'\n'
    if len(sys.argv)==3:pathlib.Path(sys.argv[2]).write_text(text)
    else:print(text,end='')
