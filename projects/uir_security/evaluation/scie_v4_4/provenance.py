"""Compare supplied review evidence with actual accessible bytes; no synthesis."""
import argparse
import csv
from pathlib import Path
import shutil
import zipfile

from .common import DOC, ROOT, RESULTS, TASK, V43, load, sha, write

V42 = RESULTS/'hete_electronics_v4_2_2026_10_21'
REVIEW = DOC/'204_PRIOR_SIX_ZIP_REVALIDATION_2026_11_08.json'
REQUIRED = ['HETE_V4_3_REPRODUCTION_CODE.zip','ELECTRONICS_V4_3_REVIEW_SOURCE.zip',
            'HETE_V4_3_EVIDENCE_PRIVATE.zip','reports.zip','hete_electronics_v4_3_2026_10_23.zip',
            'HETE_JOURNAL_V4_3.pdf','HETE_PREPRINT_V3.pdf']


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--archive-dir', action='append', type=Path, default=[])
    args=parser.parse_args()
    original=V43/'manifests/HANDOFF_MANIFEST.json'
    supplied=load(REVIEW)
    expected={r['filename']: (r['bytes'],r['sha256']) for r in load(original)['entries']}
    if len(expected)!=6 or sha(original)!=supplied['source_manifest_sha256']:
        raise SystemExit('Review record not bound to actual V4.3 handoff manifest')
    local=[]
    restricted=TASK/'private/handoff'
    for row in supplied['entries']:
        name=row['filename']
        if expected[name]!=(row['expected_bytes'],row['expected_sha256']):
            raise SystemExit(f'Conflicting expectation: {name}')
        candidates=[base/name for base in (restricted,V42,DOC,V43,*args.archive_dir)]
        observed=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
                  for p in dict.fromkeys(candidates) if p.is_file()]
        match=next((o for o in observed if (o['bytes'],o['sha256'])==expected[name]),None)
        if match:
            restricted.mkdir(parents=True,exist_ok=True)
            dest=restricted/name
            if not dest.exists():
                with Path(match['path']).open('rb') as source, dest.open('xb') as out:
                    shutil.copyfileobj(source,out)
            if (dest.stat().st_size,sha(dest))!=expected[name]:
                raise SystemExit(f'Restricted import mismatch: {name}')
            with zipfile.ZipFile(dest) as z:
                if z.testzip() is not None:
                    raise SystemExit(f'Invalid archive: {name}')
        local.append({'filename':name,'expected_bytes':expected[name][0],'expected_sha256':expected[name][1],
                      'local_status':'MATCH_IMPORTED' if match else ('MISMATCH' if observed else 'NOT_ACCESSIBLE'),
                      'observed':observed})
    present=sum(r['local_status']=='MATCH_IMPORTED' for r in local)
    write(TASK/'manifests/PRIOR_SIX_ZIP_REVALIDATION_2026_11_08.json',
          {'supplied_independent_record':supplied,'supplied_sha256':sha(REVIEW),'local_import_entries':local,
           'local_matches':present,'local_all_six_matched':present==6,
           'historical_v43_local_partial_preserved':True})
    frozen=[]
    for name in REQUIRED:
        p=next((base/name for base in (V43,DOC,*args.archive_dir) if (base/name).is_file()),None)
        frozen.append({'filename':name,'status':'PRESENT_HASHED' if p else 'NOT_ACCESSIBLE',
                       'path':str(p) if p else None,'sha256':sha(p) if p else None})
    old=load(V43/'DELIVERY_MANIFEST.json')
    different=[]
    for key,info in old['files'].items():
        p=ROOT/key
        if not p.is_file() or sha(p)!=info['sha256'] or p.stat().st_size!=info['bytes']:
            different.append(key)
    core_names=['experiments/composition/runs.jsonl','experiments/composition/audit_tamper_runs.jsonl',
                'experiments/output_channel/runs.jsonl','manifests/V4_3_PREREGISTERED_PROTOCOL.json',
                'manifests/UTILITY_ORACLE_AUDIT_AMENDMENT_001.json','manifests/FINAL_GO_HOLD_DECISION.json',
                'data/statistics/SUMMARY.json']
    core={str((V43/name).relative_to(ROOT)):sha(V43/name) for name in core_names}
    write(TASK/'manifests/V4_3_IMMUTABLE_INPUTS.json',
          {'requested_snapshots':frozen,'historical_manifest_sha256':sha(V43/'DELIVERY_MANIFEST.json'),
           'historical_listed':len(old['files']),'historical_differences':different,
           'core':core,'core_matches_historical':all(k in old['files'] and old['files'][k]['sha256']==v for k,v in core.items()),
           'work_order_inputs':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in DOC.iterdir()
                                if p.name in (REVIEW.name,'background.md','204_HETE_ELECTRONICS_V4_4_WORK_ORDER_2026-11-08.md',
                                              'HETE_V4_3_INDEPENDENT_REVIEW_2026-11-08.md')}})
    (TASK/'reports/ACCOUNT_MIGRATION_EVIDENCE_NOTE.md').write_text(
      f'# 계정 이관 재검증\n\n제공된 11월 8일 독립 검토 기록은 대화 업로드 6/6 일치를 보고합니다. '
      f'이 실행의 실제 로컬 반입·해시·CRC 검증은 {present}/6입니다. 두 범위를 합치지 않습니다. '
      'V4.3 시점의 로컬 PARTIAL 기록은 변경하지 않았습니다. V4.3 검토 ZIP의 현재 접근 여부와 기존 전체 manifest 차이는 V4_3_IMMUTABLE_INPUTS.json에 있습니다. '
      'background.md는 제공본이 0바이트이며 작업지시서와 독립 검토 보고서를 기준으로 진행했습니다.\n',encoding='utf-8')
    print('local originals',present,'of 6; V4.3 manifest differences',len(different),flush=True)


if __name__=='__main__':
    main()
