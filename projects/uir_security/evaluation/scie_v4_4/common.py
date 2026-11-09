from datetime import datetime, timezone
from hashlib import file_digest, sha256
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SOURCE = Path(__file__).resolve().parent
RESULTS = ROOT / 'projects/uir_security/results'
TASK = RESULTS / 'hete_electronics_v4_4_2026_11_08'
V43 = RESULTS / 'hete_electronics_v4_3_2026_10_23'
DOC = ROOT / 'docs/work_reports/uir_security/204_hete_v4.4'
FREEZE = 'HETE-ELECTRONICS-V4.4-2026-11-08-R1'


def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(obj):
    return sha256(canon(obj).encode()).hexdigest()


def sha(path):
    with path.open('rb') as f:
        return file_digest(f, 'sha256').hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, obj, *, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive:
        with path.open('x', encoding='utf-8') as f:
            f.write(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    else:
        temp = path.with_name(path.name + '.tmp')
        temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        temp.replace(path)


def append(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(canon(obj) + '\n')
        f.flush()
        os.fsync(f.fileno())


def lines(path):
    with path.open(encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)
