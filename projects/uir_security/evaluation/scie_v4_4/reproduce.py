"""Build a restricted evidence ZIP, actually extract it and recompute."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from .common import FREEZE,ROOT,SOURCE,TASK,sha,write

P=TASK/'private/HETE_V4_4_REPRODUCTION_PRIVATE.zip'


def package():
    source=[p for p in SOURCE.rglob('*') if p.is_file() and p.suffix in ('.py','.md') and '__pycache__' not in p.parts]
    paths=[ROOT/'AGENTS.md',ROOT/'LICENSE',ROOT/'tests/uir_security/test_scie_v4_4.py',*source]
    for relative in ('projects/__init__.py','projects/uir_security/__init__.py','projects/uir_security/evaluation/__init__.py'):
        if (ROOT/relative).is_file(): paths.append(ROOT/relative)
    paths+=list((TASK/'private/datasets').glob('*.json'))
    paths+=list((TASK/'raw_runs').glob('*.jsonl'))
    paths += [TASK/'manifests'/n for n in ('V4_3_IMMUTABLE_INPUTS.json','V4_4_PREREGISTRATION.json','V4_4_MODEL_PROTOCOL.json',
                'V4_4_DATASET_SPLITS.json','V4_4_BASELINE_FIDELITY.json','V4_4_AGENTDOJO_NATIVE_PROTOCOL.json')]
    paths += [TASK/'audits'/n for n in ('DATASET_DUPLICATION_AUDIT.json','NATIVE_ORACLE_CONTROLS.json')]
    paths += [TASK/'statistics/SUMMARY.json']
    paths += [TASK/'audits'/n for n in ('NATIVE_EXPOSURE_RECOUNT.json','SAFE_PARTIAL_ACTUAL_TEXT_CHECK.json')]
    paths += [TASK/'statistics/SAFE_PARTIAL_SECONDARY_AMENDMENT.json']
    with zipfile.ZipFile(P,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p in sorted(set(paths)):
            if not p.is_file() or p.stat().st_size==0:
                raise ValueError('Missing or empty reproduction input '+str(p))
            z.write(p,str(p.relative_to(ROOT)))
        z.writestr('pytest.ini','[pytest]\npythonpath = .\n')
        z.writestr('FREEZE_ID.txt',FREEZE+'\nPRIVATE; do not publish\n')
    with tempfile.TemporaryDirectory(prefix='hete-v44-reproduction-') as tmp, zipfile.ZipFile(P) as z:
        if z.testzip() or len(set(z.namelist()))!=len(z.namelist()):
            raise ValueError('Archive CRC/name error')
        for name in z.namelist():
            if Path(name).is_absolute() or '..' in Path(name).parts:
                raise ValueError('Unsafe path')
        z.extractall(tmp)
        local=Path(tmp)
        env=dict(os.environ, PYTHONPATH=tmp,PYTHONDONTWRITEBYTECODE='1')
        stem='projects.uir_security.evaluation.scie_v4_4'
        commands=[[sys.executable,'-B','-c','from pathlib import Path; from '+stem+' import engine; assert Path(engine.__file__).resolve().is_relative_to(Path.cwd()); print(engine.__file__)'],
                  [sys.executable,'-B','-m','pytest','tests/uir_security/test_scie_v4_4.py','-q','-p','no:cacheprovider'],
                  [sys.executable,'-B','-m',stem+'.aggregate'],[sys.executable,'-B','-m',stem+'.validate_evidence','--extracted']]
        outputs=[]
        for cmd in commands:
            p=subprocess.run(cmd,env=env,cwd=local,capture_output=True,text=True)
            outputs.append('$ '+' '.join(cmd)+'\n'+p.stdout+p.stderr)
            (TASK/'audits/FRESH_EXTRACTION.log').write_text('\n'.join(outputs),encoding='utf-8')
            if p.returncode:
                raise RuntimeError('Extracted replay failed: '+p.stdout[-800:]+p.stderr[-800:])
        target=local/TASK.relative_to(ROOT)/'statistics/SUMMARY.json'
        same=sha(target)==sha(TASK/'statistics/SUMMARY.json')
        if not same:
            raise ValueError('Fresh aggregate not identical')
    receipt={'freeze':FREEZE,'archive_sha256':sha(P),'archive_bytes':P.stat().st_size,'same_os':True,
             'actual_extract_and_execution':True,'clean_extract_tests_passed':True,
             'summary_bytes_identical':same,'offline_raw_sqlite_replay':True,
             'no_fresh_model_inference':True,'independent_human_or_other_os':False}
    write(TASK/'audits/FRESH_EXTRACTION_RECEIPT.json',receipt)
    print(receipt,flush=True)


if __name__=='__main__':
    package()
