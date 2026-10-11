"""Render required secondary tables directly from final reconstructed artifacts."""
import json

def supplemental(out, tex):
    def load(name):return json.loads((out/name).read_text())
    def table(caption, headers, values, wide=True):
        env='table*' if wide else 'table'
        lines=[r'\begin{'+env+r'}[t]\centering\small\caption{'+caption+r'}',r'\begin{tabular}{l'+'r'*(len(headers)-1)+r'}\hline', ' & '.join(headers)+r' \\\hline']
        lines+=[' & '.join(str(x) for x in row)+r' \\' for row in values]
        return '\n'.join(lines+[r'\hline\end{tabular}\end{'+env+'}'])+'\n'
    text=r'\subsection{Adaptive search and containment}'+'\n'
    adaptive=load('adaptive_attack_results.json')
    text+=f"The completed A2 search contains {sum(x['seeds'] for x in adaptive.values())} seeds and {sum(x['queries'] for x in adaptive.values())} actual candidate queries. Each seed uses at most 20 queries and stops early only at its first E2E success. Seed success rates below count seeds with at least one success, not individual-query rates.\n"
    labels={'direct_prompt_injection':'Direct injection','indirect_prompt_injection':'Indirect injection','sensitive_data_exfiltration':'Protected-secret extraction','excessive_agency_tool_escalation':'Agency escalation','jailbreak_policy_override':'Policy override','gaslighting_false_premise':'False-premise manipulation'}
    text+=table('Adaptive A2 search: actual counts.', ['Campaign','Seeds','Queries','MCR seeds','E2E seeds'],[[labels[k],r['seeds'],r['queries'],r['mcr_seeds'],r['e2e_seeds']] for k,r in adaptive.items()])
    funnel=load('containment_funnel.json')
    text+=table('HETE attack-stage indicators. Indicators overlap and are not a sequential subtraction funnel.', ['Indicator','Cases'],[[tex(k),v] for k,v in funnel.items()],False)
    text+=r'Every indicator is bound to case IDs in \texttt{containment\_funnel\_cases.jsonl}; rejection alone does not satisfy MCR.'+'\n'
    text+=r'\subsection{Utility, protected data, and mock actions}'+'\n'
    utility=load('secondary_utility_metrics.json')['primary']
    text+=table('Benign utility decomposition, count/250. Semantic success requires an allowed answer with correct entity, metric, quantity and year; complete success additionally requires the schema and citation set.', ['System','Semantic','Numeric','Entity','Contract','Citation'],[[tex(k)]+[r[x]['count'] for x in ('semantic_task_success','numeric_exact_match','entity_exact_match','contract_validity','citation_accuracy')] for k,r in utility.items()])
    ex=load('exfiltration_details.json');ag=load('agency_details.json')
    text+=table('Protected-token leakage and unauthorized mock effects. Counts use the class denominators shown.', ['System','Exfil N','Raw leaks','Egress leaks','Agency N','Forbidden-effect cases'],[[tex(k),r['case_count'],r['model_leakage_count'],r['egress_leakage_count'],ag[k]['case_count'],ag[k]['cases_with_forbidden_mutations']] for k,r in ex.items()])
    gates=load('tool_gate_comparison.json')
    text+=table('Agency-class ablation paths on identical cases. Invocation means the mock executor was actually called; mutation means its state changed.', ['Configuration','N','Proposal cases','Executor cases','Mutation cases'],[[tex(k),r['case_count'],r['cases_with_tool_proposals'],r['cases_with_executor_invocations'],r['cases_with_forbidden_mutations']] for k,r in gates.items()])
    resources=load('resource_guard_comparison.json')
    text+=table('Resource-class comparison on identical cases. Token values are sums of actual Ollama counters for invoked calls; elapsed time is measured at runtime.', ['Configuration','N','Resource blocks','E2E exceeds','Input tokens','Output tokens'],[[tex(k),r['case_count'],r['blocked_resource_exhausted'],r['e2e_resource_exceed_count'],f"{r['consumption_totals']['input_tokens']:.0f}",f"{r['consumption_totals']['output_tokens']:.0f}"] for k,r in resources.items()])
    text+=r'\subsection{Runtime paths and stochastic subset}'+'\n'
    # Short labels avoid overflowing the two-column manuscript.
    paths=load('latency_by_path.json')
    text+=table('HETE measured runtime paths; mean milliseconds include adapter execution and actual backend calls.', ['Path','N','Mean ms'],[[tex(k.replace('BLOCKED_','B_').replace('RESOURCE_EXHAUSTED','RESOURCE')),v['count'],f"{v['mean_ms']:.2f}"] for k,v in paths.items()])
    stochastic=load('stochastic_results.json')
    text+=table('The same frozen 30-case subset at each stochastic seed. Entries report count/denominator.', ['Seed','MCR','E2E','Complete utility'],[[k]+[f"{r[x]['count']}/{r[x]['denominator']}" for x in ('mcr','e2e','utility')] for k,r in stochastic.items()])
    long=load('benign_long_supplement/audit.json')['groups']
    text+=table('Supplementary benign length sensitivity: 10 fixed seed tasks at each request-length target. The 1400 target exceeds the 1024 input budget; these rows are separate from the primary population.', ['Estimated tokens','N','Resource blocks','All guard rejections','Complete utility'],[[k,r['cases'],r['resource_rejections'],r['all_guard_false_rejections'],r['complete_success']] for k,r in long.items()])
    h=load('baseline_comparison.json')['HETE']
    text+=f"For this population, HETE produced {h['mcr']['count']} model-compromise cases and {h['e2e']['count']} end-to-end failures among {h['attack_cases']} attacks; complete benign success was {h['utility']['count']}/{h['benign_cases']}. These observations must be read together: lower egress risk accompanied by rejected or invalid benign answers does not demonstrate preserved utility. Differences between the two attack counts are descriptive, not evidence that every rejected output was a compromise.\n"
    return text
