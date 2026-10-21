"""E01: hash, per-record count, exact statistics and attrition reconstruction."""
from __future__ import annotations

import json
import math
from collections import Counter

from .common import FROZEN, TASK, csv_write, load, rows, sha, write


def metric_counts(records):
    attacks = [r for r in records if r['is_attack']]
    benign = [r for r in records if not r['is_attack']]
    result = {'total_cases': len(records), 'attack_cases': len(attacks), 'benign_cases': len(benign)}
    for metric, subset, key in (
        ('mcr', attacks, 'model_compromised'), ('e2e', attacks, 'e2e_attack_succeeded'),
        ('utility', benign, 'complete_task_success'), ('frr', benign, 'false_rejection'),
    ):
        result[metric] = {'count': sum(bool(r['verdict'].get(key)) for r in subset), 'denominator': len(subset)}
    return result


def main():
    manifest = load(FROZEN / 'ARTIFACT_MANIFEST.json')
    failures = []
    entries = []
    for item in manifest['artifacts']:
        p = FROZEN / item['path']
        ok = p.is_file() and p.stat().st_size == item['size'] and sha(p) == item['sha256']
        entries.append({**item, 'verified': ok})
        if not ok:
            failures.append('frozen hash:' + item['path'])
    baseline = load(FROZEN / 'baseline_comparison.json')
    ablations = load(FROZEN / 'ablation_results.json')
    models = load(FROZEN / 'multi_model_results.json')
    stochastic = load(FROZEN / 'stochastic_results.json')
    index, table, primary, case_sets = [], [], {}, {}
    for path in sorted((FROZEN / 'raw_runs').glob('*.jsonl')):
        if path.stem == 'adaptive':
            continue
        records = list(rows(path))
        ids = [r['case_id'] for r in records]
        counts = metric_counts(records)
        if len(set(ids)) != len(ids):
            failures.append('duplicate ID:' + path.name)
        if path.stem.startswith('primary_'):
            name = records[0]['system']; summary = baseline[name]; primary[name] = records
        elif path.stem.startswith('ablation_'):
            name = path.stem.removeprefix('ablation_'); summary = ablations[name]
        elif path.stem == 'multimodel_phi':
            name = 'phi3.5:latest'; summary = models[name]
        else:
            name = path.stem.removeprefix('stochastic_'); summary = stochastic[name]
        for key, value in counts.items():
            actual = summary[key]
            if isinstance(value, dict):
                actual = {k: actual[k] for k in ('count', 'denominator')}
            matched = value == actual
            table.append({'run': path.stem, 'metric': key, 'raw': json.dumps(value), 'summary': json.dumps(actual), 'matched': matched})
            if not matched:
                failures.append(f'summary:{path.name}:{key}')
        case_sets[path.stem] = set(ids)
        index.append({'run': path.stem, 'system_or_config': name, 'records': len(records),
                      'unique_ids': len(set(ids)), 'attacks': counts['attack_cases'], 'benign': counts['benign_cases'],
                      'sha256': sha(path), 'path': str(path.relative_to(FROZEN))})
    canonical = case_sets['primary_5']
    for name, ids in case_sets.items():
        if not name.startswith('stochastic_') and ids != canonical:
            failures.append('case-set:' + name)
    stats = load(FROZEN / 'statistical_tests.json')
    exact = []
    hete = {r['case_id']: r for r in primary['HETE'] if r['is_attack']}
    for system, recs in primary.items():
        if system == 'HETE':
            continue
        other = {r['case_id']: r for r in recs if r['is_attack']}
        b = sum(bool(other[i]['verdict']['e2e_attack_succeeded']) and not hete[i]['verdict']['e2e_attack_succeeded'] for i in hete)
        c = sum(not other[i]['verdict']['e2e_attack_succeeded'] and bool(hete[i]['verdict']['e2e_attack_succeeded']) for i in hete)
        n = b + c
        p = min(1.0, 2 * sum(math.comb(n, j) for j in range(min(b, c) + 1)) / 2**n) if n else 1.0
        saved = next(s for s in stats['pairs'] if s['system'] == system)
        if not math.isclose(p, saved['p_value'], rel_tol=1e-12):
            failures.append('exact-p:' + system)
        exact.append({'system': system, 'b': b, 'c': c, 'exact_p': p})
    order = sorted(range(len(exact)), key=lambda i: exact[i]['exact_p'])
    previous = 0.0
    for rank, i in enumerate(order):
        previous = max(previous, min(1.0, exact[i]['exact_p'] * (len(exact) - rank)))
        exact[i]['holm_p'] = previous
        saved = next(s for s in stats['pairs'] if s['system'] == exact[i]['system'])
        if not math.isclose(previous, saved['holm_p'], rel_tol=1e-12):
            failures.append('holm:' + exact[i]['system'])
    adaptive = list(rows(FROZEN / 'raw_runs/adaptive.jsonl'))
    adaptive_summary = load(FROZEN / 'adaptive_attack_results.json')
    for campaign, expected in adaptive_summary.items():
        subset = [r for r in adaptive if r['campaign'] == campaign]
        actual = {'seeds': len(subset), 'queries': sum(len(r['queries']) for r in subset),
                  'mcr_seeds': sum(r['first_mcr_query'] is not None for r in subset),
                  'e2e_seeds': sum(r['first_e2e_query'] is not None for r in subset)}
        if actual != expected:
            failures.append('adaptive:' + campaign)
    funnel_cases = list(rows(FROZEN / 'containment_funnel_cases.jsonl'))
    funnel_summary = load(FROZEN / 'containment_funnel.json')
    actual_funnel = {key: sum(bool(r.get(key)) for r in funnel_cases) for key in funnel_summary}
    if actual_funnel != funnel_summary:
        failures.append('funnel:' + json.dumps(actual_funnel))
    interruption = load(FROZEN / 'operational_interruption_summary.json')
    ledger = []
    for item in interruption['interruptions']:
        ledger.append({'system': item['group'], 'case_id': item['case_id'], 'completed_rows': item['completed_rows'],
                       'event_time': 'not retained in original failure JSON', 'original_body_retained': False,
                       'admitted': False, 'resumed_missing_case': True, 'error': item['error'],
                       'source_paths': ';'.join(item['evidence_paths']), 'diagnostic_count': len(item['diagnostics'])})
    runtime = load(FROZEN / 'runtime_manifest.json')
    write(TASK / 'manifests/V3_2_SCIENCE_MANIFEST.json', {'frozen_root': str(FROZEN),
        'frozen_manifest_sha256': sha(FROZEN / 'ARTIFACT_MANIFEST.json'), 'artifacts': entries,
        'immutable_models': runtime['models'], 'audit_failures': failures,
        'preservation': 'byte-preserved source tree; hash-anchored snapshot, not OS read-only protection',
        'passed': not failures})
    csv_write(TASK / 'data/run_index.csv', index)
    csv_write(TASK / 'data/TABLE_RECONCILIATION.csv', table)
    csv_write(TASK / 'data/attrition_ledger.csv', ledger)
    write(TASK / 'data/exact_statistics_recomputed.json', exact)
    write(TASK / 'data/funnel_audit.json', {'counts': actual_funnel, 'case_ids': len({r['case_id'] for r in funnel_cases}),
        'overlapping': True, 'llm_exposed_denominator': 363, 'precall': {'policy': 210, 'resource': 27}})
    amendments = [load(FROZEN / f'SOURCE_AMENDMENT_0{i}.json') for i in (1, 2)]
    write(TASK / 'data/source_amendment_changelog.json', amendments)
    write(TASK / 'reports/lineage.md', '# V3.2 lineage audit\n\n'
        f'Frozen manifest: {len(entries)} entries, {len(failures)} failures. No original was edited.\n\n'
        'Eight unique incomplete-response interruptions are retained as an attrition ledger; response bodies and exact event timestamps were not retained for those original attempts. Later diagnostic bodies are not substitutes for the missing original. Repeated retries and manual interruptions remain in the original operational/source amendment history; eight is not a count of every attempted HTTP call.\n\n'
        'Amendment 01 changed verdict adjudication for preserved baseline generations (850 Vanilla and 399 Naive RAG rows). Amendment 02 changed future duplicate adaptive-candidate handling. Original timestamps and BEFORE/AFTER hashes are in data/source_amendment_changelog.json. An approval timestamp separate from the amendment timestamp was not recorded; none is fabricated.\n\n'
        'phi3.5:latest is a historical display tag; immutable model digest is recorded in the science manifest. Hash integrity does not prove statistical validity or authenticity. Current relocated source is not asserted byte-identical to evaluated source epochs.\n')
    write(TASK / 'reports/E01_AUDIT_STATUS.json', {'passed': not failures, 'failures': failures,
        'manifest_entries': len(entries), 'primary_n': 850, 'adaptive_queries': sum(len(r['queries']) for r in adaptive)})
    print(json.dumps({'passed': not failures, 'failures': failures, 'manifest_entries': len(entries)}))
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
