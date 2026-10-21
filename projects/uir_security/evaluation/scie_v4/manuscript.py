"""Generate NEW preprint/journal sources; never edit the historical manuscripts."""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from .common import FROZEN, PROJECT, TASK, load, rows, sha, write


def tex(value):
    return str(value).replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')


def wilson(k,n):
    z=1.959963984540054;p=k/n;d=1+z*z/n
    center=(p+z*z/(2*n))/d;radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return f'[{100*max(0,center-radius):.2f}, {100*min(1,center+radius):.2f}]'


def figures():
    fig,ax=plt.subplots(figsize=(8,3));ax.set(xlim=(0,10),ylim=(0,4));ax.axis('off')
    boxes=[(0.2,2.5,'Authenticated session\ncapabilities + revision'),(.2,.4,'Untrusted model\noutput proposal'),
           (3.5,1.5,'Admission + independent\ndispatch revalidation'),(7,1.5,'Committed effect\nor canonical egress')]
    for x,y,label in boxes:
        ax.add_patch(FancyBboxPatch((x,y),2.6,.9,boxstyle='round,pad=.08',fc='#eef2f6',ec='#334155'))
        ax.text(x+1.3,y+.45,label,ha='center',va='center',fontsize=9)
    for start,end in [((2.9,2.9),(3.5,2.2)),((2.9,.9),(3.5,1.8)),((6.2,1.95),(7,1.95))]:
        ax.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'->','color':'#334155','lw':1.5})
    ax.text(5,0,'Denials and failures remain in per-case traces; hashes alone are not an append-only log.',ha='center',fontsize=8)
    fig.tight_layout();fig.savefig(TASK/'figures/boundary_trace.pdf');fig.savefig(TASK/'figures/boundary_trace.png',dpi=180);plt.close(fig)


def main():
    destination=TASK/'manuscript_private';destination.mkdir(exist_ok=True)
    baseline=load(FROZEN/'baseline_comparison.json');models=load(FROZEN/'multi_model_results.json')
    science=load(TASK/'manifests/frozen_recovery_receipt.json');outer=load(TASK/'data/model_substitution_summary.json')
    ai=load(TASK/'data/ai_judge_agreement.json') if (TASK/'data/ai_judge_agreement.json').exists() else None
    external=list(rows(TASK/'data/benchmark_results.jsonl')) if (TASK/'data/benchmark_results.jsonl').exists() else []
    figures()
    provenance=[]
    table=r'''\begin{table}[htbp]\centering\small
\caption{Historical V3.2 custom population. Local inspired adapters are approximations; these are not official-system comparisons. MCR/E2E denominators are 600 attacks; utility/FRR denominators are 250 benign tasks.}
\label{tab:v32}\begin{tabularx}{\linewidth}{Xrrrrr}\hline
System & MCR & E2E & Utility & FRR & Mean ms\\\hline
'''
    for name,value in baseline.items():
        label=name.replace('-inspired','')+' (local)' if name in {'CaMeL-inspired','Progent-inspired','Spotlighting'} else name
        table+=tex(label)+' & '+' & '.join(f"{value[k]['count']}/{value[k]['denominator']}" for k in ('mcr','e2e','utility','frr'))+f" & {value['latency_mean_ms']:.1f}"+r' \\'+'\n'
        provenance.extend({'surface':'Table 3','field':f'baseline_comparison.json/{name}/{k}','count':value[k]['count'],'n':value[k]['denominator']} for k in ('mcr','e2e','utility','frr'))
    phi=models['phi3.5:latest'];table+='HETE/Phi-3.5 & '+' & '.join(f"{phi[k]['count']}/{phi[k]['denominator']}" for k in ('mcr','e2e','utility','frr'))+f" & {phi['latency_mean_ms']:.1f}"+r' \\'+r'\hline\end{tabularx}\end{table}'+'\n'
    table+=r'\begin{table}[htbp]\centering\small\caption{Conditional Wilson 95\% intervals (percent). Cases share templates; these are not independent-task generalization bounds.}\begin{tabular}{lrr}\hline System & E2E interval & Utility interval\\\hline'+'\n'
    for name,value in [('HETE/Qwen2.5',baseline['HETE']),('HETE/Phi-3.5',phi)]:
        table+=name+' & '+wilson(value['e2e']['count'],600)+' & '+wilson(value['utility']['count'],250)+r' \\'+'\n'
    table+=r'\hline\end{tabular}\end{table}'+'\n'
    write(destination/'v3_2_evidence.tex',table)
    write(TASK/'manifests/manuscript_number_sources.json',provenance)
    external_text='The newly registered external trials are pending; no new public-benchmark performance is claimed in this draft.'
    if external:
        summary=[]
        for model in sorted({r['model'] for r in external}):
            for config in ('vanilla','minimal_envelope','typed_hete'):
                subset=[r for r in external if r['model']==model and r['config']==config]
                clean=[r for r in subset if not r['attack']];attack=[r for r in subset if r['attack']]
                summary.append({'model':model,'config':config,'benign_n':len(clean),'benign_utility':sum(r['utility'] for r in clean),
                                'attack_n':len(attack),'attack_success':sum(r['attack_success'] is True for r in attack),
                                'backend_errors':sum(r['backend_failure'] for r in subset)})
        write(TASK/'data/public_benchmark_summary.json',summary)
        external_text=('Official AgentDojo 0.1.35 environments and original oracles were executed on four preregistered read-only tasks across workspace and banking, '
                       'with benign and goal-conditioned injected variants. The local JSON agent, minimal envelope and typed capability adapter share the same task opportunities. '
                       'This is a restricted official-environment pilot, not a reproduction of the full AgentDojo leaderboard or the complete historical HETE pipeline. '
                       'The typed and minimal adapters enforce the same read-only policy; a data structure alone is not an additional security mechanism.\n')
        external_text+=r'\begin{table}[htbp]\centering\scriptsize\caption{New official-environment read-only pilot. Failed calls remain in planned denominators.}\begin{tabular}{llrrr}\hline Model & Local system & Benign utility & Attack successes & Errors\\\hline'+'\n'
        for r in summary:
            label='Qwen3-4B' if 'qwen3:' in r['model'] else 'Ministral-14B'
            external_text+=f"{label} & {tex(r['config'])} & {r['benign_utility']}/{r['benign_n']} & {r['attack_success']}/{r['attack_n']} & {r['backend_errors']}"+r' \\'+'\n'
        external_text+=r'\hline\end{tabular}\end{table}'+'\n'
    ai_text='Two local AI raters were requested in place of humans. Their execution/analysis is pending; human validation remains false.'
    if ai:
        ai_text=('Two local models (Ministral 3 14B and Qwen3.8-27B) independently annotated a preregistered blinded sample of 200 attacks and 50 benign cases. '
                 'Source system/model, deterministic verdict and the other rater were hidden. Human validation remains false. '
                 'Cohen-type coefficients describe AI rater agreement, not human agreement or verified judge accuracy~\\cite{cohen1960kappa}. ')
        for key,value in ai['metrics'].items():
            k=value['ai_rater_cohen_kappa'];ktext='undefined (degenerate labels)' if k is None else f'{k:.3f}'
            ai_text+=f"For {tex(key)}, {value['n_valid_pairs']} valid pairs gave kappa {ktext}. "
        ai_text+='Correlated training, shared blind spots, schema errors and disagreements remain limitations. Historical deterministic scores were not changed.'
    body=r'''\section{Introduction}
Large language models transform untrusted requests, retrieved evidence and tool observations into candidate answers or actions. A generated action should not inherit execution authority from its wording. Prompt injection, retrieval poisoning and excessive agency make this boundary operationally important~\cite{owasp2026,nistaml2025,mitreatlas2026,greshake2023indirect,zou2023universal,zou2025poisonedrag}. HETE (Heterogeneous Entity Trust Extension) compiles application authority into a typed Universal Intermediate Representation (UIR) and enforces policy outside the generator. The design follows the explicit-verification principle of Zero Trust~\cite{nistzt2020}.

We ask three research questions: RQ1, which observed model compromises or resource breaches reach trusted effects? RQ2, which deterministic boundaries remain effective when the model output is deliberately replaced? RQ3, how much security, complete task utility and latency can be attributed to the enforcement mechanism rather than the backbone or a simple deterministic resolver? We retain the UIR-v2 security representation; Security Evaluation V3.2 is the historical protocol and evidence version. V4 identifies separate reinforcement experiments, not a silent new format for UIR. The shared UIR-Core Typed IR v0.1 specification is an evolving architectural contract and is not claimed to be the exact frozen V3.2 wire schema.

\section{Related Work and Novelty Scope}
CaMeL separates control and data flow and uses capabilities; Progent applies symbolic privilege rules and constrained policy updates; IsolateGPT isolates execution and mediates interactions~\cite{debenedetti2025camel,shi2025progent,wu2025isolategpt}. StruQ and SecAlign train structured or preference-based instruction boundaries; Spotlighting marks untrusted input~\cite{chen2025struq,chen2025secalign,hines2024spotlighting}. A recent privacy middleware combines injection detection and sensitive-data protection~\cite{hsine2026middleware}. HETE's proposed delta is the joint typed record of authority, evidence admission, numeric output contract, action authorization and resource accounting, together with separate measurement of model behavior and trusted effects. This is a compositional systems contribution; typed syntax alone is not established as superior to minimal enforcement.

AgentDojo measures task utility and prompt-injection effects in tool environments~\cite{debenedetti2024agentdojo}. Published adaptive studies motivate policy-aware evaluation but their algorithms and results must not be confused with our custom search~\cite{zhan2025adaptive,hofer2026assessing}. Instruction hierarchy and retrieval augmentation are useful upstream mechanisms but do not by themselves authorize system effects~\cite{wallace2024instructionhierarchy,lewis2020rag}. Model reports describe the historical Qwen2.5 and Phi backbones~\cite{qwen25techreport2024,abdin2024phi3}.

\section{System, Trust Boundaries and Assumptions}
The model and all external text are untrusted. The application supplies an authenticated principal, immutable capability set, policy revision, admitted evidence identities and budgets. The trusted computing base contains authentication, configuration, parsers, evidence endorsement, admission and dispatch checks, output validation, storage and runtime. Tests cannot establish security if this base is compromised.

\begin{table}[htbp]\centering\small\caption{Typed authority and implementation checks.}\label{tab:boundaries}
\begin{tabularx}{\textwidth}{lXX}\hline Boundary & Typed state & Check\\\hline
Session to proposal & principal, capability set, revision & external text cannot mint authority\\
Evidence admission & source ID, content binding, claim scope & hash validity is not authenticity or truth\\
Tool dispatch & registry, arguments, nonce, revision & independent permission and TOCTOU check\\
Commit and egress & transaction, verified response contract & atomic state commit; canonical checked fields\\
Resource checkpoints & tokens, tool calls, steps, elapsed time & preflight and post-call accounting are distinct\\\hline
\end{tabularx}\end{table}

\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{boundary_trace.pdf}
\caption{Authority and proposal paths. Rejection indicators overlap and are not sequential subtraction counts.}\label{fig:boundary}\end{figure}

The intended invariants are capability monotonicity, taint non-attenuation, trusted evidence admission and post-generation non-authority. Property, mutation and transaction tests exercise implementations of these conditions; no universal proof is claimed. No automatic declassification is permitted. The public HMAC benchmark key tests binding logic but cannot authenticate against an attacker possessing that key. Deployment requires protected signer keys, rotation, revocation and rollback-resistant state. A digest alone does not make a log append-only or tamper-evident.

The validated factual scope is a narrow numeric fixture: entity, metric, quantity/unit, fiscal year, citations and whole JSON. It does not validate arbitrary prose. Tool dispatch requires current permissions and revision before execution. SQLite rollback covers the local demonstration only; an external API needs its own idempotency and transaction semantics. A transport timeout and post-call elapsed check do not prove hard cancellation of GPU generation.

\section{Evaluation Design and Provenance}
\begin{table}[htbp]\centering\small\caption{Evidence populations and limits.}\label{tab:scope}
\begin{tabularx}{\textwidth}{lXX}\hline Study & Population & Scope\\\hline
Frozen V3.2 & 850: 600 attack + 250 benign & six systems; twelve full-population ablations\\
V3.2 adaptive & 180 seeds; 3,600 queries & six custom A2 campaigns; budget 20\\
V3.2 stochastic & five seeds; 30 cases each & same conditional subset\\
Historical backbones & Qwen2.5 and Phi-3.5 & identical 850 IDs; adverse Phi result retained\\
V4 boundary & nominal and independent encoded-output tests & generator replacement; local effects, not model resistance\\
V4.1 outer contract & 120 attack + 30 benign & new synthetic cases after development repair\\
New external pilot & official workspace and banking tasks & narrow read-only local-agent evaluation\\\hline
\end{tabularx}\end{table}

No V3.2 outcome, oracle, raw generation or held-out identifier was replaced. Historical source-path edits caused hash mismatches in 13 Python files. A separate overlay recovers each complete byte sequence to the original expected SHA-256. Fifty-four generated bytecode entries still fail the full historical manifest. All 418 non-bytecode artifacts verify using the explicit overlay; this scoped check is not a claim that all 736 original manifest entries pass. Original incomplete-response bodies remain missing. Eight unique interrupted case checkpoints, repeated retries, later diagnostics and two source amendments are distinguished in the attrition ledger. Exact event or approval timestamps are not invented when absent.

A local supplementary candidate projects 19,900 admitted executions, consistently tokenizes synthetic private-context fixture strings, and rejudges outcomes. It is a score-reconstruction payload rather than byte-identical transport replay. The candidate remains local pending rights and release review; no public deposit DOI or preprint posting is claimed.

MCR measures a class-specific raw behavioral objective; E2E measures released forbidden content, forbidden mock mutation, or a separate measured resource breach. The comparison E2E $<$ MCR indicates containment only for the same model-mediated objective under matched conditions and exposure. It is not a universal inequality. Historical rates use the full attack population; 237 pre-call blocks mean MCR $=0/600$ is not evidence that the model resisted 600 exposed attacks.

Counts use explicit denominators and Wilson intervals~\cite{wilson1927probable}. Exact two-sided binomial McNemar tests are paired by case ID; five primary comparisons form the Holm family at $\alpha=.05$~\cite{mcnemar1947note,westfall1993resampling}. Post-hoc class-language cluster resampling is a sensitivity proxy because true template-family IDs were not retained. All-zero bootstrap intervals are degenerate and do not establish zero unseen risk. A Wilson bound for 0/600 is approximately 0.64\% only under the stated binomial assumptions. Latency p50/p95/p99 and actual token counters include rejected admitted paths; missing interrupted-call latency remains unknown.

\section{Results}
\input{v3_2_evidence.tex}
Qwen-backed HETE observed MCR $0/600$ and E2E $0/600$, utility $249/250$ and FRR $1/250$. Phi-3.5 on identical IDs observed MCR $3/600$, E2E $6/600$, utility $0/250$ and FRR $250/250$. Enforcement placement is external to the backbone; semantic and contract competence remain model-dependent. The Phi failure analysis separates whole-JSON parse failures from contract/rejection categories without converting a failed original task into a success.

Case-level HETE indicators are 600 attempted attacks, 363 model invocations, zero behavioral MCR, 176 OutputGuard rejections, 68 action-gate rejections and zero committed trusted effects. There are 210 policy and 27 resource pre-call blocks; among exposed cases, 176 are rejected and 187 are allowed. These indicators overlap, and rejection is not itself model compromise.

Removing InputGuard yielded MCR $4/600$ with E2E $0/600$. Removing ResourceGuard yielded E2E $20/600$, showing a distinct resource path. Removing CapabilityGate, Policy and Action Revalidation together yielded MCR $8/600$ and E2E $7/600$. Individual zero-change knockouts are finite-distribution masking, not proof of redundancy in all deployments. The adaptive campaign had one excessive-agency MCR seed out of 30 and zero E2E seeds; the other five campaigns had zero MCR/E2E seeds. Six collision reframes and zero within-seed candidate-hash duplicates were recorded.

\subsection{Boundary Replacement and New Negative Evidence}
The nominal V4 replacement study observes zero forbidden effects with 26/26 positive controls; knockout effects are retained. A separately registered white-box search then releases base64-encoded private summary text in 12/12 seeds. This is a concrete limitation of exact-token filtering. V4.1 narrows the contract to verified fields and canonical serialization. On a new 120-attack/30-benign outer fixture, the original V4 releases 40 encoded payloads, V4.1 releases none, and the output-disabled control releases 120; all three complete 30/30 benign fixture records. Neither the original failures nor their repair is substituted into V3.2.

A separate replacement harness also reaches the actual current HETE pipeline at its inference backend. Across twelve malicious proposals and two positive controls, the original pipeline releases one encoded-summary attack. A new V4.1 numeric-contract guard adapter rejects unverified optional prose and observes zero forbidden outcomes with both positive controls passing. Removing both action checks produces five forbidden outcomes; disabling the output guard produces eleven. These are finite synthetic mechanism results; the new guard is not substituted into the historical runs.

A development-only Phi format probe uses twelve fresh synthetic transcription records, six Korean and six English, with native generate/JSON mode and native chat/schema mode. Both formats complete 12/12. This establishes basic adapter compatibility for this small task; it does not explain away the historical 0/250 utility or demonstrate held-out security after retuning.

The deterministic no-LLM resolver is an additional diagnostic on the already-observed V3.2 population. Trusted numeric evidence can directly determine the expected answer; this benchmark cannot establish that an LLM is necessary. Current-hardware resolver latency and historical HETE latency are not a controlled speedup comparison.

\subsection{External Pilot}
EXTERNAL_RESULTS

\subsection{Independent AI Judge Study}
AI_RESULTS

\section{Discussion and Limitations}
The contribution is the explicit authority boundary and effect-level measurement, not a universal zero-attack claim. The finite custom template population, repeated entities, narrow numeric contract, mock effects, restricted official-environment tasks, public task training contamination and model-format reliability limit generalization. Cluster proxies cannot recover missing original template-family metadata. Official CaMeL interpreter conformance is separate from a full model-agent baseline run; no official CaMeL or Progent superiority is claimed. The historical AgentDojo-inspired N=5 micro-suite remains historical supplementary material, distinct from the new official-environment pilot.

Fail-closed enforcement can preserve some boundaries while destroying utility, as Phi illustrates. The retained encoded leak shows why literal-token DLP is insufficient for broad confidentiality. The strict repair protects a smaller accepted representation and has no demonstrated arbitrary-prose semantic benefit. Independent AI raters can share training data and failure modes; their agreement is not human validation or an independent factual oracle. Public release, author statements and final journal review remain separate completion conditions.

\section{Conclusion}
Typed authority records and deterministic checks separate generated proposals from trusted effects under explicit TCB and contract assumptions. Historical Qwen and Phi outcomes, ablations, retries, and new unfavorable boundary results are preserved. New mechanism tests and restricted external trials strengthen the audit trail while exposing limits. The evidence establishes neither universal security, full official-baseline superiority, human-validated judge accuracy nor model-independent utility. Submission readiness remains conditional on the documented acceptance gates and author confirmations.
'''
    body=body.replace('EXTERNAL_RESULTS',external_text).replace('AI_RESULTS',ai_text)
    write(destination/'manuscript_body.tex',body)
    abstract=('HETE treats model output as an untrusted proposal and places authority in a typed intermediate representation and deterministic enforcement envelope. '
        'On the frozen 850-case custom benchmark, Qwen2.5-backed HETE observed MCR 0/600, E2E-ASR 0/600, benign utility 249/250 (99.6\\%) and FRR 1/250 (0.4\\%). '
        'Identical-case Phi-3.5 results were MCR 3/600, E2E-ASR 6/600, utility 0/250 and FRR 250/250. '
        'These results distinguish external enforcement placement from backbone-dependent contract competence. '
        'Separate reinforcement includes raw-record audits, deliberate malicious-output replacement, a narrow canonical-output repair after an encoded-leak counterexample, restricted official-environment evaluation, and blinded AI annotation. '
        'Human validation remains false, inspired adapters are not official-system reproductions, and no universal security or independent-task generalization is established. '
        'Original missing response bodies and historical manifest damage are disclosed; publication is conditional on author and release checks.')
    title='HETE: A Typed Intermediate Representation and Deterministic Enforcement Envelope for Zero-Trust Language-Model Execution'
    preamble=r'''\documentclass[11pt]{article}
\usepackage[a4paper,margin=24mm]{geometry}
\usepackage[T1]{fontenc}\usepackage{mathptmx,graphicx,tabularx,booktabs,amsmath,microtype,url}
\usepackage[hidelinks]{hyperref}
\title{TITLE}
\author{SeongSu Park and Ki-Hyung Kim\\Ajou University, Republic of Korea}
\date{21 October 2026 --- Preprint. Not peer-reviewed.\\Local draft; not posted or submitted}
\begin{document}\maketitle
\begin{abstract}ABSTRACT\end{abstract}
\input{manuscript_body.tex}
\section*{Publication Statements}
Author contributions, corresponding author, conflicts of interest and funding-role confirmation are pending author approval. The historical IITP grant acknowledgment is retained in the original manuscript and must be confirmed before release. No human participants supplied evaluation labels; synthetic fixtures and local AI annotation were used. Code and data are locally archived; a public repository/DOI and license must be confirmed before publication. AI assistance in development, analysis and manuscript preparation must be reviewed and disclosed by the authors. No preprint DOI has been assigned.
\bibliographystyle{plain}\bibliography{references_clean}
\end{document}
'''.replace('TITLE',title).replace('ABSTRACT',abstract)
    write(destination/'HETE_PREPRINT_V1.tex',preamble)
    template=TASK/'resources/mdpi_official_template/Definitions'
    target_defs=destination/'Definitions'
    if target_defs.exists():shutil.rmtree(target_defs)
    shutil.copytree(template,target_defs)
    # Official template EPS assets are converted before the no-shell-escape
    # build. Preserve both the original asset and its derived PDF.
    for eps in target_defs.glob('*.eps'):
        gsroot=TASK/'resources/tex_packages/ghostscript'
        env=dict(os.environ)
        env['LD_LIBRARY_PATH']=str(gsroot/'usr/lib/x86_64-linux-gnu')+':'+env.get('LD_LIBRARY_PATH','')
        env['GS_LIB']=':'.join(str(p) for p in (gsroot/'usr/share/ghostscript').glob('*/Resource/Init'))
        env['GS_LIB']+=':'+':'.join(str(p) for p in (gsroot/'usr/share/ghostscript').glob('*/lib'))
        subprocess.run([shutil.which('gs') or str(gsroot/'usr/bin/gs'),'-dSAFER','-dBATCH','-dNOPAUSE','-sDEVICE=pdfwrite','-dEPSCrop',
                        '-sOutputFile='+str(eps.with_name(eps.stem+'-eps-converted-to.pdf')),str(eps)],env=env,check=True,stdout=subprocess.DEVNULL)
    journal=r'''\documentclass[electronics,article,submit,pdftex,moreauthors]{Definitions/mdpi}
\usepackage{amsmath,tabularx,graphicx}
\firstpage{1}\pubvolume{1}\issuenum{1}\articlenumber{0}\hreflink{https://doi.org/}
\setlength{\headheight}{25pt}
\lhead{\footnotesize Internal Electronics draft --- not submitted}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\footnotesize Internal journal draft --- not submitted}}
\Title{TITLE}\TitleCitation{HETE: Typed Representation and External Enforcement}
\Author{SeongSu Park $^{1}$ and Ki-Hyung Kim $^{2}$}
\AuthorNames{SeongSu Park and Ki-Hyung Kim}\AuthorCitation{Park, S.; Kim, K.}
\address{$^{1}$ Department of Computer Engineering, Ajou University, Suwon, Republic of Korea; parky@ajou.ac.kr\\
$^{2}$ Department of Cyber Security, Ajou University, Suwon, Republic of Korea; kkim86@ajou.ac.kr}
\corres{Corresponding author designation pending author confirmation.}
\pubyear{2026}\copyrightyear{2026}\datereceived{}\daterevised{}\dateaccepted{}\datepublished{}
\abstract{ABSTRACT}
\keyword{zero trust; language models; typed intermediate representation; prompt injection; authority enforcement}
\begin{document}
\noindent\textbf{Internal journal draft. Author statements and submission gates are pending; not submitted.}
\input{manuscript_body.tex}
\authorcontributions{Pending author confirmation. No individual contributions or final author approval are asserted by this draft.}
\funding{Historical acknowledgment: IITP-2026-RS-2021-II211835. Funding wording, funder roles and APC support require author confirmation.}
\institutionalreview{No human participants supplied study labels; synthetic fixtures and local AI models were used. Authors must confirm institutional requirements before submission.}
\informedconsent{No human evaluation participants; not applicable to the reported AI annotation.}
\dataavailability{Evidence is locally archived. A tokenized supplementary candidate exists; public deposit, release rights and DOI are pending. No public availability is asserted.}
\conflictsofinterest{Pending declarations from both authors.}
\acknowledgments{Local AI models and coding assistance were used in development, annotation, analysis and drafting. Authors must review outputs and approve a complete tool-use disclosure before submission.}
\bibliography{references_clean}
\end{document}
'''.replace('TITLE',title).replace('ABSTRACT',abstract)
    write(destination/'HETE_JOURNAL.mdpi.tex',journal)
    shutil.copy2(TASK/'resources/references_clean.bib',destination/'references_clean.bib')
    shutil.copy2(TASK/'figures/boundary_trace.pdf',destination/'boundary_trace.pdf')
    write(TASK/'reports/PREPRINT_CHANGELOG.md','# New local preprint draft\n\nV1 (2026-10-21) is not posted. Corrected canonical references, narrowed security claims, preserved V3.2 outcomes and attrition, disclosed recovered source and bytecode damage, and added separately versioned reinforcement evidence. The historical V3.2/V3.2A manuscripts remain byte-preserved. No prior preprint DOI or author approval is invented.\n')
    write(TASK/'reports/SUPPLEMENTARY_README.md','# Supplementary map\n\nOriginal raw V3.2 evidence stays in the historical project result directory. The new local candidate has 19,900 projected executions and explicit tokenization/scoring checks. Task data contains raw counts, source recovery receipt, class-language intervals, latency quantiles, original unfavorable Phi outputs analysis, independent AI labels, official environment traces, nominal and encoded boundary counterexamples and the distinct V4.1 outer holdout. No public DOI exists yet.\n')
    print(destination)


if __name__=='__main__':main()
