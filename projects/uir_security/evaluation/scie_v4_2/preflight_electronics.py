"""Evidence/build integrity PASS and actual publication approval HOLD are separate."""
from .common import *
from .closure_reports import FREEZE_ID
from .paper import ABSTRACT,KEYWORDS
from collections import Counter
import re
import subprocess
import zipfile
from PIL import Image


def main():
    checks=[]
    def check(name,passed,detail):checks.append({'check':name,'passed':bool(passed),'detail':detail})
    baseline=load(TASK/'manifests/BASELINE_LOCK.json')['files'];repair=load(TASK/'manifests/V4_1_LOCK.json')
    mismatches=[p for p,h in {**baseline,**repair}.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    check('historical_frozen_files',not mismatches,{'locked_files':len(set(baseline)|set(repair)),'mismatches':mismatches})
    external=list(rows(TASK/'experiments/agentdojo_external/attack_trace.jsonl'))
    check('external_population',len(external)==432 and len({r['run_id'] for r in external})==432,
          {'rows':len(external),'unique_run_ids':len({r['run_id'] for r in external}),'not_independent_physical_calls':True})
    check('external_tasks_domains',len({(r['domain'],r['task_id']) for r in external})==12 and len({r['domain'] for r in external})==3,
          '12 unique tasks;3 official domains;9 delegated-write tasks per backbone/configuration')
    ledger=list(csv.DictReader((TASK/'data/outcome_ledger.csv').open()))
    check('missing_not_counted_blocked',sum(r['attack_success'] is None for r in external if r['attack'])==6 and
          all(r['attack_success'] is None for r in external if r['backend_failure']),
          '2 retained physical incomplete responses propagated to6 logical unknowns;scored58/planned60 per Ministral config')
    check('exposure_ledger_complete',len(ledger)==432 and sum(1 for _ in csv.DictReader((TASK/'data/EXPOSURE_DETECTOR_CORRECTIONS.csv').open()))==3,
          'Recorded generator inputs independently inspected;3 original raw flags corrected offline and preserved')
    costs=load(TASK/'data/statistics/PHYSICAL_MODEL_COST.json')
    check('physical_request_count',sum(v['calls'] for v in costs.values())==690,costs)
    compact=load(TASK/'data/EXTERNAL_COMPACT.json')
    expected={'ministral-3:14b':(7,58,2),'qwen3:4b-instruct-2507-q4_K_M':(4,60,0)}
    checks_ok=True
    for model,(utility,scored,unknown) in expected.items():
        for config in ('C1_minimal','C2_typed'):
            r=next(v for v in compact if v['model']==model and v['config']==config)
            checks_ok &= (r['benign_utility'],r['official_attack_success'],r['attack_scored_n'],r['unknown_security_outcomes'])==(utility,0,scored,unknown)
    check('guard_counts_and_incremental_null',checks_ok,'Qwen4/12,0/60;Ministral7/12,0/58+2unknown;minimal=typed')
    legacy=load(TASK/'data/statistics/LEGACY_RECOUNT.json');portable=load(TASK/'data/statistics/PORTABLE_RECOUNT.json')
    check('portable_independent_recount',legacy['records']==portable['records']==19900 and
          all(legacy[k]==portable[k] for k in ('counts','exact_tests','adaptive')),'Python -I -S stdlib recount matches independently written aggregate/exact/Holm results;projection only')
    for file,n,field in [('experiments/multimodel_utility/bilingual_runs.jsonl',64,'run_id'),
                         ('experiments/official_baseline/OFFICIAL_AGENT_CASE_TRACE_003.jsonl',6,'run_id'),
                         ('experiments/typed_semantics/BOUNDED_MODEL_TRACE.jsonl',192,None)]:
        pop=list(rows(TASK/file));okay=len(pop)==n and (not field or len({r[field] for r in pop})==n)
        check('population_'+Path(file).stem,okay,{'rows':len(pop),'expected':n})
    bounded=load(TASK/'manifests/BOUNDED_MODEL_RESULT.json')
    check('bounded_model_no_universal_claim',bounded['passed'] and not bounded['failures'] and
          all(r['matched'] for r in rows(TASK/'experiments/typed_semantics/BOUNDED_MODEL_TRACE.jsonl')),
          '96 states x2 systems;finite coverage only')
    contract=list(csv.DictReader((TASK/'experiments/model_substitution/CANONICAL_CONTRACT_AUDIT.csv').open()))
    check('encoded_negative_and_utility_cost',[(int(r['attack_releases']),int(r['legitimate_prose_denied'])) for r in contract]==[(72,0),(0,12),(0,12)],
          'Original actual pipeline72/96;unchanged installed V4.1 and new canonical0/96;both reject12/12 legitimate prose')
    source=Path(__file__).parent
    hash_rules=[('AGENTDOJO_V4_2_PROTOCOL_002.json','runner_sha256','external.py'),
        ('AGENTDOJO_V4_2_PROTOCOL_002.json','engine_sha256','typed_engine.py'),
        ('TYPED_EFFECT_PROTOCOL.json','script_sha256','mechanism.py'),
        ('RED_TEAM_PROTOCOL.json','source_sha256','mechanism.py'),
        ('BOUNDED_MODEL_PROTOCOL.json','source_sha256','schema_spec.py'),
        ('POLICY_TIMING_PROTOCOL.json','source_sha256','performance.py'),
        ('BILINGUAL_UTILITY_PROTOCOL.json','source_sha256','bilingual.py'),
        ('OFFICIAL_BASELINE_PROTOCOL_003.json','source_sha256','official_baseline_v003.py')]
    bad=[f'{p}:{key}' for p,key,file in hash_rules if load(TASK/'manifests'/p)[key]!=sha(source/file)]
    check('experiment_code_unchanged_from_protocol',not bad,bad)
    oracle=load(TASK/'manifests/AGENTDOJO_V4_2_PROTOCOL_002.json')['oracle_sources']
    check('official_oracle_sources_unchanged',all(sha(OLD/'resources/agentdojo'/p)==h for p,h in oracle.items()),
          {'pinned_oracle_source_files':len(oracle),'rewritten_oracles':False})
    mapping=load(TASK/'manifests/NEW_EVIDENCE_MAP.json')
    check('new_case_claim_linkage',sha(TASK/mapping['path'])==mapping['sha256'] and mapping['source_populations']==6 and mapping['rows']>1000,
          {'rows':mapping['rows'],'case_record_and_protocol_hashes':True,'cache_request_digests':True})
    check('abstract_keywords',170<=len(ABSTRACT.split())<=195 and 3<=len(KEYWORDS.split(';'))<=10,
          {'abstract_words':len(ABSTRACT.split()),'keywords':len(KEYWORDS.split(';'))})
    bodies=[]
    author=load(TASK/'manifests/AUTHOR_METADATA.json')
    for folder,main in [('manuscript_preprint','HETE_PREPRINT_V2.tex'),('manuscript_electronics','HETE_JOURNAL_V4_2.mdpi.tex')]:
        directory=TASK/folder;wrapper=(directory/main).read_text();body=(directory/'manuscript_body_v4_2.tex').read_text()
        back=(directory/'publication_statements.tex').read_text();bodies.append(body)
        log=(directory/Path(main).with_suffix('.log')).read_text(errors='replace')
        bad=[word for word in ('Overfull','undefined references','undefined citations','Citation `','Reference `','! LaTeX Error') if word in log]
        check(folder+'_final_log_clean',not bad,bad)
        check(folder+'_required_sections',all(name in body for name in ('Introduction','Materials and Methods','Results','Discussion','Conclusions')) and
              all(name in back for name in ('Author contributions','Funding','Institutional review and consent','Data and code availability','GenAI assistance','Conflicts of interest')),
              'Methods/Results plus required declaration drafts;ethical confirmation remains HOLD')
        check(folder+'_metadata',FREEZE_ID in wrapper and all(a['name'] in wrapper and a['email'] in wrapper and a['orcid'] in wrapper for a in author['authors']),
              'User-directed author/contact/ORCID;corresponding Kim;freeze ID;not inferred author approval')
        funding=author['funding_verbatim'].replace('&',r'\&')
        check(folder+'_funding_verbatim',funding in back,'User-provided acknowledgment preserved,including supplied spelling;TeX & escaped only')
        # Numeric bibliography order follows first occurrence of each citation key.
        cited=[]
        for group in re.findall(r'\\cite\{([^}]+)\}',body):
            for key in group.split(','):
                if key not in cited:cited.append(key)
        bibliography=(directory/Path(main).with_suffix('.bbl')).read_text()
        bibkeys=re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}',bibliography)
        check(folder+'_reference_order',cited==bibkeys,{'unique_first_citations':len(cited),'bibliography_items':len(bibkeys),'numbered_first_use':cited==bibkeys})
        pdf=directory/Path(main).with_suffix('.pdf');info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
        pages=int(re.search(r'Pages:\s+(\d+)',info).group(1))
        check(folder+'_compiled_pdf',pdf.stat().st_size>10000 and pdf.read_bytes().startswith(b'%PDF') and pages>=1,{'bytes':pdf.stat().st_size,'pages':pages})
    check('same_scientific_body',bodies[0]==bodies[1],'Distinct wrappers/templates;identical included evidence body and separate unposted statuses')
    for file in (TASK/'figures').glob('*.png'):
        with Image.open(file) as im:dpi=im.info.get('dpi',(0,0));size=im.size
        check('figure_'+file.stem,all(d>=599 for d in dpi) and (file.with_suffix('.pdf')).read_bytes().startswith(b'%PDF'),{'pixels':size,'dpi':dpi,'editable_generator':'paper.py','vector_pdf':True})
    packages=load(TASK/'manifests/PACKAGE_MANIFEST.json')
    for package in packages:
        file=TASK/package['path']
        with zipfile.ZipFile(file) as z:
            names=z.namelist();zero=[i.filename for i in z.infolist() if i.file_size==0];bad=z.testzip()
            freeze=z.read('FREEZE_ID.txt').decode()
            safe=all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
            okay=not zero and not bad and len(names)==len(set(names)) and safe and FREEZE_ID in freeze and sha(file)==package['sha256']
            if file.name=='ELECTRONICS_SUBMISSION_READY.zip':okay &= file.stat().st_size<=120_000_000 and 'Definitions/mdpi.cls' in names and 'HETE_JOURNAL_V4_2.mdpi.pdf' in names
            if file.name=='HETE_PREPRINT_V2.zip':okay &= not any('Definitions/' in n for n in names)
        check('zip_'+file.stem,okay,{'bytes':file.stat().st_size,'members':len(names),'zero_files':zero,'CRC_bad':bad,'safe_paths':safe})
    fresh=load(TASK/'reports/FRESH_DIRECTORY_VERIFICATION.json')
    with zipfile.ZipFile(TASK/'HETE_V4_2_REPRODUCTION_CODE.zip') as z:
        stale=[]
        for file in source.glob('*.py'):
            name=str(file.relative_to(ROOT))
            if name not in z.namelist() or z.read(name)!=file.read_bytes():stale.append(name)
    check('packaged_current_source_bytes',not stale,stale)
    check('fresh_directory_build_and_source_tests',len(fresh)==3 and all(v.get('fresh_directory_compile') or v.get('passed') for v in fresh),fresh)
    text=subprocess.check_output(['pdftotext','-f','1','-l','1',str(TASK/'HETE_JOURNAL_V4_2_FINAL.pdf'),'-'],text=True)
    check('no_false_submission_or_license_banner','Submitted to' not in text and 'Local review draft' in text and 'Not submitted or published' in text,
          'Official class preserved;wrapper overrides default submitted/copyright license boilerplate for honest local status')
    visual=load(TASK/'reports/VISUAL_REVIEW.json')
    check('all_page_visual_review',all(visual[k]['reviewed_pages']==list(range(1,visual[k]['pages']+1)) for k in ('journal','preprint')) and
          all(visual[k]['pdf_sha256']==sha(TASK/visual[k]['pdf']) for k in ('journal','preprint')),
          'Agent visual inspection of all-page contact sheets and first/fourth/final page layouts;not author approval')
    tests=(TASK/'logs/security_tests_final.log').read_text()
    check('security_regression_tests','170 passed' in tests,'170 tests;new typed22 and effect/exposure8 plus prior140')
    decision=load(TASK/'SUBMISSION_DECISION.json')
    check('honest_release_hold',decision['decision']=='HOLD' and not decision['author_all_approval'] and not decision['human_validation'] and not decision['submitted'] and not decision['public_release_performed'],
          'Technical checks never substitute for missing author/rights/publication approvals')
    passed=all(c['passed'] for c in checks)
    report={'freeze_id':FREEZE_ID,'automated_technical_pass':passed,'checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks),
        'submission_authorized':False,'decision':'HOLD','checks':checks,
        'unresolved_release_gates':['HETE-specific all-author declarations/version approval','institutional data/code/output rights and human privacy audit',
            'sponsor role/APC/IRB/access wording','no simultaneous journal submission confirmation','reviewer conflicts and signed scientific-risk decision'],
        'scope':'Technical evidence/packaging review only;no publication,no human validation,no independent OS replication'}
    write(TASK/'PREFLIGHT_REPORT.json',report)
    write(TASK/'reports/MDPI_COMPLIANCE_REPORT.md',f'''# Technical draft compliance

Freeze {FREEZE_ID}. Automated technical checks: {sum(c['passed'] for c in checks)}/{len(checks)}. {'PASS' if passed else 'FAIL'}. Submission authorization: **HOLD**. Full machine result: PREFLIGHT_REPORT.json.

Abstract177 words;6 keywords;actual technical Methods;numbered references in first-citation order;two vector/600dpi figures;nonzero journal/preprint PDF;safe ZIP CRC/hash/size/source presence;fresh-directory source builds and extracted-source30 tests. Root security regression170 tests passed. All-page visual inspection is by the implementing agent, not independent editorial/author approval. Source template restrictions separate generic preprint from journal. The earlier corrupted template is not consumed.

Author contacts and funding are user-directed. HETE-specific declarations/rights/APC/IRB/access and final all-author approval remain unresolved in the draft, rather than being silently removed or replaced with an untrue approved assertion. Required cover-letter sentences are conditional draft text. Ethics/release gates G3/G4 have not passed. READY/FINAL filenames mean assembled local review artifacts only. This package must not be submitted/posted until signed final decisions and all substantive declarations are resolved.
''')
    print('technical checks',sum(c['passed'] for c in checks),'/',len(checks),'PASS' if passed else 'FAIL','release HOLD')
    for c in checks:
        if not c['passed']:print('FAILED',c['check'],str(c['detail'])[:500])
    if not passed:raise SystemExit(1)


if __name__=='__main__':main()
