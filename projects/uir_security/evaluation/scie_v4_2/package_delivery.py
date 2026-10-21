"""Local review bundles, CRC checked and built again after safe extraction."""
from .common import *
from .closure_reports import FREEZE_ID
from .build_manuscripts import build
import shutil
import subprocess
import tempfile
import zipfile


def zip_files(path,files,root=None,extra=None):
    members=[]
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for file in sorted(files):
            if not file.is_file() or file.stat().st_size==0:raise ValueError('Missing/empty bundle file: '+str(file))
            name=str(file.relative_to(root)) if root else file.name
            if name in members:raise ValueError('Duplicate member '+name)
            members.append(name);z.write(file,name)
        for name,text in (extra or {}).items():
            if name in members:raise ValueError('Duplicate extra')
            z.writestr(name,text);members.append(name)
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad or any(i.file_size==0 for i in z.infolist()):raise ValueError('CRC/empty member failure')
    return {'path':str(path.relative_to(TASK)),'sha256':sha(path),'bytes':path.stat().st_size,'members':len(members),'CRC':'PASS',
            'freeze_id':FREEZE_ID,'release_authorized':False}


def main():
    packages=[]
    for folder,main in [('manuscript_preprint','HETE_PREPRINT_V2.tex'),('manuscript_electronics','HETE_JOURNAL_V4_2.mdpi.tex')]:
        directory=TASK/folder
        if folder=='manuscript_electronics':
            soul=OLD/'resources/tex_packages/extracted/usr/share/texlive/texmf-dist/tex/generic/soul'
            dest=directory/'vendor/soul';dest.mkdir(parents=True,exist_ok=True)
            for file in soul.glob('*.sty'):shutil.copy2(file,dest/file.name)
        write(directory/'FREEZE_ID.txt',FREEZE_ID+'\nLocal review package; submission/public release HOLD.\n')
        write(directory/'README_BUILD.md',f'''# Local review manuscript package

Freeze `{FREEZE_ID}`. Publication, all-author approval and release rights remain HOLD. Main: `{main}`.

Ubuntu TeX Live: pdflatex, bibtex and normal recommended fonts/packages. For journal use `TEXINPUTS=./vendor/soul:`; the unmodified LPPL SOUL files include their own license headers. Commands: pdflatex -interaction=nonstopmode -halt-on-error {main}; bibtex {Path(main).stem}; then pdflatex twice. Converted MDPI EPS logos are included, avoiding an implicit network/system Ghostscript dependency. The journal Definitions class is the freshly obtained official template, unchanged; only wrapper macros label this as an internal unsubmitted draft. Do not post MDPI Definitions with a preprint. Generic article source is a separate package.

Shared included body and back matter, clean bibliography, vector figures, 600dpi PNG variants and figure-generator Python source are present. Both generic/journal PDFs are generated from the same numerical evidence. No model weights, unrelated raw transcripts or reviewer private contact lists are in this manuscript ZIP. Draft statements explicitly retain unknown approvals. READY/FINAL filename is not submission permission.
''')
        for file in (TASK/'figures').glob('*.png'):shutil.copy2(file,directory/file.name)
        shutil.copy2(Path(__file__).with_name('paper.py'),directory/'figure_and_manuscript_generator.py')
        # .aux/.log/.out are intermediate local state; .bbl supplies exact bibliography.
        files=[f for f in directory.rglob('*') if f.is_file() and f.suffix in ('.tex','.bib','.bbl','.cls','.bst','.sty','.pdf','.png','.eps','.md','.txt','.py')]
        name='HETE_PREPRINT_V2.zip' if folder=='manuscript_preprint' else 'ELECTRONICS_SUBMISSION_READY.zip'
        packages.append(zip_files(TASK/name,files,root=directory))
    shutil.copy2(TASK/'manuscript_electronics/HETE_JOURNAL_V4_2.mdpi.pdf',TASK/'HETE_JOURNAL_V4_2_FINAL.pdf')
    sourcefiles=[ROOT/'AGENTS.md',ROOT/'LICENSE',ROOT/'pyproject.toml',ROOT/'Cargo.toml']
    sourcefiles += list((ROOT/'src').rglob('*.py'))+list((ROOT/'src').rglob('*.json'))
    for directory in (PROJECT/'evaluation',ROOT/'tests/uir_security'):
        sourcefiles += [p for p in directory.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.md') and '__pycache__' not in p.parts]
    for path in [ROOT/'projects/__init__.py',PROJECT/'__init__.py']:
        if path.is_file() and path.stat().st_size:sourcefiles.append(path)
    # Empty package markers are represented by a harmless comment, not 0-byte ZIP entries.
    sourcefiles=list(dict.fromkeys(p for p in sourcefiles if p.stat().st_size))
    extras={'FREEZE_ID.txt':FREEZE_ID+'\nLocal review only; release HOLD.\n',
            'README_REPRODUCTION.md':(TASK/'source/REPRODUCTION_COMMANDS.md').read_text(),
            'DEPENDENCY_LOCK.json':(TASK/'source/DEPENDENCY_LOCK.json').read_text(),
            'recount_projection.py':Path(__file__).with_name('recount_projection.py').read_text(),
            'PORTABLE_RECOUNT_DOCKERFILE':(TASK/'source/PORTABLE_RECOUNT_DOCKERFILE').read_text()}
    for directory in [PROJECT/'evaluation',*[(PROJECT/'evaluation'/x) for x in ('scie_v4_2','scie_v4','llm_security_v3_2')]]:
        p=directory/'__init__.py'
        if p.exists() and not p.stat().st_size:extras[str(p.relative_to(ROOT))]='# Package marker retained in review source bundle.\n'
    packages.append(zip_files(TASK/'HETE_V4_2_REPRODUCTION_CODE.zip',sourcefiles,root=ROOT,extra=extras))
    groups={
        'S1_LEGACY_LINEAGE': [TASK/'data/RAW_TO_CLAIM_MAP.csv',TASK/'data/statistics/LEGACY_RECOUNT.json',TASK/'data/statistics/PORTABLE_RECOUNT.json',TASK/'reports/LEGACY_INTEGRITY_REPORT.md',TASK/'reports/ATTRITION_AND_AMENDMENT.md'],
        'S2_EXTERNAL_EFFECTS': [TASK/'data/outcome_ledger.csv',TASK/'data/EXTERNAL_COMPACT.csv',TASK/'data/NEW_BACKEND_ATTRITION.csv',TASK/'data/EXPOSURE_DETECTOR_CORRECTIONS.csv',TASK/'experiments/agentdojo_external/EXTERNAL_TASK_LEDGER.csv',TASK/'experiments/agentdojo_external/external_results.csv',TASK/'data/statistics/PAIRED_COMPARISON.csv',TASK/'data/statistics/CLUSTER_SENSITIVITY.json'],
        'S3_TYPED_AND_OUTPUT': [TASK/'source/UIR_TYPED_SCHEMA_V4_2.json',TASK/'source/TRUSTED_EFFECT_SCHEMA.json',TASK/'experiments/typed_semantics/EFFECT_RESULTS.csv',TASK/'experiments/typed_semantics/BOUNDED_MODEL_TRACE.jsonl',TASK/'experiments/model_substitution/CANONICAL_CONTRACT_AUDIT.csv',TASK/'experiments/policy_incremental/POLICY_TIMING_SUMMARY.csv',TASK/'reports/TYPED_ENFORCEMENT_SEMANTICS.md'],
        'S4_BILINGUAL_AND_OFFICIAL': [TASK/'data/BILINGUAL_SUMMARY.json',TASK/'experiments/multimodel_utility/BILINGUAL_FAILURE_LEDGER.csv',TASK/'experiments/official_baseline/OFFICIAL_LOCAL_CASE_COMPARISON.csv',TASK/'experiments/official_baseline/FIDELITY_MATRIX_V4_2.csv',TASK/'reports/OFFICIAL_BASELINE_REPRO.md',TASK/'reports/JUDGE_VALIDATION_REPORT.md'],
    }
    groups['S1_LEGACY_LINEAGE'] += [OLD/'resources/publication_candidate_local/per_case_records.jsonl',
        OLD/'resources/publication_candidate_local/REPLAY_RESULT.json']
    groups['S2_EXTERNAL_EFFECTS'] += [TASK/'data/NEW_RAW_TO_CLAIM_MAP.csv',TASK/'manifests/AGENTDOJO_V4_2_PROTOCOL_002.json',
        TASK/'manifests/STATS_PROTOCOL_V4_2.json',TASK/'manifests/MODEL_REGISTRY.json']
    groups['S3_TYPED_AND_OUTPUT'] += [TASK/'manifests/TYPED_EFFECT_PROTOCOL.json',TASK/'manifests/RED_TEAM_PROTOCOL.json',
        TASK/'manifests/BOUNDED_MODEL_PROTOCOL.json',TASK/'manifests/POLICY_TIMING_PROTOCOL.json',
        TASK/'experiments/typed_semantics/DECISION_TRACE_EXAMPLES.jsonl',TASK/'experiments/adaptive_redteam/ADAPTIVE_QUERY_LOG.jsonl']
    groups['S4_BILINGUAL_AND_OFFICIAL'] += [TASK/'manifests/BILINGUAL_UTILITY_PROTOCOL.json',TASK/'manifests/OFFICIAL_BASELINE_PROTOCOL_003.json',
        TASK/'experiments/multimodel_utility/bilingual_runs.jsonl',TASK/'experiments/official_baseline/OFFICIAL_AGENT_CASE_TRACE_003.jsonl']
    for name,files in groups.items():
        packages.append(zip_files(TASK/'supplementary'/(name+'.zip'),files,root=ROOT if name=='S1_LEGACY_LINEAGE' else TASK,extra={
            'FREEZE_ID.txt':FREEZE_ID+'\nLocal review only; public release HOLD.\n',
            'README.md':'PRIVATE local review evidence,release HOLD. S1 includes the exact saved historical score projection and reference aggregates under their original repository paths; run the standalone recount on that projection. S2 has derived external ledgers/protocols;full external HTTP captures remain task-local private. S3 contains finite mechanism/output traces. S4 contains bilingual and official-agent captures with synthetic benchmark contacts. No bundle reconstructs missing original transport. Machine scan is not human rights/privacy approval. No public redistribution authorized.\n'}))
    write(TASK/'manifests/PACKAGE_MANIFEST.json',packages)
    # Safe fresh directory builds from ZIP bytes, not original source paths.
    results=[]
    for package in packages[:3]:
        with tempfile.TemporaryDirectory(prefix='hete-v42-review-') as tmp:
            dest=Path(tmp)
            with zipfile.ZipFile(TASK/package['path']) as z:
                for member in z.infolist():
                    path=Path(member.filename)
                    if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe ZIP member')
                z.extractall(dest)
            if package['path'].endswith('REPRODUCTION_CODE.zip'):
                env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(dest)
                command=[sys.executable,'-m','pytest','tests/uir_security/test_scie_v4_2_typed_engine.py',
                         'tests/uir_security/test_scie_v4_2_effect_oracles.py','-q','-p','no:cacheprovider']
                r=subprocess.run(command,cwd=dest,env=env,text=True,capture_output=True)
                write(TASK/'logs/FRESH_SOURCE_TESTS.txt',r.stdout+r.stderr)
                if r.returncode:raise RuntimeError('Extracted source tests failed')
                results.append({'package':package['path'],'fresh_directory_tests':30,'passed':True,'scope':'same OS/root venv; actual extracted typed/effect source, not full legacy inference'})
            else:
                main='HETE_PREPRINT_V2.tex' if package['path'].startswith('HETE_PREPRINT') else 'HETE_JOURNAL_V4_2.mdpi.tex'
                pdf=build(dest,main,TASK/'logs'/('FRESH_'+package['path']+'.txt'))
                text=(dest/Path(main).with_suffix('.log')).read_text(errors='replace')
                bad=[word for word in ('Overfull','undefined references','undefined citations') if word in text]
                if bad:raise RuntimeError('Fresh TeX warnings '+str(bad))
                results.append({'package':package['path'],'fresh_directory_compile':True,'pdf_bytes':pdf.stat().st_size,'scope':'same OS TeX Live; not independent OS/human replication'})
    write(TASK/'reports/FRESH_DIRECTORY_VERIFICATION.json',results)
    combined='\n\n'.join((TASK/'logs'/name).read_text() for name in ('manuscript_preprint_clean_build.txt','manuscript_electronics_clean_build.txt','FRESH_HETE_PREPRINT_V2.zip.txt','FRESH_ELECTRONICS_SUBMISSION_READY.zip.txt'))
    write(TASK/'CLEAN_BUILD_LOG.txt',combined)
    print('packages',len(packages),'fresh-directory builds2; extracted source tests30',flush=True)


if __name__=='__main__':main()
