import csv
import hashlib
import json
import os
import sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path.cwd().absolute()
if not (ROOT/'AGENTS.md').is_file():raise RuntimeError('Run from the UIR repository root')
PROJECT=ROOT/'projects/uir_security'
BASE=PROJECT/'results/hete_electronics_v4_2_2026_10_21'
TASK=PROJECT/'results/hete_electronics_v4_3_2026_10_23'
DOC=ROOT/'docs/work_reports/uir_security/203_hete_v4.3'
FREEZE='HETE-ELECTRONICS-V4.3-2026-10-23-R1'
PYTHON=sys.executable
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(path):return json.loads(Path(path).read_text())
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def rows(path):
    with Path(path).open() as stream:
        for line in stream:
            if line.strip():yield json.loads(line)
def csvwrite(path,values):
    if not values:raise ValueError('Empty evidence')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(values[0]));writer.writeheader();writer.writerows(values)
def freeze(path,value):
    path=Path(path)
    if path.exists() and load(path)!=value:raise RuntimeError('Frozen protocol differs: '+str(path))
    write(path,value)
