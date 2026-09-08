import json
import math
from pathlib import Path

def compute_mcnemar(paired_outcomes_a, paired_outcomes_b):
    b = sum(1 for a_val, b_val in zip(paired_outcomes_a, paired_outcomes_b) if a_val == 1 and b_val == 0)
    c = sum(1 for a_val, b_val in zip(paired_outcomes_a, paired_outcomes_b) if a_val == 0 and b_val == 1)
    tot = b + c
    if tot == 0:
        chi2, p_val = 0.0, 1.0
    else:
        chi2 = ((abs(b - c) - 1.0) ** 2) / float(tot)
        p_val = math.erfc(math.sqrt(chi2) / math.sqrt(2.0))
    return {
        'b_discordant': b,
        'c_discordant': c,
        'chi2': round(chi2, 4),
        'p_value': round(p_val, 6),
        'p_exact': p_val,
        'statistically_significant': p_val < 0.01,
    }

res_dir = Path('/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1')
pairs = [json.loads(line) for line in open(res_dir / 'raw_runs/custom/evaluated_pairs.jsonl')]
ora_map = {p['oracle']['original_case_id']: p['oracle'] for p in pairs}

files = {
    'Vanilla SLM': res_dir / 'raw_runs/baselines/raw_run_vanilla_slm_phi35.jsonl',
    'Naive RAG': res_dir / 'raw_runs/baselines/raw_run_naive_rag_phi35.jsonl',
    'Spotlighting': res_dir / 'raw_runs/baselines/raw_run_spotlighting_phi35.jsonl',
    'Progent': res_dir / 'raw_runs/baselines/raw_run_progent_phi35.jsonl',
    'CaMeL': res_dir / 'raw_runs/baselines/raw_run_camel_phi35.jsonl',
    'HETE UIR-v3.1 Security': res_dir / 'raw_runs/phi35/raw_run_hete_uir_v3_1_security_phi35.jsonl',
}

vectors = {}
for name, path in files.items():
    records = [json.loads(line) for line in open(path)]
    vec = [1 if r['e2e_verdict'] else 0 for r in records if ora_map[r['case_id']]['is_attack']]
    vectors[name] = vec

hete_vec = vectors['HETE UIR-v3.1 Security']
comps = ['Vanilla SLM', 'Naive RAG', 'Spotlighting', 'Progent', 'CaMeL']
for name in comps:
    res = compute_mcnemar(vectors[name], hete_vec)
    arr = (sum(vectors[name]) - sum(hete_vec)) / 90.0 * 100.0
    print(f"{name}: b={res['b_discordant']}, c={res['c_discordant']}, chi2={res['chi2']}, p={res['p_exact']:.2e}, p_val={res['p_value']}, ARR={arr:.2f}pp, sig={res['statistically_significant']}")
