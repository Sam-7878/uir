from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get('UIR_REPOSITORY', os.getcwd())).absolute()
if not (ROOT / 'AGENTS.md').is_file():
    raise RuntimeError('Run from the UIR repository root or set UIR_REPOSITORY')
PROJECT = ROOT / 'projects/uir_security'
FROZEN = PROJECT / 'results/llm_security_v3_2_closure'
TASK = PROJECT / 'results/scie_acceptance_2026_10_21_v4'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path: Path):
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    path.write_text(text, encoding='utf-8')


def csv_write(path: Path, values: list[dict]):
    if not values:
        raise ValueError('Refuse empty scientific table')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)
