"""Build local review ZIPs and actually reproduce their supported scope."""
from .common import *
from .build import compile_one
import shutil
import subprocess
import tempfile
import zipfile

def archive(path,files,root,extra=None):
    names=[]
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted(files):
            if not file.is_file() or file.stat().st_size==0:raise ValueError('Missing/empty '+str(file))
            name=str(file.relative_to(root))
            if name in names:raise ValueError('Duplicate archive member')
            z.write(file,name);names.append(name)
        for name,text in (extra or {}).items():
            if name in names:raise ValueError('Duplicate extra member')
            z.writestr(name,text);names.append(name)
    with zipfile.ZipFile(path) as z:
        if z.testzip() or any(i.file_size==0 for i in z.infolist()):raise ValueError('CRC/empty member')
    return {'path':str(path.relative_to(TASK)),'sha256':sha(path),'bytes':path.stat().st_size,'members':len(names),'CRC':'PASS','freeze':FREEZE,'public_release_authorized':False}

def safe_extract(path,target):
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('Unsafe extraction')
        z.extractall(target)

def main():
    packages=[]
    for folder,main,name in [('journal','HETE_JOURNAL_V4_3.tex','ELECTRONICS_V4_3_REVIEW_SOURCE.zip'),('preprint','HETE_PREPRINT_V3.tex','HETE_PREPRINT_V3.zip')]:
        directory=TASK/'paper'/folder
        write(directory/'FREEZE_ID.txt',FREEZE+'\nLOCAL REVIEW ONLY;PUBLICATION HOLD\n')
        write(directory/'README_BUILD.md',f'''# Source build and publication status

Main `{main}`. Four stages:pdflatex,bibtex,pdflatex,pdflatex. For journal set TEXINPUTS=./vendor/soul: to use included unmodified SOUL files with their original license headers. Normal TeX Live packages/fonts required. Converted logos are included;no implicit model/old-account dependency. Source,publications statements,bibliography,vector figures and new600dpi PNGs are included. The generic preprint hasno MDPI Definitions. Journal class is unchanged;wrapper labels it unsubmitted and unlicensed pending rights.

Freeze {FREEZE}. Preprint-first posting is planned,not done. Internal preprintV3 doesnot mean3 public postings. No DOI,receipt or all-author final approval exists. Read the limitations and secondary utility-audit amendment. This is a local review artifact,not permission to publish. The paper has no arbitrary page target;the full methods,catalogs,conditional argument,traces and reproduction limits are provided.
''')
        for file in (TASK/'figures').glob('*.png'):shutil.copy2(file,directory/file.name)
        files=[p for p in directory.rglob('*') if p.is_file() and p.suffix in ('.tex','.bib','.bbl','.bst','.sty','.cls','.eps','.pdf','.png','.md','.txt')]
        packages.append(archive(TASK/name,files,directory))
    for folder,name in [('journal','HETE_JOURNAL_V4_3'),('preprint','HETE_PREPRINT_V3')]:shutil.copy2(TASK/'paper'/folder/(name+'.pdf'),TASK/(name+'.pdf'))
    code=[ROOT/'AGENTS.md',ROOT/'LICENSE']+list(Path(__file__).parent.glob('*.py'))+list(Path(__file__).parent.glob('*.md'))+[ROOT/'tests/uir_security/test_scie_v4_3_boundary.py']
    code+=[TASK/'manifests'/n for n in ('V4_3_PREREGISTERED_PROTOCOL.json','ANALYSIS_PREREGISTRATION.json','COMPOSITION_CASES.json','OUTPUT_CASES.json','EXFIL_FAMILY_SPLIT.json')]
    code+=list((TASK/'source').glob('*.tex'))
    packages.append(archive(TASK/'HETE_V4_3_REPRODUCTION_CODE.zip',code,ROOT,{
        'FREEZE_ID.txt':FREEZE+'\nLocal review;release HOLD.\n','pytest.ini':'[pytest]\npythonpath = .\naddopts = --import-mode=importlib\n',
        'README_REPRODUCTION.md':'Extract into a NEW root with AGENTS.md. Use actual Python3.14.x. Run pytest tests/uir_security/test_scie_v4_3_boundary.py,then python -m projects.uir_security.evaluation.scie_v4_3.study run,then the analyze module. The runner refuses existing final records. Protocol hashes/cases are preserved. This reproduces the finite study with fresh keys,no LLM,not another held-out research sample. Full manuscript builds use their separate self-contained source ZIPs;the authoring generator additionally needs the verified V4.2 source/manuscript inputs. No private raw historical model data,keys or old account credentials are included. Public rights remain unresolved.\n'}))
    evidence=[]
    for directory in ('manifests','reports','experiments/composition','experiments/output_channel','data/statistics','source'):
        evidence.extend(p for p in (TASK/directory).rglob('*') if p.is_file() and p.stat().st_size and p.suffix in ('.json','.jsonl','.csv','.md','.tex','.patch') and p.name!='PACKAGE_MANIFEST.json')
    evidence=list(dict.fromkeys(evidence))
    packages.append(archive(TASK/'HETE_V4_3_EVIDENCE_PRIVATE.zip',evidence,TASK,{'FREEZE_ID.txt':FREEZE+'\nPRIVATE_LOCAL_REVIEW;no publication rights granted.\n'}))
    write(TASK/'manifests/PACKAGE_MANIFEST.json',packages)
    receipts=[]
    for package in packages[:3]:
        with tempfile.TemporaryDirectory(prefix='hete-v43-fresh-') as tmp:
            target=Path(tmp);safe_extract(TASK/package['path'],target)
            if 'REPRODUCTION_CODE' in package['path']:
                env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(target)
                commands=[[PYTHON,'-c','from pathlib import Path;from projects.uir_security.evaluation.scie_v4_3 import engine;assert Path(engine.__file__).resolve().is_relative_to(Path.cwd().resolve());print("Actual extracted engine",engine.__file__)'],
                    [PYTHON,'-m','pytest','tests/uir_security/test_scie_v4_3_boundary.py','-q','-p','no:cacheprovider'],
                    [PYTHON,'-m','projects.uir_security.evaluation.scie_v4_3.study','run'],[PYTHON,'-m','projects.uir_security.evaluation.scie_v4_3.analyze']]
                outputs=[]
                for command in commands:
                    r=subprocess.run(command,cwd=target,env=env,text=True,capture_output=True);outputs.append('$ '+' '.join(command)+'\n'+r.stdout+r.stderr)
                    write(TASK/'logs/fresh_source_study.txt','\n'.join(outputs))
                    if r.returncode:raise RuntimeError('Fresh source study failed')
                reproduced=load(target/'projects/uir_security/results/hete_electronics_v4_3_2026_10_23/data/statistics/SUMMARY.json');reference=load(TASK/'data/statistics/SUMMARY.json')
                # Runtime timing and random keys differ;deterministic outcomes must match.
                if not all(reproduced[k]==reference[k] for k in ('composition','output','primary','raw_rows')):raise ValueError('Reproduced study outcome mismatch')
                receipts.append({'package':package['path'],'source_tests':11,'actual_study_reproduced':True,'rows':reproduced['raw_rows'],'counts_and_exact_primary_match':True,'same_OS':True,'external_human':False})
            else:
                main='HETE_JOURNAL_V4_3.tex' if package['path'].startswith('ELECTRONICS') else 'HETE_PREPRINT_V3.tex'
                compile_one(target,main,TASK/'logs'/('fresh_'+package['path']+'.txt'))
                log=(target/Path(main).with_suffix('.log')).read_text(errors='replace')
                if any(x in log for x in ('Overfull','undefined references','undefined citations','ignored error:')):raise ValueError('Fresh TeX layout/error warning')
                receipts.append({'package':package['path'],'fresh_directory_compile':True,'same_OS':True,'external_human':False})
    write(TASK/'reports/FRESH_DELIVERY_VERIFICATION.json',receipts)
    print('local bundles4;fresh builds2;source tests11+full new finite study reproduced',flush=True)

if __name__=='__main__':main()
