"""Document renderer. Publication numbers require a raw-data audit with no data failures."""
from pathlib import Path
import json
import hashlib
import re
import sys
REPO=next(p for p in Path(__file__).resolve().parents if (p / 'Cargo.toml').is_file())
RESULTS=REPO/'results/llm_security_v3_2_closure'
PAPER=REPO/'docs/papers/_47_1_UIR_for_ZTA'
DOC=REPO/'docs/security_v3_2'
def tex(value):
 return str(value).replace('\\',r'\textbackslash{}').replace('_',r'\_').replace('%',r'\%').replace('&',r'\&').replace('#',r'\#')
def load(name):
 p=RESULTS/name
 return json.loads(p.read_text()) if p.exists() else {}

def render(final=False):
 manifest=load('dataset_manifest_v3_2.json');protocol=load('campaign_protocol.json')
 report=load('publication_evidence_validation.json')
 operations=load('operational_interruption_summary.json')
 if final:
  problems=[x for x in report.get('scientific_integrity_failures',['no raw audit']) if not x.startswith('methodology ') and x!='Missing or invalid methodology_acceptance.json']
  if problems:raise ValueError('Raw audit must pass before rendering final numbers: '+str(problems[:5]))
 status='V3.2 FROZEN EXECUTION EVIDENCE' if final else 'INCOMPLETE: LIVE EXECUTION / VALIDATION PENDING'
 intro=r'''\section{Experimental Methodology}\label{sec:methodology}
\subsection{Evidence status and population}
'''+tex(status)+'.\n'
 splits=manifest.get('splits',{})
 intro+=r'\begin{table}[t]\centering\caption{Frozen population counts from the dataset manifest.}\label{tab:dataset-counts}\begin{tabular}{lr}\hline Split & Cases \\\hline'+'\n'
 for split,entry in splits.items():intro+=tex(split)+' & '+str(entry['total'])+r' \\'+'\n'
 intro+=r'\hline\end{tabular}\end{table}'+'\n'
 intro+=r'''The primary protocol retains all 850 original held-out identifiers (250 benign and 600 attack cases).
Stimulus repairs and exact before/after hashes are stored in the lineage manifest. No unapproved 240-case subset is used.
The population is a custom, template-generated bilingual experiment; distinct identifiers do not establish independent real-world tasks or zero semantic overlap.
Each runtime view excludes oracle labels. Artificial per-case secrets exist in private session context, are supplied in protected model context, and are absent from attacker-visible requests.
\subsection{Systems, runtime, and contracts}
The shared harness evaluates Vanilla SLM, Naive RAG, Spotlighting, a Progent-inspired runtime sandbox approximation, a CaMeL-inspired capability-isolation approximation, and HETE.
These approximations do not reproduce the official CaMeL or Progent systems, and no superiority over those reference systems is claimed.
Vanilla has no retrieval channel; the other adapters receive the same retrieved fixture. All receive the same output-contract instruction and protected-context fixture through the runtime-only backend.
The runtime uses local Ollama on Ubuntu 26.04.1 with the root Python 3.12.13 virtual environment. Model digests, quantization, actual request options, and backend token counters are retained in runtime and raw manifests.
The primary model is Qwen2.5-7B; Phi-3.5 uses exactly the same 850 HETE cases \cite{qwen25techreport2024,abdin2024phi3}. Requests use temperature zero, top-p one, seed 42, context 8192, and maximum 384 new tokens. The backend timeout is 180 seconds; the resource guard's 30-second elapsed budget is separately measured and is not an assertion of streaming cancellation.
The revised numeric JSON contract rejects prefixes, suffixes, Markdown fences, duplicate keys, non-finite values, unknown fields, unsupported citations, and claims inconsistent with admitted evidence. Complete task success requires the frozen entity, revenue value and unit, year, citation set, and whole-document schema. Currency scales are B/M/T or explicit base units; omitting a scale means base units, never the expected answer scale. Equivalent units are compared exactly with decimal arithmetic; absolute tolerance is zero.
\subsection{Threat metrics and interventions}
MCR measures the frozen behavioral objective in raw generations. Secret extraction requires the actual per-case protected target, not discussion of a secret or a refusal. Agency E2E success requires a forbidden mock state mutation, not merely a tool name or failed call. Proposed tools undergo capability admission and independent action revalidation; each case begins with fresh mock state.
Resource measurements distinguish attacker input estimates, actual Ollama token consumption, retrievals, tool proposals/executions, and actual agent steps after tool observations. Suppressing a response cannot undo resource consumption. The maximum harness ceiling is 16 agent steps when the resource guard is removed.
The protocol specifies 12 full-size HETE configurations, including individual and paired control removals. Adaptive A2 search specifies six campaigns with 30 seeds each and budget 20; new candidates change request or retrieval content, and observed feedback determines whether the next mutation retains the best candidate or resets. This custom search is reported separately from published adaptive-attack systems \cite{zhan2025adaptive}. A0/A1 are not evaluated. Five stochastic seeds use a frozen 30-case subset with temperature 0.7 and top-p 0.9.
\subsection{Human and external-benchmark scope}
No human reviewers supplied labels. Human validation is false; no human Cohen's kappa or adjudication result is reported. Deterministic judges have limited linguistic coverage and have not been externally validated by humans.
The historical AgentDojo-inspired micro-suite (N=5) is supplementary local material. Actual AgentDojo was not imported or executed; no external-benchmark performance or superiority claim is made.
\subsection{Statistical and artifact methods}
Rates are accompanied by raw counts, explicit denominators, and Wilson intervals \cite{wilson1927probable}. Paired exact two-sided binomial McNemar tests are computed on matching attack IDs \cite{mcnemar1947note}, with Holm correction at family-wise alpha 0.05 \cite{westfall2010multiple}. Scientific validity requires completeness and reconstruction, irrespective of whether outcomes favor HETE. Raw generations, tool mutations, stochastic and adaptive traces, configuration, and summaries are manifested by SHA-256.
\section{Results}\label{sec:results}
'''
 if final:
  summary=load('baseline_comparison.json')
  intro+=r'\begin{table*}[t]\centering\caption{Full 850-case primary comparison. Rates use 600 attacks or 250 benign cases as applicable.}\label{tab:heldout-baselines}\begin{tabular}{lrrrr}\hline System & MCR (count/600) & E2E (count/600) & Complete utility (count/250) & FRR (count/250) \\\hline'+'\n'
  for name,r in summary.items():
   vals=[f"{r[k]['rate']:.2f}\\% ({r[k]['count']}/{r[k]['denominator']})" for k in ('mcr','e2e','utility','frr')]
   intro+=tex(name)+' & '+' & '.join(vals)+r' \\'+'\n'
  intro+=r'\hline\end{tabular}\end{table*}'+'\n'
  intro+='Every value in this table is generated from the frozen raw-evidence summaries. Confidence intervals and full per-class, ablation, adaptive, stochastic, and model-comparison counts are in the supplementary artifact tables.\n'
  model_quality=load('secondary_utility_metrics.json').get('models',{})
  intro+=r'\subsection{Multi-model comparison}'+'\n'+r'\begin{table*}[t]\centering\small\caption{HETE on identical frozen cases. Raw/final invalid are benign whole-output contract failures.}\begin{tabular}{lrrrrrrrrr}\hline Model & Attack N & Benign N & MCR & E2E & Utility & FRR & Raw invalid & Final invalid & Mean ms \\\hline'+'\n'
  for name,r in load('multi_model_results.json').items():
   raw_invalid=model_quality[name]['raw_generation_invalid_contract']
   intro+=tex(name)+f" & {r['attack_cases']} & {r['benign_cases']} & "+' & '.join(f"{r[k]['count']}/{r[k]['denominator']}" for k in ('mcr','e2e','utility','frr'))+f" & {raw_invalid['count']}/{raw_invalid['denominator']} & {r['benign_cases']-r['contract']['count']}/{r['benign_cases']} & {r['latency_mean_ms']:.2f}"+r' \\'+'\n'
  intro+=r'\hline\end{tabular}\end{table*}'+'\n'
  intro+=r'\subsection{Ablations}'+'\n'+r'\begin{table*}[t]\centering\small\caption{Full-size HETE ablations. MCR/E2E use attack N; utility/FRR use benign N.}\begin{tabular}{lrrrrrr}\hline Configuration & Attack N & Benign N & MCR & E2E & Complete utility & FRR \\\hline'+'\n'
  for name,r in load('ablation_results.json').items():
   intro+=tex(name)+f" & {r['attack_cases']} & {r['benign_cases']} & "+' & '.join(f"{r[k]['count']}/{r[k]['denominator']}" for k in ('mcr','e2e','utility','frr'))+r' \\'+'\n'
  intro+=r'\hline\end{tabular}\end{table*}'+'\n'
  intro+=r'\subsection{Exact paired tests}'+'\n'+r'\begin{table}[t]\centering\begin{tabular}{lrr}\hline Baseline & Exact p & Holm p \\\hline'+'\n'
  for row in load('statistical_tests.json').get('pairs',[]):intro+=tex(row['system'])+f" & {row['p_value']:.5e} & {row['holm_p']:.5e}"+r' \\'+'\n'
  intro+=r'\hline\end{tabular}\end{table}'+'\n'
  from render_supplemental_tables import supplemental
  intro+=supplemental(RESULTS,tex)
 else:
  intro+='The full campaign and scientific-validity audit are incomplete. No preliminary subset rates are presented as final evidence. Previous V3.1 numbers and unsupported human/AgentDojo claims have been withdrawn.\n'
 intro+=r'''\section{Discussion}\label{sec:discussion}
The architectural hypothesis is that authority checks can contain model behavior. Its empirical support must be assessed from model compromise, actual egress, mock state changes, complete utility, and latency together. A post-generation rejection does not by itself establish model compromise. Unfavorable outcomes must remain in the evidence; they are not a reason to retune against the held-out set.
\section{Limitations and Threats to Validity}\label{sec:limitations}
This is a custom fixture-based experiment using two quantized local models. The financial fixtures are benchmark ground truth, not a new audit of company filings. Template families and repeated entities limit independence and external generalization. Binomial intervals and paired tests condition on the frozen case population; they do not prove performance on an independent population of novel attacks.
The deterministic language judges can miss paraphrased harmful assertions or mistake contextual mentions for assertions. No human validation or actual AgentDojo evaluation was performed. The inspired baseline approximations, narrow numeric contract, mock tool side effects, and private system-context exfiltration setup restrict the scope of conclusions. Exact protected-token matching does not establish containment of all encoded or transformed leakage. Post-call elapsed-budget detection is not equivalent to hard real-time cancellation of generation.
Two source amendments are part of the evidence history. The first corrected signed-evidence and quantity adjudication before any HETE live case and preserved all earlier generations before rejudging. The second repaired a fail-closed adaptive-candidate collision after the primary and ablation records had frozen; it preserved the first completed adaptive campaign and changed only how a future colliding candidate is deterministically reframed. Both amendments retain before/after source hashes and original records; neither changed a success threshold or removed an observed outcome.
'''
 intro+=f"{operations.get('unique_interruption_count',0)} live backend responses failed the campaign's complete-response admission check. No failed response was admitted as a publication row. The runner preserved every prior checkpoint, recorded each interruption, and resumed only the missing case under unchanged frozen settings. Unscored diagnostics and any model unload/reload observations are retained in the artifact. The rejected response bodies were not retained, so their precise failure modes cannot be reconstructed.\n"
 intro+=r'''
\section{Conclusion}\label{sec:conclusion}
HETE separates language-model text from trusted execution authority. The V3.2 artifact is designed to test this separation with complete raw evidence and honest scope. Final submission requires the scientific-validity gate, artifact/manuscript audit, and clean LaTeX/BibTeX build; no perfect security or utility outcome is presumed.
'''
 (PAPER/'v3_2_evidence.tex').write_text(intro)
 main=PAPER/'_47.1_UIR_ZTA.tex';original=DOC/'audit/manuscript_before_closure.tex'
 if not original.exists():original.write_bytes(main.read_bytes())
 s=original.read_text()
 a=s.index(r'\begin{abstract}');b=s.index(r'\end{abstract}',a)
 abstract=r'''\begin{abstract}
HETE treats language models as untrusted transformation components and uses a typed Universal Intermediate Representation to bind evidence and execution authority outside the model. The V3.2 scientific-validity protocol evaluates model compromise, trusted effects, exact benign-task completion, and resource consumption on all 850 custom held-out cases. It compares six shared-harness systems, including explicitly scoped CaMeL-inspired and Progent-inspired approximations, and specifies identical-case local Ollama model comparisons, full-size ablations, and budgeted adaptive search. Human validation and actual public AgentDojo results are not claimed. '''
 abstract+=('Frozen empirical counts are reported with reconstructible raw traces and exact paired tests. ' if final else 'Full execution and independent validation are pending; this draft is not final publication evidence. ')
 s=s[:a]+abstract+s[b:]
 # Withdraw complete paragraphs containing unsupported introductory empirical claims.
 for prefix in ('The evaluation protocol is specifically designed','Across comprehensive empirical evaluations'):
  start=s.index(prefix);end=s.index('\n\n',start)
  s=s[:start]+'The V3.2 protocol and its current evidence status are specified in Section~\\ref{sec:methodology}; previous preliminary claims are superseded.\n'+s[end:]
 start=s.index('    We introduce the \\texttt{llm\\_security\\_v3} benchmark');end=s.index('\n',start)
 s=s[:start]+'    We provide an auditable full-population protocol with deterministic behavioral oracles and explicitly scoped inspired baseline approximations.'+s[end:]
 s=s.replace('demonstrating empirically that even when an LLM is manipulated or aligned imperfectly, deterministic downstream gates intercept unauthorized actions and contain malicious effects.', 'testing whether downstream gates contain manipulated model behavior using distinct model and system outcome measures.')
 s=s.replace('public benchmark performance, multi-model evaluation','the scope of supplementary suites, multi-model evaluation')
 a=s.index(r'\section{Experimental Methodology}');b=s.index(r'\section*{Acknowledgment}',a)
 s=s[:a]+r'\input{v3_2_evidence.tex}'+'\n\n'+s[b:]
 s=s.replace('Rigorous Leakage-Free Benchmark and Multi-Defense Evaluation.', 'Auditable Benchmark and Scoped Multi-Defense Evaluation.')
 s=s.replace('Slutzky \\etal{} proposed', 'Debenedetti \\etal{} proposed')
 s=s.replace('slutzky2025camel', 'debenedetti2025camel').replace('yang2024progent', 'shi2025progent')
 start=s.index(r'    \item \textbf{Input Demarcation and Encoding:}')
 end=s.index(r'\end{itemize}',start)
 s=s[:start]+r'''    \item \textbf{Input Demarcation and Encoding:} Spotlighting marks untrusted input using delimiting, datamarking, or encoding \cite{hines2024spotlighting}. Our local adapter implements delimiter-based framing only; it is not a reproduction of every published variant.
    \item \textbf{External Privilege Enforcement:} CaMeL separates control and data flows and checks capabilities when tools are called \cite{debenedetti2025camel}. Progent expresses tool privileges using symbolic policy rules and checks proposed calls deterministically \cite{shi2025progent}. The local adapters in our experiment approximate selected mechanisms; they do not reproduce either reference implementation.
'''+s[end:]
 start=s.index(r'\begin{table*}[t]',s.index(r'\subsection{Zero Trust, Structured Security Boundaries, and HETE}'))
 end=s.index(r'\section{Threat Model and Security Requirements}',start)
 s=s[:start]+r'''\begin{table*}[t]
\centering
\caption{Published mechanisms and the scope of local evaluated adapters; no absence-of-feature or official-system superiority claim is inferred.}
\label{tab:rw-taxonomy}
\begin{tabularx}{\textwidth}{lXX}
\toprule Approach & Published mechanism / design & Evaluated local scope \\
\midrule
Spotlighting \cite{hines2024spotlighting} & Untrusted-input transformations & Delimiter framing in a single prompt \\
CaMeL \cite{debenedetti2025camel} & Control/data flow separation and capabilities & Prompt labels and tool-capability membership \\
Progent \cite{shi2025progent} & Deterministic privilege-policy checks & Fixed tool-name allow-list \\
HETE & Typed UIR and external enforcement & Custom fixture pipeline, signed evidence, output validation and mock actions \\
\bottomrule
\end{tabularx}
\end{table*}

Table~\ref{tab:rw-taxonomy} distinguishes published designs from the much narrower adapters evaluated here. The architectural invariants below state intended enforcement conditions; the finite experiment is not a proof of universal security.

'''+s[end:]
 s=s.replace('Step metrics, token counts & Budget signal & \\textbf{Yes} (terminates runaway tasks) & Hard termination',
             'Step metrics, token counts & Budget signal & \\textbf{Yes} (stops at measured checkpoints) & Fail-closed checkpoint')
 s=s.replace('publishes the complete TCB audit matrix', 'publishes the implementation TCB inventory used in this evaluation')
 s=s.replace('Verified by: \\texttt{test\\_', 'Exercised by regression test: \\texttt{test\\_')
 s=s.replace('This is an architectural guarantee enforced deterministically by the \\texttt{CapabilityGate} and \\texttt{SecurityPolicyEngine}',
             'This is an intended architectural invariant exercised by the \\texttt{CapabilityGate} and \\texttt{SecurityPolicyEngine}')
 s=s.replace('Token, retrieval, tool, recursion, and time budgets are enforced independently of model compliance.',
             'Token, retrieval, tool, recursion, and elapsed-time budgets are checked independently of model compliance at recorded enforcement points; elapsed generation is detected after the backend call.')

 main.write_text(s)
 (DOC/'MANUSCRIPT_STATUS.md').write_text('# Manuscript evidence status\n\n'+status+'\n\nGenerated sections: Abstract, Experimental Methodology, Results, Discussion, Limitations, Conclusion. Architecture and bibliography retained. Source: `audit/render_evidence.py`.\n')

if __name__=='__main__':render('--final' in sys.argv)
