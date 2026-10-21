import json
import subprocess
import sys
import zipfile
from datetime import datetime,timezone
from .common import *


def main():
    setup()
    roots=[OLD/'manifests/DELIVERY_MANIFEST.json',OLD/'manifests/V3_2_SCIENCE_MANIFEST.json',
           OLD/'manifests/frozen_recovery_receipt.json',OLD/'manifests/SCOPED_RELEASE_VERIFICATION.json',
           OLD/'reports/E01_AUDIT_STATUS.json',FROZEN/'ARTIFACT_MANIFEST.json']
    historical={str(p.relative_to(ROOT)):sha(p) for p in roots}
    for sub in ('data','manuscript_private','manifests'):
        historical.update({str(p.relative_to(ROOT)):sha(p) for p in (OLD/sub).rglob('*') if p.is_file()})
    freeze(TASK/'manifests/BASELINE_LOCK.json',{'id':'HETE-V4.2-baseline-lock-001',
        'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'files':historical,'historical_v32_full_manifest_pass':False,
        'missing_original_response_bodies':'eight unique interruption checkpoints; no synthetic recovery',
        'source_recovery':'13 exact-byte Python overlays, original files unchanged; 54 bytecode unresolved; 418 non-bytecode verified'})
    freeze(TASK/'manifests/V4_1_LOCK.json',{str(p.relative_to(ROOT)):sha(p) for p in [
        PROJECT/'evaluation/scie_v4/strict_boundary.py',PROJECT/'evaluation/scie_v4/full_pipeline_replacement.py',
        OLD/'data/outer_boundary_traces.jsonl',OLD/'data/full_pipeline_replacement.jsonl',OLD/'data/attack_trace.jsonl']})
    import importlib.metadata as m
    write(TASK/'manifests/ENVIRONMENT.json',{'python':sys.version,'executable':sys.executable,
        'os_release':Path('/etc/os-release').read_text(),'task_dependency_path':str(DEPS),
        'root_packages':{k:m.version(k) for k in ('jsonschema','requests','pytest','numpy','scipy')},
        'git_dirty':True,'started_utc':datetime.now(timezone.utc).isoformat()})
    write(TASK/'logs/baseline_git_status.txt',subprocess.check_output(['git','status','--short'],text=True))
    inventory=[]
    for path in sorted((OLD/'resources').glob('HETE_*.zip')):
        with zipfile.ZipFile(path) as z:
            inventory.append({'file':path.name,'sha256':sha(path),'crc_error':z.testzip(),
                'zero_byte_members':[i.filename for i in z.infolist() if not i.is_dir() and not i.file_size],
                'pdf_members':{i.filename:i.file_size for i in z.infolist() if i.filename.endswith('.pdf')}})
    write(TASK/'reports/INPUT_PACKAGE_INSPECTION.json',inventory)
    write(TASK/'manifests/DECISION_LOG.json',{'work_order':'HETE-ELEC-LGK04C9ZT5-V4.2-WO-20261021',
        'human_validation':False,'AI_alternative_authorization':'user approved Ministral14B/Qwen3.8-27B raters in previous turn',
        'historical_inputs_written':False,'submission_authorized':False,
        'author_information_source':'user-directed dlg_gnn/projects/benchmark/paper/current/a10; project-specific final sign-off not inferred',
        'funding_user_supplied':'This work was supported by the IITP(Institute of Information & Coummunications Technology Planning & Evaluation)-ITRC(Information Technology Research Center) grant funded by the Korea government(Ministry of Science and ICT)(IITP-2026-RS-2021-II211835)'})
    print('baseline files locked',len(historical),'package inventory',inventory)


if __name__=='__main__':main()
