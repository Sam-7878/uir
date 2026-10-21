"""Post-hoc sensitivity analysis; no new inference or changes to V3.2 scoring."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict

import numpy as np

from .common import FROZEN, TASK, csv_write, load, rows, write


def wilson(k, n):
    if n == 0:
        return [None, None]
    z = 1.959963984540054; p = k / n; d = 1 + z*z/n
    center = (p + z*z/(2*n))/d
    margin = z*((p*(1-p)/n + z*z/(4*n*n))**.5)/d
    return [max(0, center-margin), min(1, center+margin)]


def main():
    rng = np.random.default_rng(20261021)
    protocols = {'analysis_id': 'J13-posthoc-V4-001', 'resamples': 3000, 'seed': 20261021,
                 'primary_endpoint': 'forbidden trusted effect (separate resource breach)',
                 'secondary_endpoints': ['raw behavioral MCR','benign complete utility','false rejection','latency','token usage'],
                 'multiplicity': 'historical five primary paired E2E comparisons, Holm alpha .05',
                 'cluster_limit': 'true generator family IDs were not retained; class-language coarse proxies are a sensitivity analysis, not validated template families'}
    write(TASK/'manifests/stats_protocol.json', protocols)
    table, latency, cluster_table, phi_failures, taxonomy = [], [], [], [], []
    for path in sorted((FROZEN/'raw_runs').glob('primary_*.jsonl')) + [FROZEN/'raw_runs/multimodel_phi.jsonl']:
        records = list(rows(path)); system = records[0]['system']; model = records[0]['model']
        grouping = defaultdict(list)
        for r in records:
            grouping[('language', r['runtime_case']['language'])].append(r)
            grouping[('class', r['attack_class'])].append(r)
            e = r['execution'];status = e.get('terminal_status','UNKNOWN')
            if not e.get('llm_invoked',bool(r.get('calls'))):
                category = 'llm_not_invoked_resource' if 'RESOURCE' in status else 'llm_not_invoked_policy'
            elif status in {'MODEL_ERROR','BACKEND_ERROR','TIMEOUT','OOM'}:
                category = 'backend_failure'
            elif 'RESOURCE' in status:
                category = 'resource_rejection'
            elif any(g['component'] == 'OutputGuard' for g in e.get('guard_events',[])):
                category = 'json_or_evidence_contract_rejection'
            elif e.get('mock_state_mutations'):
                category = 'trusted_mock_mutation'
            else:
                category = 'allowed_or_action_filtered'
            taxonomy.append({'run':path.stem,'case_id':r['case_id'],'language':r['runtime_case']['language'],
                             'class':r['attack_class'],'category':category,'terminal_status':status})
        for (dimension, value), subset in grouping.items():
            for metric, key, attack in [('mcr','model_compromised',True),('e2e','e2e_attack_succeeded',True),
                                      ('utility','complete_task_success',False),('frr','false_rejection',False)]:
                population = [r for r in subset if r['is_attack'] == attack]
                n = len(population)
                if n:
                    k = sum(bool(r['verdict'].get(key)) for r in population); lo,hi = wilson(k,n)
                    table.append({'run':path.stem,'system':system,'model':model,'dimension':dimension,
                                  'value':value,'metric':metric,'count':k,'n':n,'rate':k/n,'wilson_lo':lo,'wilson_hi':hi})
        paths = defaultdict(list)
        for r in records:
            paths[('attack' if r['is_attack'] else 'benign')+'_'+r['execution']['terminal_status']].append(r)
        paths['all_admitted'] = records
        for name, subset in paths.items():
            times = [r['execution']['latency_ms'] for r in subset]
            latency.append({'run':path.stem,'path':name,'n':len(subset),
                            'p50_ms':float(np.quantile(times,.5)), 'p95_ms':float(np.quantile(times,.95)),
                            'p99_ms':float(np.quantile(times,.99)), 'mean_ms':float(np.mean(times)),
                            'input_tokens':sum(c.get('input_tokens',0) for r in subset for c in r['calls']),
                            'output_tokens':sum(c.get('output_tokens',0) for r in subset for c in r['calls'])})
        for metric,key,attack in [('mcr','model_compromised',True),('e2e','e2e_attack_succeeded',True),('utility','complete_task_success',False)]:
            clusters = defaultdict(list)
            for r in records:
                if r['is_attack'] == attack:
                    clusters[(r['attack_class'],r['runtime_case']['language'])].append(bool(r['verdict'].get(key)))
            values = list(clusters.values()); totals = np.array([sum(v) for v in values]); sizes=np.array([len(v) for v in values])
            idx=rng.integers(0,len(values),size=(3000,len(values)))
            estimates=totals[idx].sum(axis=1)/sizes[idx].sum(axis=1)
            lo,hi=np.quantile(estimates,[.025,.975])
            cluster_table.append({'run':path.stem,'metric':metric,'proxy_clusters':len(values),
                                  'bootstrap_lo':float(lo),'bootstrap_hi':float(hi),
                                  'warning':'all-zero resamples are degenerate; not a zero-risk bound or proof of external validity'})
        if path.stem == 'multimodel_phi':
            for r in records:
                if r['is_attack']:
                    continue
                raw=r['execution'].get('model_output',''); reason=''
                try:
                    parsed=json.loads(raw)
                    if not isinstance(parsed,dict): reason='json_not_object'
                    elif not {'entity','metric','value','citations'} <= set(parsed): reason='missing_required_fields'
                    elif not r['verdict'].get('citation_accuracy'): reason='citation_failure_or_rejection'
                    elif not r['verdict'].get('numeric_match'): reason='numeric_failure_or_rejection'
                    else: reason='contract_or_policy_rejection'
                except ValueError: reason='whole_json_parse_failure'
                phi_failures.append({'case_id':r['case_id'],'language':r['runtime_case']['language'],
                    'failure_category':reason,'finish_reasons':';'.join(str(c.get('finish_reason')) for c in r['calls']),
                    'backend_complete':all(c['response'].get('done') is True for c in r['calls']),
                    'observed_output_tokens':sum(c['output_tokens'] for c in r['calls']),
                    'raw_sha256':__import__('hashlib').sha256(raw.encode()).hexdigest()})
    csv_write(TASK/'data/per_class_language_intervals.csv',table)
    csv_write(TASK/'data/latency_quantiles.csv',latency)
    csv_write(TASK/'data/cluster_sensitivity.csv',cluster_table)
    csv_write(TASK/'data/phi_failure_analysis.csv',phi_failures)
    csv_write(TASK/'data/outcome_taxonomy.csv',taxonomy)
    write(TASK/'reports/MULTIMODEL_FAILURE_ANALYSIS.md','# Historical Phi-3.5 failure analysis\n\n'
          +json.dumps(dict(Counter(r['failure_category'] for r in phi_failures)),indent=2)+'\n\n'
          'All 250 original benign outcomes remain failures. Categories use stored output syntax and historical verdicts; downstream rejection conflates semantic correctness with accepted output and does not establish the unique causal reason. '
          'Backend completion means transport completed, not that content followed the contract. No template/prompt fix is applied to the frozen population.\n')
    write(TASK/'reports/STATS_VALIDATION.md','# Post-hoc statistical sensitivity\n\n'
          'Per-language and per-class Wilson intervals, latency p50/p95/p99, token totals and outcome taxonomy are recomputed from admitted raw records. '
          'Historical exact McNemar/Holm is independently regenerated by audit_v32.py. Excluded incomplete attempts remain in attrition_ledger.csv and cannot be assigned missing generation latency.\n\n'
          'Original template-family labels were not preserved. Coarse class-language clustering is explicitly a sensitivity proxy, not a recovered family-disjoint experiment. '
          'The 0/600 Wilson upper bound is '+str(wilson(0,600)[1])+'. Zero-only bootstrap samples are degenerate and cannot bound unseen risk. '
          'This is an independent implementation within the same research workflow, not external human certification.\n')
    print('wrote intervals, latency, cluster sensitivity, Phi analysis, taxonomy')


if __name__=='__main__':
    main()
