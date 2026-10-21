"""Local-only, complete manuscript bundles and standalone offline score replay."""
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from .common import FROZEN, PROJECT, TASK, load, sha, write

REPLAY=r'''"""Standalone offline replay using the included pinned wheels."""
import csv, hashlib, json, math
from collections import defaultdict
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent))
if len(sys.argv)>1:sys.path.insert(0,str(Path(sys.argv[1]).absolute()))
from scorer.judges.security_evaluator import SecurityEvaluatorV32
from scorer.schema.oracle_case import OracleCase

root=Path(__file__).parent
manifest=json.loads((root/'MANIFEST.json').read_text())
for name,digest in manifest.items():
    path=root/name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise SystemExit('Hash mismatch: '+name)
expected=json.loads((root/'expected.json').read_text())
evaluator=SecurityEvaluatorV32();groups=defaultdict(list);adaptive=defaultdict(list);mismatches=[]
for line in (root/'per_case_records.jsonl').open():
    r=json.loads(line);v=evaluator.evaluate_case(r['execution'],OracleCase.from_dict(r['oracle']))
    for key in ('model_compromised','e2e_attack_succeeded','complete_task_success','false_rejection'):
        if bool(v.get(key))!=bool(r['verdict'].get(key)):mismatches.append([r['run'],r['case_id'],key])
    r['replayed_verdict']=v;groups[r['run']].append(r)
    if r['run']=='adaptive':adaptive[(r['campaign'],r['seed_case_id'])].append(r)
actual={}
for name,records in groups.items():
    if name=='adaptive':continue
    attacks=[r for r in records if r['is_attack']];benign=[r for r in records if not r['is_attack']]
    actual[name]={'total_cases':len(records),'attack_cases':len(attacks),'benign_cases':len(benign)}
    for metric,field,pop in [('mcr','model_compromised',attacks),('e2e','e2e_attack_succeeded',attacks),
                              ('utility','complete_task_success',benign),('frr','false_rejection',benign)]:
        actual[name][metric]={'count':sum(bool(r['replayed_verdict'].get(field)) for r in pop),'denominator':len(pop)}
if actual!=expected['counts']:mismatches.append('aggregate tables differ')
campaigns={}
for campaign in expected['adaptive']:
    seeds=[records for (c,s),records in adaptive.items() if c==campaign]
    campaigns[campaign]={'seeds':len(seeds),'queries':sum(map(len,seeds)),
        'mcr_seeds':sum(any(r['replayed_verdict']['model_compromised'] for r in rs) for rs in seeds),
        'e2e_seeds':sum(any(r['replayed_verdict']['e2e_attack_succeeded'] for r in rs) for rs in seeds)}
if campaigns!=expected['adaptive']:mismatches.append('adaptive seed aggregates differ')
hete={r['case_id']:r for r in groups['primary_5'] if r['is_attack']};exact=[]
for name,system in expected['primary_names'].items():
    if name=='primary_5':continue
    other={r['case_id']:r for r in groups[name] if r['is_attack']}
    if set(other)!=set(hete):raise SystemExit('Unpaired cases: '+name)
    b=sum(other[i]['replayed_verdict']['e2e_attack_succeeded'] and not hete[i]['replayed_verdict']['e2e_attack_succeeded'] for i in hete)
    c=sum(not other[i]['replayed_verdict']['e2e_attack_succeeded'] and hete[i]['replayed_verdict']['e2e_attack_succeeded'] for i in hete)
    n=b+c;p=min(1.,2*sum(math.comb(n,j) for j in range(min(b,c)+1))/2**n) if n else 1.
    exact.append({'system':system,'b':b,'c':c,'exact_p':p})
previous=0.
for rank,i in enumerate(sorted(range(len(exact)),key=lambda i:exact[i]['exact_p'])):
    previous=max(previous,min(1.,exact[i]['exact_p']*(len(exact)-rank)));exact[i]['holm_p']=previous
for result in exact:
    ref=next(e for e in expected['exact'] if e['system']==result['system'])
    if any(not math.isclose(result[k],ref[k],rel_tol=1e-12) for k in ('exact_p','holm_p')):mismatches.append(result['system']+' exact p')
report={'passed':not mismatches,'records':sum(map(len,groups.values())),'mismatches':mismatches,
        'counts':actual,'adaptive':campaigns,'exact_tests':exact,
        'scope':'tokenized admitted execution projection; not original transport replay or human certification'}
(root/'REPLAY_RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('counts','adaptive','exact_tests')}))
raise SystemExit(bool(mismatches))
'''


def archive(directory,destination):
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(directory.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                archive.write(path,path.relative_to(directory))


def main():
    candidate=TASK/'resources/publication_candidate_local';source=PROJECT/'evaluation/llm_security_v3_2'
    scorer=candidate/'scorer';scorer.mkdir(exist_ok=True)
    shutil.copy2(source/'__init__.py',scorer/'__init__.py')
    for sub in ('judges','schema'):
        target=scorer/sub;target.mkdir(exist_ok=True)
        for path in (source/sub).glob('*.py'):shutil.copy2(path,target/path.name)
    target=scorer/'harness';target.mkdir(exist_ok=True)
    for name in ('__init__.py','agency_harness.py'):shutil.copy2(source/'harness'/name,target/name)
    expected={};names={}
    import csv
    index=list(csv.DictReader((TASK/'data/run_index.csv').open()))
    baseline=load(FROZEN/'baseline_comparison.json');ablations=load(FROZEN/'ablation_results.json')
    models=load(FROZEN/'multi_model_results.json');stochastic=load(FROZEN/'stochastic_results.json')
    for item in index:
        run=item['run'];name=item['system_or_config']
        if run.startswith('primary_'):value=baseline[name];names[run]=name
        elif run.startswith('ablation_'):value=ablations[name]
        elif run=='multimodel_phi':value=models[name]
        else:value=stochastic[name]
        expected[run]={k:({x:value[k][x] for x in ('count','denominator')} if k in ('mcr','e2e','utility','frr') else value[k])
                       for k in ('total_cases','attack_cases','benign_cases','mcr','e2e','utility','frr')}
    write(candidate/'expected.json',{'counts':expected,'primary_names':names,
        'adaptive':load(FROZEN/'adaptive_attack_results.json'),'exact':load(TASK/'data/exact_statistics_recomputed.json')})
    write(candidate/'reproduce.py',REPLAY)
    write(candidate/'OFFLINE_REPLAY.md','# Standalone score replay\n\n'
          'Pinned wheel dependencies and a wheel built from the shared package pyproject.toml are included. '
          'The cp314 Linux dependency wheel targets the specified Ubuntu Python 3.14 environment. '
          'No source repository, model, GPU or network is needed after extraction. Choose an empty temporary dependency directory.\n\n'
          '```bash\npython -m pip install --no-index --find-links ./wheels --target /tmp/hete-replay-deps uir-research==0.2.0\n'
          'python -I -S reproduce.py /tmp/hete-replay-deps\n```\n\n'
          'This checks every payload/scorer hash, rejudges 19,900 records, regenerates all primary/ablation/stochastic/Phi counts, '
          'adaptive seed aggregates and exact paired McNemar/Holm values. The tokenized payload is a score projection; '
          'missing original interrupted response bodies remain missing. No public release authorization is implied.\n')
    manifest={str(p.relative_to(candidate)):sha(p) for p in sorted(candidate.rglob('*'))
              if p.is_file() and p.name not in ('MANIFEST.json','REPLAY_RESULT.json') and '__pycache__' not in p.parts}
    write(candidate/'MANIFEST.json',manifest)
    dependencies=TASK/'resources/portable_replay_dependencies'
    if not dependencies.exists():
        install=subprocess.run(['/mnt/d/_Work/goat_bank/.venv_cuda/bin/python','-m','pip','install','--no-index',
                    '--find-links',str(candidate/'wheels'),'--target',str(dependencies),'uir-research==0.2.0'],capture_output=True,text=True)
        write(TASK/'logs/portable_dependency_install.log',install.stdout+install.stderr)
        if install.returncode:raise RuntimeError(install.stdout+install.stderr)
    result=subprocess.run(['/mnt/d/_Work/goat_bank/.venv_cuda/bin/python','-I','-S','reproduce.py',str(dependencies)],cwd=candidate,
                          capture_output=True,text=True)
    write(TASK/'logs/standalone_replay.log',result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    archive(candidate,TASK/'resources/HETE_EVIDENCE_LOCAL_CANDIDATE.zip')
    for stem,wrapper in [('HETE_PREPRINT_V1','HETE_PREPRINT_V1.tex'),('HETE_JOURNAL_SOURCE','HETE_JOURNAL.mdpi.tex')]:
        bundle=TASK/'resources'/('bundle_'+stem);bundle.mkdir(exist_ok=True)
        for name in (wrapper,'manuscript_body.tex','v3_2_evidence.tex','references_clean.bib','boundary_trace.pdf'):
            shutil.copy2(TASK/'manuscript_private'/name,bundle/name)
        pdf=wrapper.removesuffix('.tex')+'.pdf';shutil.copy2(TASK/'manuscript_private'/pdf,bundle/pdf)
        if stem=='HETE_JOURNAL_SOURCE':
            if (bundle/'Definitions').exists():shutil.rmtree(bundle/'Definitions')
            shutil.copytree(TASK/'manuscript_private/Definitions',bundle/'Definitions')
        write(bundle/'BUILD.md','# Build this local draft\n\nNot posted/submitted. Author statements and release rights remain pending. '
              'Install standard TeX Live latex-base, latex-recommended, latex-extra, plain-generic, fonts-recommended and science packages. '
              'MDPI class/styles and derived logo PDFs are included in the journal bundle. No repository-relative external files are needed.\n\n'
              f'Run `pdflatex -no-shell-escape {wrapper}`, `bibtex {wrapper.removesuffix(".tex")}`, then pdflatex twice more. '
              'The harmless epstopdf shell-escape-disabled warning is expected; all used graphics already exist as PDF.\n')
        write(bundle/'MANIFEST.json',{str(p.relative_to(bundle)):sha(p) for p in sorted(bundle.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'})
        archive(bundle,TASK/'resources'/(stem+'.zip'))
    receipt={'local_only':True,'standalone_replay':load(candidate/'REPLAY_RESULT.json')['passed'],
             'artifacts':[{ 'path':str(p.relative_to(TASK)),'bytes':p.stat().st_size,'sha256':sha(p)}
                          for p in sorted((TASK/'resources').glob('HETE_*.zip'))]}
    write(TASK/'manifests/LOCAL_BUNDLES.json',receipt)
    print(json.dumps(receipt))


if __name__=='__main__':main()
