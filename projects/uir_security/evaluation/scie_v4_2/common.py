import csv
import hashlib
import json
import os
import sys
from pathlib import Path
sys.dont_write_bytecode=True

ROOT=Path(os.environ.get('UIR_REPOSITORY',os.getcwd())).absolute()
if not (ROOT/'AGENTS.md').is_file():raise RuntimeError('Run from the UIR repository root')
PROJECT=ROOT/'projects/uir_security'
OLD=PROJECT/'results/scie_acceptance_2026_10_21_v4'
TASK=PROJECT/'results/hete_electronics_v4_2_2026_10_21'
FROZEN=PROJECT/'results/llm_security_v3_2_closure'
DEPS=OLD/'resources/benchmark_env/lib/python3.14/site-packages'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value if isinstance(value,str) else json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def rows(path):
    with Path(path).open() as f:
        for line in f:
            if line.strip():yield json.loads(line)
def csvwrite(path,records):
    if not records:raise ValueError('Refuse empty evidence table')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)


def freeze(path,value):
    path=Path(path)
    if path.exists() and load(path)!=value:raise RuntimeError('Frozen protocol differs: '+str(path))
    write(path,value)


def setup():
    for name in ('experiments/typed_semantics','experiments/policy_incremental','experiments/agentdojo_external',
       'experiments/official_baseline','experiments/model_substitution','experiments/multimodel_utility',
       'experiments/adaptive_redteam','experiments/human_audit','data/raw_private','data/redacted_public_candidate',
       'data/statistics','source','manuscript_preprint','manuscript_electronics','supplementary','submission_private'):
        (TASK/name).mkdir(parents=True,exist_ok=True)
