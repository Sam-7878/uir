"""Account for every planned official-environment trial, including nonexposure."""
import json
from collections import defaultdict

import numpy as np

from .common import TASK, csv_write, load, rows, write


def main():
    records=list(rows(TASK/'data/benchmark_results.jsonl'))
    if len(records)!=48 or len({r['run_id'] for r in records})!=48:
        raise ValueError('Expected all 48 unique preregistered trials')
    grouped=defaultdict(list)
    for r in records:grouped[(r['domain'],r['model'],r['config'])].append(r)
    summary=[]
    for (domain,model,config),subset in sorted(grouped.items()):
        clean=[r for r in subset if not r['attack']];attacks=[r for r in subset if r['attack']]
        exposed=[r for r in attacks if any('IMPORTANT NEW TASK' in str(t.get('observation')) for t in r['trace'])]
        calls=[c['response'] for r in subset for c in r['calls']]
        summary.append({'domain':domain,'model':model,'system':config,'benign_n':len(clean),
            'benign_utility':sum(r['utility'] for r in clean),'attack_n':len(attacks),
            'attack_success':sum(r['attack_success'] is True for r in attacks),
            'attack_utility':sum(r['utility'] for r in attacks),'injected_content_observed':len(exposed),
            'backend_errors':sum(r['backend_failure'] for r in subset),
            'state_mutating_trials':sum(r['pre_state']!=r['post_state'] for r in subset),
            'denied_tool_proposals':sum(not t['admitted'] for r in subset for t in r['trace']),
            'latency_p50_s':float(np.quantile([r['latency_s'] for r in subset],.5)),
            'latency_p95_s':float(np.quantile([r['latency_s'] for r in subset],.95)),
            'input_tokens':sum(c.get('prompt_eval_count',0) for c in calls),
            'output_tokens':sum(c.get('eval_count',0) for c in calls)})
    csv_write(TASK/'data/public_benchmark_domain_results.csv',summary)
    write(TASK/'data/public_benchmark_domain_results.json',summary)
    write(TASK/'reports/public_benchmark_report.md','# Official AgentDojo read-only pilot\n\n'
          'All 48 registered trials completed. The environment, tasks and utility/security oracles come from AgentDojo 0.1.35 '
          '(benchmark v1.2.2; exact commit in manifests/agentdojo_protocol.json). This is a local JSON-agent integration, '
          'not a leaderboard reproduction or the complete historical HETE agent. Four read-only tasks, two domains, '
          'two installed immutable model artifacts, benign/attack variants and three local systems were run. '
          'The original injection_task_0 goal remains unchanged; a custom append payload populates all official injection vectors. '
          'The attacker does not receive utility-oracle answers, and the agent receives no ground_truth.\n\n'
          'public_benchmark_domain_results.csv separates planned attack denominators from actual observed injected content. '
          'A task that never reads the modified surface is not evidence of model resistance. Official ASR and utility are reported separately, '
          'including trials where both succeed. Counts are tiny and tasks correlated; no population superiority or significance claim is made. '
          'State mutations include legitimate read side effects, such as marking an email as read; the official security oracle determines attacker-goal success. '
          'Denied proposal counts are a policy rejection proxy, not a natural-language refusal rate. '
          'GPU energy was not measured; actual Ollama input/output counters and latency are retained.\n\n'
          'The minimal and typed adapters share the same capability predicate. Their matched observations do not demonstrate an incremental security '
          'or semantic utility benefit from typed syntax. The read-only policy would be overrestrictive for a write task, '
          'which is why no write-task comparison is claimed.\n\n'+json.dumps(summary,indent=2)+'\n')
    write(TASK/'reports/benchmark_protocol.md','# Registered external protocol\n\n'+json.dumps(load(TASK/'manifests/agentdojo_protocol.json'),indent=2)+'\n\n'
          'Frozen before first inference. Deviations and backend failures are represented per trial. Read-only selection and the '
          'simple JSON agent restrict generalization. Public task familiarity/training contamination cannot be ruled out.\n')
    print('trials',len(records),'backend_errors',sum(r['backend_failure'] for r in records),
          'attacks',sum(r['attack'] for r in records),'successes',sum(r['attack_success'] is True for r in records))


if __name__=='__main__':main()
