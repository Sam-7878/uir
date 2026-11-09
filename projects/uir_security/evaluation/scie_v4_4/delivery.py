"""Finalize and independently verify the enumerated local delivery."""
import argparse
from pathlib import Path
import zipfile

from .common import DOC,FREEZE,ROOT,SOURCE,TASK,load,sha,write

MANIFEST=TASK/'manifests/ARTIFACT_SHA256_MANIFEST.json'


def final_checks():
    approval=load(TASK/'results/SUBMISSION_DECISION.json')
    evidence=load(TASK/'results/PUBLICATION_EVIDENCE_VALIDATION.json')
    if any(approval[k] for k in ('release_authorized','preprint_posted','journal_submitted','submission_allowed')):
        raise ValueError('Approval or receipt contradicts this unsigned delivery')
    doc=load(TASK/'manifests/MANUSCRIPT_RECEIPT.json')
    vis=load(TASK/'audits/VISUAL_REVIEW_RECEIPT.json')
    if sha(TASK/'statistics/SUMMARY.json')!=doc['science_summary_sha256']:
        raise ValueError('Manuscript summary mismatch')
    if set(doc['documents'])!={'journal','preprint'}:
        raise ValueError('Both source variants required')
    if not all(doc['documents']['journal'][k]==doc['documents']['preprint'][k] for k in ('body_sha256','results_sha256')):
        raise ValueError('Journal/preprint scientific text mismatch')
    for kind,d in doc['documents'].items():
        pdf,z=TASK/d['pdf'],TASK/d['zip']
        if not (sha(pdf)==d['pdf_sha256'] and sha(z)==d['zip_sha256'] and d['fresh_extract_build'] and d['pages']>0):
            raise ValueError('Manuscript files do not match receipt')
        vi=vis['documents'][kind]
        if vi['pdf_sha256']!=d['pdf_sha256'] or vi['reviewed_pages']!=list(range(1,d['pages']+1)):
            raise ValueError('Missing exact PDF visual QA')
        with zipfile.ZipFile(z) as a:
            names=a.namelist()
            if not names or a.testzip() is not None or a.read(pdf.name)!=pdf.read_bytes():
                raise ValueError('Source ZIP not bound to PDF')
            if kind=='preprint' and any(n.startswith('Definitions/') for n in names):
                raise ValueError('Journal template in generic preprint')
    reproduction=load(TASK/'audits/FRESH_EXTRACTION_RECEIPT.json')
    p=TASK/'private/HETE_V4_4_REPRODUCTION_PRIVATE.zip'
    if sha(p)!=reproduction['archive_sha256'] or not reproduction['summary_bytes_identical']:
        raise ValueError('Reproduction receipt mismatch')
    old=load(TASK/'audits/V43_FINAL_PRESERVATION.json')
    if not old['hash_integrity_verified'] or old['enumerated_files']!=241:
        raise ValueError('Historical preservation check failed')
    return evidence,approval


def generate():
    evidence,approval=final_checks()
    files=[]
    exclusions=['manifest itself','matplotlib cache','Python bytecode','scratch TeX aux/out/blg files',
                'obsolete intermediate visual renderings if present']
    for p in TASK.rglob('*'):
        if (not p.is_file() or p==MANIFEST or p.suffix in ('.aux','.out','.blg','.pyc','.lock')
            or 'mpl' in p.relative_to(TASK).parts or p.relative_to(TASK).parts[:2]==('audits','visual')):
            continue
        files.append(p)
    files.extend(p for p in SOURCE.rglob('*') if p.is_file() and p.suffix in ('.py','.md') and '__pycache__' not in p.parts)
    files.extend([ROOT/'tests/uir_security/test_scie_v4_4.py',ROOT/'AGENTS.md',ROOT/'LICENSE'])
    files.extend(p for p in DOC.iterdir() if p.is_file())
    obs={str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(files))}
    write(MANIFEST,{'freeze':FREEZE,'scope':'V4.4 local files enumerated here, not historical whole workspace or rights approval',
                    'files':obs,'excluded':exclusions,'science_valid':evidence['science_valid'],
                    'release_authorized':False,'preprint_posted':False,'journal_submitted':False,
                    'original_six_locally_matched':load(TASK/'manifests/PRIOR_SIX_ZIP_REVALIDATION_2026_11_08.json')['local_matches'],
                    'v43_preservation_receipt_sha256':sha(TASK/'audits/V43_FINAL_PRESERVATION.json'),
                    'publication_decision_sha256':sha(TASK/'results/SUBMISSION_DECISION.json')})
    return verify()


def verify():
    manifest=load(MANIFEST)
    errors=[]
    if not manifest['files'] or manifest['freeze']!=FREEZE:
        errors.append('Empty or wrong manifest')
    for key,v in manifest['files'].items():
        rel=Path(key)
        if rel.is_absolute() or '..' in rel.parts:
            errors.append('Invalid path '+key);continue
        p=ROOT/rel
        if not p.is_file() or p.stat().st_size!=v['bytes'] or sha(p)!=v['sha256']:
            errors.append(key)
    print({'files':len(manifest['files']),'integrity_verified':not errors,'errors':errors,
           'science_valid':manifest['science_valid'],'release_authorized':False},flush=True)
    return not errors


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--verify',action='store_true')
    if not (verify() if ap.parse_args().verify else generate()):
        raise SystemExit(1)
