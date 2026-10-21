"""Recover exact historical bytes into a NEW overlay without editing frozen inputs."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from .common import FROZEN, ROOT, TASK, load, sha, write


def main():
    entries = load(FROZEN/'ARTIFACT_MANIFEST.json')['artifacts']
    missing = [r for r in entries if not (FROZEN/r['path']).is_file() or sha(FROZEN/r['path']) != r['sha256']]
    desired = {r['sha256']:r for r in missing}
    names = {Path(r['path']).name for r in missing}
    objects = subprocess.check_output(['git','rev-list','--objects','--all'], cwd=ROOT, text=True)
    candidates = []
    for line in objects.splitlines():
        parts = line.split(' ',1)
        if len(parts)==2 and Path(parts[1]).name in names:
            candidates.append(parts)
    recovery = []
    for oid, recorded in candidates:
        proc = subprocess.run(['git','cat-file','blob',oid],cwd=ROOT,capture_output=True)
        if proc.returncode:
            continue
        digest = hashlib.sha256(proc.stdout).hexdigest()
        if digest in desired:
            entry = desired[digest]
            target = TASK/'resources/recovered_v32_overlay'/entry['path']
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(proc.stdout)
            recovery.append({'path':entry['path'],'sha256':digest,'git_blob':oid,'historical_path':recorded,
                             'recovered_overlay':str(target.relative_to(TASK))})
            del desired[digest]
    # Layout edits replaced repository discovery. A candidate reversal is accepted
    # only if its ENTIRE byte sequence matches the already-frozen expected SHA.
    import re
    for entry in missing:
        p=FROZEN/entry['path']
        if not p.is_file() or p.suffix != '.py':
            continue
        data=p.read_text()
        for depth in range(2,7):
            candidate=re.sub(r"REPO\s*=\s*next\(p for p in Path\(__file__\)\.resolve\(\)\.parents if \(p / 'Cargo.toml'\)\.is_file\(\)\)",
                ('REPO=' if 'REPO=next' in data else 'REPO = ')+f'Path(__file__).resolve().parents[{depth}]',data).encode()
            if hashlib.sha256(candidate).hexdigest()==entry['sha256']:
                target=TASK/'resources/recovered_v32_overlay'/entry['path'];target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(candidate)
                recovery.append({'path':entry['path'],'sha256':entry['sha256'],'method':'exact SHA-verified reversal of layout-only REPO discovery edit',
                                 'recovered_overlay':str(target.relative_to(TASK))})
                break
    # A single digest can occur at several source-epoch paths.
    by_hash={r['sha256']:TASK/r['recovered_overlay'] for r in recovery}
    for entry in missing:
        if entry['sha256'] in by_hash:
            target=TASK/'resources/recovered_v32_overlay'/entry['path'];target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(by_hash[entry['sha256']].read_bytes())
    unresolved=[r for r in missing if not (TASK/'resources/recovered_v32_overlay'/r['path']).is_file()
                or sha(TASK/'resources/recovered_v32_overlay'/r['path'])!=r['sha256']]
    write(TASK/'manifests/frozen_recovery_receipt.json', {'initial_mismatches':len(missing),
        'recovered':recovery,'unrecovered':unresolved,'original_files_edited':False,
        'interpretation':'overlay accepts only entire byte strings matching frozen hashes; missing bytecode is not fabricated'})
    print('initial mismatches',len(missing),'recovered_files',len(missing)-len(unresolved),'unrecovered_files',len(unresolved))


if __name__=='__main__':
    main()
