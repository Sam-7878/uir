"""Offline scope-aware evidence verification; no inference and no old writes."""
import csv
import json
from pathlib import Path

from .common import FROZEN, TASK, load, rows, sha, write


def main():
    failures=[];items=[]
    for item in load(FROZEN/'ARTIFACT_MANIFEST.json')['artifacts']:
        if item['path'].endswith('.pyc'):continue
        original=FROZEN/item['path'];overlay=TASK/'resources/recovered_v32_overlay'/item['path']
        selected=overlay if overlay.is_file() else original
        ok=selected.is_file() and selected.stat().st_size==item['size'] and sha(selected)==item['sha256']
        items.append({'recorded_path':item['path'],'selected_path':str(selected.relative_to(TASK)) if selected==overlay
                      else 'frozen/'+item['path'],'sha256':item['sha256'],'verified':ok})
        if not ok:failures.append('science hash:'+item['path'])
    if len(items)!=418:failures.append('non-bytecode population differs')
    with (TASK/'data/TABLE_RECONCILIATION.csv').open() as f:
        comparisons=list(csv.DictReader(f))
    if not comparisons or any(r['matched']!='True' for r in comparisons):failures.append('summary mismatch')
    sanitized=load(TASK/'manifests/sanitized_evidence_audit.json')
    if not sanitized['passed'] or sanitized['records']!=19900:failures.append('projected score replay')
    candidate=TASK/'resources/publication_candidate_local/per_case_records.jsonl'
    if sha(candidate)!=sanitized['payload_sha256']:failures.append('projected payload changed')
    external=list(rows(TASK/'data/benchmark_results.jsonl'))
    if len(external)!=48 or len({r['run_id'] for r in external})!=48:failures.append('external trial completeness')
    if any(r['backend_failure'] for r in external):failures.append('external backend failures')
    ai=load(TASK/'data/ai_judge_agreement.json')
    if not ai['completed'] or ai['human_validation'] or any(ai['missing'].values()):failures.append('AI annotation scope')
    bibliography=(TASK/'resources/references_clean.bib').read_text()
    import re
    keys=re.findall(r'@\w+\{([^,]+)',bibliography)
    if len(keys)!=25 or len(keys)!=len(set(keys)):failures.append('bibliography keys')
    build=load(TASK/'manifests/manuscript_build_audit.json')
    if len(build)!=2 or not all(r['passed'] for r in build):failures.append('manuscript build')
    for r in build:
        if sha(TASK/'manuscript_private'/(r['stem']+'.pdf'))!=r['pdf_sha256']:failures.append('PDF changed:'+r['stem'])
    for name in ('HETE_PREPRINT_V1','HETE_JOURNAL.mdpi'):
        source=TASK/'manuscript_private'/(name+'.tex')
        if not source.is_file():failures.append('missing source:'+name)
    report={'passed':not failures,'failures':failures,'non_bytecode_science_entries':len(items),
        'table_comparisons':len(comparisons),'projected_scored_records':19900,'external_trials':len(external),
        'AI_annotations':500,'human_validation':False,'original_full_manifest_pass':False,
        'original_source_mismatches':13,'exact_source_overlay_recovered':13,'unrecovered_bytecode':54,
        'publication_authorized':False,'scope':'offline scientific-byte/aggregate/build checks; no external human certification',
        'science_entries':items}
    write(TASK/'manifests/SCOPED_RELEASE_VERIFICATION.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='science_entries'}))
    return int(bool(failures))


if __name__=='__main__':raise SystemExit(main())
