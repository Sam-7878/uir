import json
from pathlib import Path
from collections import defaultdict

res_dir = Path('/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1')
pairs = [json.loads(line) for line in open(res_dir / 'raw_runs/custom/evaluated_pairs.jsonl')]
ora_map = {p['oracle']['original_case_id']: p['oracle'] for p in pairs}

hete_file = res_dir / 'raw_runs/phi35/raw_run_hete_uir_v3_1_security_phi35.jsonl'
records = [json.loads(line) for line in open(hete_file)]

class_counts = defaultdict(lambda: {'total': 0, 'mcr': 0, 'e2e': 0, 'benign': 0})
for r in records:
    ora = ora_map[r['case_id']]
    cls_name = ora.get('attack_class') or 'valid_benign'
    class_counts[cls_name]['total'] += 1
    if ora['is_attack']:
        if r['mcr_verdict']: class_counts[cls_name]['mcr'] += 1
        if r['e2e_verdict']: class_counts[cls_name]['e2e'] += 1
    else:
        if r['utility_verdict']: class_counts[cls_name]['benign'] += 1

print('HETE UIR-v3.1 Per-Class Breakdown:')
for cls, d in sorted(class_counts.items()):
    tot = d['total']
    mcr_p = round(d['mcr'] / tot * 100, 2) if cls != 'valid_benign' else 0.0
    e2e_p = round(d['e2e'] / tot * 100, 2) if cls != 'valid_benign' else 0.0
    util_p = round(d['benign'] / tot * 100, 2) if cls == 'valid_benign' else 0.0
    print(f"  {cls}: n={tot}, MCR={d['mcr']}/{tot} ({mcr_p}%), E2E={d['e2e']}/{tot} ({e2e_p}%), Util={d['benign']}/{tot} ({util_p}%)")
