"""No missing-input PASS fallback; valid evidence does not authorize publication."""
from .common import *
import re
import subprocess
import zipfile
from PIL import Image

def main():
    write(TASK/'PREFLIGHT_REPORT.json',{'freeze':FREEZE,'scientific_evidence_valid':False,'status':'IN_PROGRESS_OR_INPUT_FAILURE','submission_authorized':False,'preprint_authorized':False})
    checks=[]
    def check(name,ok,detail):checks.append({'name':name,'passed':bool(ok),'detail':detail})
    proto=load(TASK/'manifests/V4_3_PREREGISTERED_PROTOCOL.json');here=Path(__file__).parent
    check('registered_engine_and_runner_unchanged',proto['engine_sha256']==sha(here/'engine.py') and proto['study_sha256']==sha(here/'study.py'),'No mediator/payload/case retuning after final outcomes')
    check('registered_cases_unchanged',proto['composition_cases_sha256']==sha(TASK/'manifests/COMPOSITION_CASES.json') and proto['output_cases_sha256']==sha(TASK/'manifests/OUTPUT_CASES.json'),'Case bytes match local pre-final registration;not externally timestamped')
    baseline=load(TASK/'manifests/BASELINE_V4_2_LOCK.json')['captured_current_input_files'];bad=[]
    for file,v in baseline.items():
        p=ROOT/file
        if not p.is_file() or sha(p)!=v['sha256']:bad.append(file)
    check('V4_2_current_inputs_preserved',bool(baseline) and not bad,{'files':len(baseline),'changed':bad,'historic_two_source_changes_separately_disclosed':True})
    supplied=load(TASK/'manifests/HANDOFF_MANIFEST.json')
    check('available_original_three_ZIPs_match',sum(r['status']=='MATCH' for r in supplied['entries'])==3 and
        all(sha(ROOT/r['actual_path'])==r['sha256'] for r in supplied['entries'] if r['status']=='MATCH'),
        '3 originalZIPs match;other3 user-confirmed deleted,not counted as matched')
    check('missing_original_archives_honest',load(TASK/'manifests/HANDOFF_RESOLUTION.json')['not_full_six_ZIP_match'],'M01 original-archive handoff PARTIAL;unpacked inputs separately locked')
    expected={'composition':('experiments/composition/runs.jsonl',704),'audit':('experiments/composition/audit_tamper_runs.jsonl',96),'output':('experiments/output_channel/runs.jsonl',512)}
    populations={}
    for name,(file,n) in expected.items():
        pop=list(rows(TASK/file));populations[name]=pop
        check(name+'_population',len(pop)==n and len({(r['case_id'],r['config']) for r in pop})==n,{'rows':len(pop),'expected':n})
    summary=load(TASK/'data/statistics/SUMMARY.json')
    for r in summary['composition']:
        pop=[x for x in populations['composition'] if x['config']==r['config']];neg=[x for x in pop if x['expected_commits']==0]
        check(r['config']+'_counts_match_raw',len(pop)==r['composition_cases'] and len(neg)==r['negative_cases'] and
              sum(x['forbidden_effect'] for x in neg)==r['forbidden_effects'] and sum(not x['spec_match'] for x in pop)==r['spec_mismatches'],
              'Validity checks consistency,not whether the algorithm wins or achieves0 errors')
    check('model_requests_accounted',summary['physical_model_requests']==0 and all(r['physical_model_calls']==0 for r in populations['composition']+populations['output']),
          'New deterministic study useszero generators;historical690 requests not recomputed as fresh')
    check('secondary_audit_amendment_visible',load(TASK/'manifests/UTILITY_ORACLE_AUDIT_AMENDMENT_001.json')['stage'].startswith('post-final'),
          'Raw release-only flags retained;corrected complete utility is secondary posthoc')
    claims=list(csv.DictReader((TASK/'reports/CLAIM_TO_EVIDENCE_V4_3.csv').open()))
    rawhashes={name:sha(TASK/name) for name in {r['raw_file'] for r in claims}}
    check('claim_map_complete',len(claims)==sum(len(v) for v in populations.values()) and
          all(rawhashes[r['raw_file']]==r['raw_file_sha256'] for r in claims),{'claim_rows':len(claims)})
    manuscript=load(TASK/'manifests/MANUSCRIPT_SOURCE_MAP.json');shared=[]
    for folder,main in [('journal','HETE_JOURNAL_V4_3.tex'),('preprint','HETE_PREPRINT_V3.tex')]:
        directory=TASK/'paper'/folder;wrapper=(directory/main).read_text();body=(directory/'manuscript_body_v4_3.tex').read_text();back=(directory/'publication_statements.tex').read_text()
        abstract=(re.search(r'\\abstract\{(.*?)\}\\keyword',wrapper,re.S).group(1) if folder=='journal' else re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',wrapper,re.S).group(1))
        check(folder+'_real_abstract',170<=len(abstract.split())<=200 and len(abstract.split())==manuscript['abstract_words'],'Read actual required source;no fallback if metadata missing')
        check(folder+'_freeze_and_status',FREEZE in wrapper and 'not submitted' in wrapper.lower() if folder=='journal' else FREEZE in wrapper and 'not posted' in wrapper.lower(),'Internal draft/unposted status preserved')
        for name in ('manuscript_body_v4_3.tex','extended_methods.tex','v4_3_results.tex','appendices_v4_3.tex','publication_statements.tex'):
            if folder=='journal':shared.append((name,sha(directory/name)))
            else:check('shared_'+name,sha(directory/name)==dict(shared)[name],'Identical scientific content across wrappers')
        check(folder+'_required_sections',all(s in body for s in ('Introduction','Materials and Methods','Results','Discussion','Conclusions')) and
              all(s in back for s in ('Funding','Author contributions','Data and code availability','Conflicts of interest','GenAI assistance')),'Required sections contain honest pending ethical declarations')
        author=load(BASE/'manifests/AUTHOR_METADATA.json');funding=author['funding_verbatim'].replace('&',r'\&')
        check(folder+'_author_and_funding',all(a['name'] in wrapper and a['email'] in wrapper and a['orcid'] in wrapper for a in author['authors']) and funding in back,
              'User-directed identities/correspondence/exact acknowledgment;not final HETE approval')
        log=(directory/Path(main).with_suffix('.log')).read_text(errors='replace')
        warnings=[s for s in ('Overfull','undefined references','undefined citations','ignored error:','! LaTeX Error') if s in log]
        check(folder+'_clean_final_TeX',not warnings,warnings)
        pdf=directory/Path(main).with_suffix('.pdf');info=subprocess.check_output(['pdfinfo',str(pdf)],text=True);pages=int(re.search(r'Pages:\s+(\d+)',info).group(1))
        check(folder+'_PDF_real',pdf.stat().st_size>10000 and pdf.read_bytes().startswith(b'%PDF'),{'pages':pages,'bytes':pdf.stat().st_size})
        bbl=(directory/Path(main).with_suffix('.bbl')).read_text();bibkeys=re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}',bbl)
        cited=[]
        for group in re.findall(r'\\cite\{([^}]+)\}',body):
            for key in group.split(','):
                if key not in cited:cited.append(key)
        check(folder+'_numbered_references',cited==bibkeys and len(cited)>0,{'first_citation_items':len(cited),'bibliography_items':len(bibkeys)})
    figure_files=list((TASK/'figures').glob('*.png'))
    check('new_figure_inventory_nonempty',len(figure_files)==2,'Two new600dpi panels plus historical imported vector figures;empty scans fail')
    for png in figure_files:
        with Image.open(png) as im:dpi=im.info.get('dpi',(0,0))
        check('figure_'+png.stem,all(x>=599 for x in dpi) and png.with_suffix('.pdf').is_file(),{'dpi':dpi,'vector_pdf':True,'editable_source':'paper.py'})
    for p in load(TASK/'manifests/PACKAGE_MANIFEST.json'):
        path=TASK/p['path']
        with zipfile.ZipFile(path) as z:
            names=z.namelist();okay=z.testzip() is None and len(names)==len(set(names)) and all(i.file_size>0 for i in z.infolist())
            okay &= FREEZE in z.read('FREEZE_ID.txt').decode() and all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
            if 'PREPRINT' in path.name:okay &= not any('Definitions/' in n for n in names)
            if 'ELECTRONICS' in path.name:okay &= path.stat().st_size<=120_000_000 and 'Definitions/mdpi.cls' in names
        check('archive_'+path.stem,okay and sha(path)==p['sha256'],{'bytes':path.stat().st_size,'members':len(names),'CRC':'PASS' if okay else 'FAIL'})
    receipts=load(TASK/'reports/FRESH_DELIVERY_VERIFICATION.json')
    with zipfile.ZipFile(TASK/'HETE_V4_3_REPRODUCTION_CODE.zip') as z:
        stale=[p.name for p in here.glob('*.py') if str(p.relative_to(ROOT)) not in z.namelist() or z.read(str(p.relative_to(ROOT)))!=p.read_bytes()]
    check('source_bundle_matches_current_code',not stale,stale)
    check('fresh_source_and_manuscripts',len(receipts)==3 and all(r.get('fresh_directory_compile') or r.get('actual_study_reproduced') for r in receipts),receipts)
    check('regression_tests','181 passed' in (TASK/'logs/security_regression.txt').read_text(),'181 root security tests executed,not merely reported from old30')
    visual=load(TASK/'reports/VISUAL_REVIEW.json')
    expected_pdfs={'paper/journal/HETE_JOURNAL_V4_3.pdf','paper/preprint/HETE_PREPRINT_V3.pdf'}
    check('all_page_visual_self_review',len(visual['documents'])==2 and {r['pdf'] for r in visual['documents']}==expected_pdfs and all(r['pages']>0 and r['reviewed_pages']==list(range(1,r['pages']+1)) and sha(TASK/r['pdf'])==r['pdf_sha256'] for r in visual['documents']),
          'Implementing agent self-review;external human language/visual review remains NOT RUN')
    decision=load(TASK/'manifests/FINAL_GO_HOLD_DECISION.json')
    check('publication_authorization_not_fabricated',not any(decision[k] for k in ('submission_authorized','preprint_authorized','submitted','preprint_posted','public_release','human_validation')),
          'Scientific validity and G3/G4 authority are separate')
    passed=all(r['passed'] for r in checks)
    result={'freeze':FREEZE,'scientific_evidence_valid':passed,'technical_checks_passed':sum(r['passed'] for r in checks),'technical_checks_total':len(checks),
        'submission_authorized':False,'preprint_authorized':False,'original_six_ZIP_identity_complete':False,'handoff_archive_scope':'3MATCH+3user-confirmed deleted originals',
        'decision':'HOLD','checks':checks,'limitations':['No typed-specific security/audit benefit observed','Constructed finite programs and repeated templates',
        'Secondary complete-utility correction posthoc','Arbitrary benign prose still denied','No human/second-OS/production validation','Author/rights/APC/IRB/reviewer/version signoff unresolved']}
    write(TASK/'PREFLIGHT_REPORT.json',result);print('technical/scoped evidence',sum(r['passed'] for r in checks),'/',len(checks),'PASS' if passed else 'FAIL','publication HOLD')
    for r in checks:
        if not r['passed']:print('FAIL',r['name'],str(r['detail'])[:500])
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
