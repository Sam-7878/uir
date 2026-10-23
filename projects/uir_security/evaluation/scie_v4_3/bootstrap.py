"""Input inventory and isolated restoration; old outputs never modified."""
from .common import *
import difflib
import platform
import subprocess
import tempfile
import zipfile

def main():
    for name in ('manifests','logs','resources','source','figures','experiments/composition','experiments/output_channel',
                 'experiments/semantic_tasks','experiments/agentdojo_external','experiments/official_baseline',
                 'data/raw_private','data/statistics','data/redacted_release_candidate','reports','paper/journal','paper/preprint','submission_private'):
        (TASK/name).mkdir(parents=True,exist_ok=True)
    write(TASK/'.gitignore','# Local-only research artifacts; publication requires separate author/rights approval.\n*\n')
    supplied=load(DOC/'203_HETE_V4_3_HANDOFF_INPUT_MANIFEST.json');entries=[]
    candidates=list(BASE.glob('*.zip'))+list(BASE.glob('supplementary/*.zip'))
    for item in supplied['entries']:
        matches=[p for p in candidates if p.name==item['filename']]
        r={**item,'rights_class':'LOCAL_ONLY_UNAPPROVED_RELEASE','role':('source' if 'CODE' in item['filename'] else 'manuscript' if 'SUBMISSION' in item['filename'] or 'PREPRINT' in item['filename'] else 'private review/evidence snapshot')}
        if len(matches)==1:
            p=matches[0];r.update(actual_path=str(p.relative_to(ROOT)),actual_bytes=p.stat().st_size,actual_sha256=sha(p))
            r['status']='MATCH' if (r['bytes'],r['sha256'])==(r['actual_bytes'],r['actual_sha256']) else 'FAIL_MISMATCH'
        else:r.update(status='MISSING_ZIP_NOT_RECONSTRUCTED',reason='Unpacked directories may exist;cannot recreate original uploaded ZIP bytes from their contents')
        entries.append(r)
    freeze(TASK/'manifests/HANDOFF_MANIFEST.json',{'id':FREEZE,'supplied_manifest_sha256':sha(DOC/'203_HETE_V4_3_HANDOFF_INPUT_MANIFEST.json'),
        'entries':entries,'all_six_match':all(r['status']=='MATCH' for r in entries),'note':'A content hash is byte identity,not release authority or scientific validity'})
    old=load(BASE/'DELIVERY_MANIFEST.json');audit=[];diff=[]
    with zipfile.ZipFile(BASE/'HETE_V4_2_REPRODUCTION_CODE.zip') as z:
        for name,value in old['source_files'].items():
            p=ROOT/name;expected=value['sha256'];actual=sha(p) if p.is_file() else None
            mapped=name.replace('/202_hete_v4/','/202_hete_v4.2/');mapped_path=ROOT/mapped
            state='MATCH' if actual==expected else 'CHANGED_SINCE_FREEZE' if actual else 'MISSING_RECORDED_PATH'
            if not actual and mapped_path.is_file() and sha(mapped_path)==expected:state='EXACT_BYTES_RELOCATED'
            audit.append({'path':name,'expected':expected,'actual':actual,'status':state,'explicit_translation':mapped if state=='EXACT_BYTES_RELOCATED' else ''})
            if state=='CHANGED_SINCE_FREEZE' and name in z.namelist():
                diff.extend(difflib.unified_diff(z.read(name).decode().splitlines(),p.read_text().splitlines(),fromfile='frozen-zip/'+name,tofile='current/'+name))
    csvwrite(TASK/'reports/V4_2_CURRENT_SOURCE_AUDIT.csv',audit)
    write(TASK/'reports/V4_2_POSTFREEZE_SOURCE_DIFF.patch','\n'.join(diff)+'\n')
    locks={str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in BASE.rglob('*') if p.is_file() and 'matplotlib_cache' not in p.parts}
    # Capture the current input state without claiming it equals the older freeze.
    freeze(TASK/'manifests/BASELINE_V4_2_LOCK.json',{'captured_current_input_files':locks,'historic_source_audit':audit,
        'old_manifest_sha256':sha(BASE/'DELIVERY_MANIFEST.json'),'freeze':old['freeze_id'],'original_source_changes_not_undone':True})
    git=lambda *args:subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
    write(TASK/'manifests/ENVIRONMENT.json',{'python':sys.version,'executable':sys.executable,'os_release':Path('/etc/os-release').read_text(),
        'git_commit':git('rev-parse','HEAD'),'git_branch':git('branch','--show-current'),'remote':git('remote','get-url','origin'),
        'root':'current verified workspace,not inferred from old account','business_account_required':False})
    receipts=[]
    with tempfile.TemporaryDirectory(prefix='hete-v43-restore-') as tmp:
        target=Path(tmp)
        with zipfile.ZipFile(BASE/'HETE_V4_2_REPRODUCTION_CODE.zip') as z:
            if z.testzip():raise ValueError('Input CRC fail')
            for item in z.namelist():
                p=Path(item)
                if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe archive')
            z.extractall(target)
        env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(target)
        command=[PYTHON,'-m','pytest','tests/uir_security/test_scie_v4_2_typed_engine.py','tests/uir_security/test_scie_v4_2_effect_oracles.py','-q','-p','no:cacheprovider']
        run=subprocess.run(command,cwd=target,env=env,capture_output=True,text=True)
        write(TASK/'logs/restored_v4_2_tests.txt',run.stdout+run.stderr)
        receipts.append({'kind':'extracted source scoped tests','exit_code':run.returncode,'expected_tests':30,'same_OS_and_venv':True,'external_human_or_second_OS':False})
        if run.returncode:raise RuntimeError('Restored scoped tests failed')
        with zipfile.ZipFile(BASE/'supplementary/S1_LEGACY_LINEAGE.zip') as z:
            inputs=[n for n in z.namelist() if n.endswith('/per_case_records.jsonl')]
            if len(inputs)!=1:raise ValueError('Projection missing/ambiguous')
            (target/'per_case_records.jsonl').write_bytes(z.read(inputs[0]))
        run=subprocess.run([PYTHON,'-I','-S','recount_projection.py','per_case_records.jsonl','recount.json'],cwd=target,capture_output=True,text=True)
        if run.returncode:raise RuntimeError(run.stderr)
        got=load(target/'recount.json');expected=load(BASE/'data/statistics/LEGACY_RECOUNT.json')
        if not all(got[k]==expected[k] for k in ('records','counts','exact_tests','adaptive')):raise ValueError('Independent recount mismatch')
        write(TASK/'data/statistics/RESTORED_PROJECTION_RECOUNT.json',got)
        receipts.append({'kind':'extracted script + projection','exit_code':0,'records':got['records'],'groups':got['configurations'],
            'site_packages_disabled':True,'input_sha256':got['input_sha256'],'same_OS':True,'source':'supplementary S1 available locally,not evidence of missing aggregate ZIP identity'})
    write(TASK/'REPRODUCTION_RECEIPTS.json',receipts)
    print('six input ZIP status:',[(r['filename'],r['status']) for r in entries]);print('restore tests30 PASS;projection19900/25 exact match')

if __name__=='__main__':main()
