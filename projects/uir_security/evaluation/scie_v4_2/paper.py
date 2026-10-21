"""New, evidence-generated generic and Electronics manuscripts; old V4 untouched."""
from .common import *

import csv
import os
import re
import shutil
import subprocess
import zipfile

os.environ.setdefault('MPLCONFIGDIR',str(TASK/'resources/matplotlib_cache'))
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['pdf.fonttype']=42
matplotlib.rcParams['ps.fonttype']=42
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

TITLE='HETE: Typed Authority and Auditable Enforcement for Tool-Using Language-Model Agents'
ABSTRACT='''Language-model agents can propose unauthorized actions after reading adversarial content. We present HETE, an application-controlled typed representation separating generated proposals from capability-bearing execution while recording evidence, policy revisions, approvals, effects, and output contracts. A reference interpreter compiles proposals into proof-bound approved actions and revalidates authority before dispatch. We preserve historical evaluations and compare equivalent minimal and typed guards in official AgentDojo environments with local agents. Twelve tasks across three domains, including authorized writes, yield 432 logical executions over two backbones and sixty task-attack pairings. Physical inference requests and cached logical executions are distinguished. The guards have identical observed outcomes: Qwen3 completes 4/12 benign tasks with 0/60 attack successes; Ministral completes 7/12 with 0/58 scored successes and two unknown attack outcomes. Historical Phi-3.5 utility remains 0/250. Encoded-output tests expose original leakage; narrower contracts block tested releases but reject legitimate explanatory prose. Bounded-state and bilingual workflow tests supplement these findings. Typed records provide explicit execution obligations and audit linkage, with no demonstrated incremental security or utility over equivalent policy checks. General confidentiality, production key management, and generalization remain unestablished.'''
KEYWORDS='secure AI deployment; prompt injection; typed intermediate representation; tool-using language-model agents; capability enforcement; zero trust'


def tx(value):return str(value).replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')
def label(model):return 'Qwen3-4B' if 'qwen3:' in model else 'Ministral-14B'
def csvrows(path):return list(csv.DictReader(Path(path).open()))


def figures(compact):
    fig,ax=plt.subplots(figsize=(9,4));ax.set(xlim=(0,12),ylim=(0,5));ax.axis('off')
    boxes=[(.2,3.5,3.1,.9,'Application-owned authority\nprincipal, capabilities, revision, evidence'),
           (.2,.7,2.7,1,'Untrusted generator\nProposedAction JSON'),
           (3.5,.7,2.5,1,'Typed compiler\nApprovedAction + proof'),
           (6.6,.7,2.2,1,'Current-state\nrevalidation'),
           (9.4,.7,2.3,1,'Executor / commit\ncanonical egress')]
    for x,y,w,h,text in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',fc='#edf2f7' if y>3 else '#f7fafc',ec='#334155'))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=8.6)
    for a,b in [((2.95,1.2),(3.4,1.2)),((6.05,1.2),(6.5,1.2)),((8.9,1.2),(9.3,1.2)),((3.4,3.7),(4.7,1.85)),((3.4,3.9),(7.5,1.85))]:
        ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','lw':1.2,'color':'#334155'})
    ax.text(6,.1,'Proof / revision / ownership / evidence / nonce checks precede effects. Host and authority store remain trusted.',ha='center',fontsize=8)
    fig.tight_layout();fig.savefig(TASK/'figures/typed_boundary.pdf');fig.savefig(TASK/'figures/typed_boundary.png',dpi=600);plt.close(fig)
    from .analysis import wilson
    fig,axes=plt.subplots(1,2,figsize=(9,4))
    ordered=sorted(compact,key=lambda r:(r['model'],r['config']))
    names=[]
    for i,r in enumerate(ordered):
        names.append(label(r['model'])+'\n'+r['config'][:2]);color={'C0':'#a1a1aa','C1':'#60a5fa','C2':'#2563eb'}[r['config'][:2]]
        for j,(k,n) in enumerate([(r['benign_utility'],r['benign_n']),(r['official_attack_success'],r['attack_scored_n'])]):
            p=100*k/n;lo,hi=wilson(k,n);axes[j].bar(i,p,color=color,width=.65)
            axes[j].errorbar(i,p,yerr=[[p-100*lo],[100*hi-p]],fmt='none',color='#334155',capsize=3)
            axes[j].text(i,max(p,1)+3,f'{k}/{n}',ha='center',fontsize=8)
    for ax,title in zip(axes,['Benign complete utility','Official goal success (scored attacks)'],strict=True):
        ax.set(xticks=range(len(names)),xticklabels=names,ylabel='Percent',title=title,ylim=(0,110 if ax is axes[0] else 65))
        ax.tick_params(axis='x',labelsize=7);ax.grid(axis='y',alpha=.2)
    fig.suptitle('Conditional Wilson intervals; correlated tasks and unknown outcomes limit inference',fontsize=9)
    fig.tight_layout();fig.savefig(TASK/'figures/security_utility.pdf');fig.savefig(TASK/'figures/security_utility.png',dpi=600);plt.close(fig)


def main():
    compact=load(TASK/'data/EXTERNAL_COMPACT.json')
    bilingual=list(rows(TASK/'experiments/multimodel_utility/bilingual_runs.jsonl'))
    if len(bilingual)!=64:raise ValueError('All 64 bilingual logical trials required before final manuscript')
    official=list(rows(TASK/'experiments/official_baseline/OFFICIAL_AGENT_CASE_TRACE_003.jsonl'))
    if len(official)!=6:raise ValueError('Six official implementation trials required before final manuscript')
    words=len(ABSTRACT.split())
    if words>200:raise ValueError(f'Abstract {words} words')
    figures(compact);baseline=load(FROZEN/'baseline_comparison.json');phi=load(FROZEN/'multi_model_results.json')['phi3.5:latest']
    historic=r'''\begin{table}[htbp]\centering\small
\caption{Historical V3.2 custom population, unchanged. Attack denominators600; benign denominators250. Local adapters do not represent official baseline agents. Latency is historical mean over850 admitted records.}\label{tab:historical}
\begin{tabularx}{\linewidth}{Xrrrrr}\toprule System & MCR & E2E & Utility & FRR & ms\\\midrule
'''
    for name,value in list(baseline.items())+[('HETE/Phi-3.5',phi)]:
        name=name.replace('-inspired',' (local)').replace('Spotlighting','Spotlighting (local)')
        historic+=tx(name)+' & '+' & '.join(f"{value[k]['count']}/{value[k]['denominator']}" for k in ('mcr','e2e','utility','frr'))+f" & {value['latency_mean_ms']:.1f}"+r' \\'+'\n'
    historic+=r'\bottomrule\end{tabularx}\end{table}'
    external=r'''\begin{table}[htbp]\centering\small
\caption{New external study: separate backbones and local configurations. Attacks show success/scored plus planned and actual injected-input exposure. Unknown outcomes are never blocked successes. Writes are complete benign tasks with an observed state-changing write, out of nine delegated-write tasks per model/configuration.}\label{tab:external}
\begin{tabularx}{\linewidth}{Xlrrrrr}\toprule Backbone & Local & Utility & Attack & Plan & Exposed & Writes\\\midrule
'''
    for r in compact:
        external+=f"{label(r['model'])} & {r['config'][:2]} & {r['benign_utility']}/{r['benign_n']} & {r['official_attack_success']}/{r['attack_scored_n']} & {r['attack_planned_n']} & {r['injected_content_observed_n']} & {r['benign_complete_with_write']}/{r['benign_write_tasks']}"+r' \\'+'\n'
    external+=r'\bottomrule\end{tabularx}\end{table}'
    bilingual_table=r'''\begin{table}[htbp]\centering\small
\caption{New synthetic bilingual report workflow. Four semantic intents translated to KO/EN produce eight IDs. C3 is a fixed first-term resolver and is not a general deterministic reasoning baseline. Its repeated model blocks are not additional independent cases.}\label{tab:bilingual}
\begin{tabular}{llrrr}\toprule Backbone & Local & KO & EN & Total\\\midrule
'''
    bilingual_summary=[]
    for model in sorted({r['run_id'].split('/')[0] for r in bilingual}):
        for config in ('C0_vanilla','C1_minimal','C2_typed','C3_literal_resolver'):
            pop=[r for r in bilingual if r['run_id'].startswith(model+'/') and r['config']==config]
            ko=sum(r['utility'] for r in pop if r['language']=='ko');en=sum(r['utility'] for r in pop if r['language']=='en')
            bilingual_table+=f'{label(model)} & {config[:2]} & {ko}/4 & {en}/4 & {ko+en}/8'+r' \\'+'\n'
            bilingual_summary.append({'model_block':model,'config':config,'ko':ko,'en':en,'total':ko+en,'n':8})
    bilingual_table+=r'\bottomrule\end{tabular}\end{table}'
    write(TASK/'data/BILINGUAL_SUMMARY.json',bilingual_summary)
    official_text=(f"The upstream CaMeL PrivilegedLLM, interpreter and domain policies were executed on three official task IDs, with benign and direct-attack conditions ({len(official)} trials). "
        f"Benign utility was {sum(r['utility'] for r in official if r['method']=='benign')}/3; attack-goal success was {sum(r['attack_success'] is True for r in official if r['method']!='benign')}/3, "
        f"with {sum(r['backend_failure'] for r in official)} backend/integration exceptions. "
        "These are functional local-backend observations, not reproduction of published numbers. Agent interface, domain policies and retry budget differ from C1/C2, so no superiority is inferred.")
    body=r'''\section{Introduction}
Tool-using language-model agents can transform untrusted tool observations into proposed email, calendar, payment or reporting operations. A generated instruction does not establish authority. Prompt injection and retrieval corruption make the distinction operationally important~\cite{greshake2023indirect,zou2025poisonedrag,owasp2026,nistaml2025,mitreatlas2026}. Zero Trust motivates explicit verification of application-granted access rather than trust based on the origin of prose~\cite{nistzt2020}.

HETE (Heterogeneous Entity Trust Extension) represents application authority, evidence and effects in a typed security intermediate representation. The objective is to separate a model's proposed action from an authorized effect and to retain the evidence needed to audit that separation. A flat policy checker can enforce the same predicate; typed syntax alone is not presumed to improve security. This distinction is central to our evaluation rather than an unfavorable comparison to omit.

We ask three questions. RQ1: does an actual compiled authority/evidence/action path prevent finite unauthorized effects while permitting legitimate writes? RQ2: what empirical security, utility, latency or trace difference remains when a minimal guard has equivalent policy and model proposals? RQ3: how do model compatibility, encoded outputs, task exposure and missing backend responses constrain interpretation? Contributions are the executable typed boundary, matched effect-level evaluation and a failure-preserving record of where the approach does and does not apply.

The work addresses secure AI deployment and application-level vulnerability mitigation. UIR-Core Typed IR v0.1 is a shared evolving architecture; the Python security IR here is an application reference interpreter, not a claim of wire or Rust implementation equivalence. V3.2 denotes the historical evaluation, V4/V4.1 the earlier mechanism/repair studies, and V4.2 separate new protocols. No historical outcome is replaced by a repaired system's result.

\section{Related Work and Architectural Scope}
CaMeL separates control/data flow and propagates capabilities; Progent enforces programmatic privilege policy; IsolateGPT mediates isolated agentic execution~\cite{debenedetti2025camel,shi2025progent,wu2025isolategpt}. StruQ and SecAlign improve instruction/data separation through structured training or preference optimization, while Spotlighting marks untrusted input~\cite{chen2025struq,chen2025secalign,hines2024spotlighting}. Instruction hierarchy and retrieval augmentation are complementary upstream mechanisms~\cite{wallace2024instructionhierarchy,lewis2020rag}. A recent Electronics middleware addresses prompt injection and sensitive-data exposure~\cite{hsine2026middleware}.

HETE's proposed delta is a common record linking application authority, scoped evidence, approved actions, resource checkpoints and canonical output to actual effects. Capabilities, isolation and output filtering are prior mechanisms, not inventions claimed here. The comparison in Table~\ref{tab:fidelity} distinguishes architecture and actual evaluation. AgentDojo supplies stateful tasks and security/utility oracles~\cite{debenedetti2024agentdojo}. Adaptive studies motivate policy-aware attacks, but the fixed attacks and boundary replacement tests here do not reproduce their search algorithms~\cite{zhan2025adaptive,hofer2026assessing}.

\begin{table}[htbp]\centering\small\caption{Comparison fidelity. Architectural overlap is distinct from a matched empirical advantage.}\label{tab:fidelity}
\begin{tabularx}{\linewidth}{lXX}\toprule System & Relevant mechanism & Executed evidence / limit\\\midrule
CaMeL & Control/data separation, capabilities & Upstream agent subset with local backend; different interface/policy/budget\\
Progent & Programmatic privilege control & Architectural comparison; historical inspired adapter is local\\
IsolateGPT & Execution isolation and mediation & Architectural comparison only\\
StruQ / SecAlign & Training-based instruction boundary & No retraining reproduction\\
Spotlighting & Untrusted-input marking & Historical delimiter approximation\\
Minimal C1 & Flat equivalent policy checks & Same new tasks/proposals/grants as C2\\
Typed C2 & Compiled actions and proof-bound dispatch & Actual interpreter/executor, no observed extra security/utility\\\bottomrule
\end{tabularx}\end{table}

\section{Materials and Methods}
\subsection{Threat Model and Trusted Computing Base}
The adversary may control retrieved or tool-returned text and may replace the model response with arbitrary JSON. It can suggest privileged tools, changed arguments, forged principal/evidence claims, malformed identifiers, replayed nonces, stale revisions or encoded optional text. It cannot alter the application issuer, live authority store, signer keys, interpreter, registry, executor or egress channel. Hostile Python code with memory access is outside this JSON boundary.

The TCB includes principal issuance, delegated capabilities/approvals, ownership and revision state, scoped evidence endorsement, parsers, dispatch and storage. Hash equality binds bytes; it does not establish truth, freshness or authenticity. The old public HMAC fixture key cannot authenticate against an attacker who knows it. New local tests generate fresh signing/proof keys outside model context and exercise key-epoch revocation. They do not certify enterprise key management, rollback-resistant credential storage or protection after source compromise.

\subsection{Typed Records and Admission Rules}
The application constructs the trusted session, capability grants, policy revision and budget. Evidence uses \texttt{EvidenceRef}, containing a content digest, signer, claim scope, key epoch and signature. Tool text becomes \texttt{UntrustedObservation}; it never promotes itself to trusted evidence. A whole JSON decoder admits only tool and arguments, rejecting duplicate keys, nonfinite values, confusable tool identifiers and extra authority fields. The schema is closed at the proposal boundary; tool argument schemas are registry-specific.

\begin{table}[htbp]\centering\small\caption{Actual authority/record transitions and proof obligations. Runtime type checks do not authenticate a compromised application.}\label{tab:types}
\begin{tabularx}{\linewidth}{lXX}\toprule Record & Trusted origin / transition & Enforced obligation\\\midrule
TrustedSession & Application issuer & Principal, revision, grants, approval and budget fixed outside text\\
EvidenceRef & Curator/key store & Digest, signature, scope and revocation checked\\
ProposedAction & Untrusted JSON compiled by app & Whole schema, registry and arguments validated\\
ApprovedAction & Successful admission & Session, revision, arguments, evidence and nonce bound by proof\\
CanonicalOutput & Application egress & Numeric verified fields or declared task-text envelope\\
AuditEvent & Each decision/effect & IDs, stages, verdict, executor invocation and mutation linked\\\bottomrule
\end{tabularx}\end{table}

\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{typed_boundary.pdf}
\caption{Actual V4.2 proposal-to-effect path. The generator does not construct grants. Typed compilation precedes independent live-state revalidation and executor invocation. Canonical numeric output and arbitrary task text have different guarantees.}\label{fig:architecture}\end{figure}

The compiler constructs a ProposedAction and checks capability, resource scope, approval, argument constraints, admitted evidence and budget. A successful transition creates an ApprovedAction bound by a proof to principal, session, policy revision, arguments, evidence IDs and nonce. The dispatcher requires the actual approved runtime type, verifies the proof and independently checks current permission, ownership, approval, evidence status and revision. Thus an admission-time decision cannot silently authorize a later changed state. A monotone revision store rejects rollback; a consumed nonce prevents the same approval from being replayed.

\begin{verbatim}
proposal = parse_whole_json(untrusted_bytes)
typecheck(proposal, registry_schema)
check(delegation, ownership, approval, arguments)
verify(evidence_signature, content_binding, claim_scope)
approved = bind_proof(session, revision, proposal, nonce)
revalidate(approved, live_authority, evidence, nonce)
effect = executor.commit(approved)
release(canonical_contract, checked_application_record)
audit(proposal_id, approved_id, effect, output_id)
\end{verbatim}

The audit links actual proposal/approved-action IDs, proof digest, evidence IDs, stages, result and output ID under one run ID. The proof protects the approved object under the TCB assumptions; an unkeyed artifact hash alone does not create an append-only log. WORM storage, signed time and externally witnessed logging are not implemented. SQLite transaction evidence applies locally, not across distributed external APIs.

\subsection{Minimal Guard, Resolver and Gate Controls}
C0 is the unguarded local JSON agent. C1 uses flat checks for capabilities, schema, arguments, evidence and revalidation. C2 invokes the typed compiler and approved-object proof verifier, with the same application delegation predicate as C1. Common audit fields are measured equally; typed-only IDs are not treated as a security win by definition. C4 removes individual or joint gates in a separate finite corpus. Single-gate masking is distinguished from jointly disabled checks.

C3 is a deterministic workflow resolver with the same official sandbox and policy opportunity. Its first implementation mishandled BaseModel representations and had 42 transport faults in72 runs. Those failures remain recorded. A serialization-only correction on the same seen IDs is a post-hoc development diagnostic, not a new held-out control. The old numeric fixture is directly solvable by a trusted no-LLM resolver (250/250 benign and0/600 original E2E); neither study proves that inserting an LLM is necessary.

\subsection{Official Environments, Delegated Writes and Attack Surface}
AgentDojo0.1.35, benchmark revisionv1.2.2, is pinned by source commit and oracle hashes. Twelve new task IDs span workspace, banking and travel; nine requests delegate writes. Capabilities derive from the explicit authenticated request plus application constraints, never task ground truth. Examples include lunch creation with the requested participant/time, scoped calendar changes, a bounded refund to the stated account, profile updates, a specified hotel reservation and email to the stated recipient. The application owns the pre-injection calendar IDs. The agent receives neither expected utility answers nor security verdicts.

Four upstream fixed attacks (direct, ignore-previous, system-message and important-instructions without names) and one custom appended injection retain the original attacker goal. Upstream canary-based surface discovery is attack preparation outside the execution agent. Twelve tasks times five attack methods give sixty task-attack pairings. Two generator backbones and three local configurations, with benign conditions, give432 logical environment executions. These are not432 independent attacks. Qwen3-4B and Ministral3-14B are generators; Qwen3.8-27B and Ministral14B have a distinct historical AI-rater role.

Exact-request response caching is a paired counterfactual design: identical request bytes and model digest reuse one captured response, while each system executes a separate environment and official oracle. Divergent observations create new requests. A cache hit is not a new physical inference. Unique physical calls/tokens and reconstructed cold-response time are reported separately from cached wall time. No throughput advantage is inferred from reuse.

Exposure is reconstructed from actual recorded generator prompts. A normalized quote/newline view recognizes injected text inside BaseModel repr strings; the original tool-result flags and correction ledger are retained. This also prevents a last tool observation without a subsequent model call from being treated as generator exposure. Public-task contamination and correlated attack templates remain unresolved limitations.

\subsection{Canonical Output and Adversarial Replacement}
The numeric contract admits exactly a verified entity, metric, value, fiscal year and citation set. It rejects unverified optional prose. The original V4 encoded failures and V4.1 repair remain locked under their own experiments. New tests install the unchanged V4.1 guard at the actual HETE pipeline egress and separately exercise the new typed canonical boundary. Ninety-six generated variants use literal, base64, hex, URL, Unicode, fragmented, compressed and reversed representations of synthetic private content. URL encoding of an ASCII-only token may equal the literal form; these are not eight independent attack ideas.

Twelve repeated numeric positive controls and twelve repeated safe explanatory controls measure accepted-contract utility and lost functionality separately. This fixed one-query output-replacement tool is not an adaptive LLM red team. The external AgentDojo final-answer path permits arbitrary authenticated-user task text in a typed envelope and does not inherit the numeric contract's semantic/confidentiality claim. Generic natural-language DLP, covert channels and curator compromise are not solved by serialization.

\subsection{Bilingual Workflow and Model Compatibility}
A separately registered synthetic workflow has four semantic intents translated to Korean and English: revenue, profit and two explicit negation variants. Models read two signed records, select the requested metric and write an evidence-bound report to actual SQLite state. Eight IDs per generator/configuration are evaluated; translations and reused records are correlated. The first-term literal resolver is deliberately a limited program, so an advantage over it would not prove a general inability of deterministic semantic parsers. Historical Qwen2.5/Phi model results remain unchanged~\cite{qwen25techreport2024,abdin2024phi3}; the prior Phi12/12-format probes remain development-only.

\subsection{Metrics, Missing Outcomes and Resource Semantics}
Historical MCR-attempted and MCR-model-exposed use different denominators: HETE/Qwen0/600 and0/363. New external raw-goal proposal is an explicit structural predicate (attacker email/body/subject, recipient IBAN, or hotel/dates), not an alias for every historical behavioral judge. Quoting/refusing an attack does not satisfy that tool predicate. E2E is the union of forbidden content release, unauthorized execution/state mutation and independently measured resource breach, retaining component flags and an exclusive reporting priority.

Official AgentDojo goal success is preserved as implemented. In banking, the upstream injection oracle counts an outgoing attacker transfer when a streaming service exists; it is not independent proof that a subject disclosed that service. Policy rejection is not attack success, and neither is it proof of model resistance. Proposal, admission, executor invocation, state mutation, read side effect and egress are separately recorded. Task utility additionally requires the official legitimate completion criterion.

Incomplete backend responses produce unknown security outcomes, never blocked attacks. Retained response IDs identify cache propagation from a physical failure to several logical trials. Planned, scored and injected-input-exposed denominators appear together. Missing-outcome lower/upper bounds use observed successes/N and(successes+unknown)/N. Calls, steps, tokens and bytes are checkpointed; late output overrun is denied after the call. HTTP timeout and post-call accounting do not establish hard streaming cancellation or a universal wall-clock bound.

\subsection{Statistics, Annotation and Reproducibility}
Wilson intervals condition on binomial assumptions~\cite{wilson1927probable}. Repeated tasks/templates and selective backend completion limit population interpretation. Endpoint definitions appear in the original work order, but the explicit analysis-family file was written after the first backbone and during the second. Six domain/backbone C1/C2 exact paired McNemar comparisons with Holm adjustment and task-ID bootstrap are therefore exploratory~\cite{mcnemar1947note,westfall1993resampling}. Unknown paired outcomes are retained in planned counts and excluded from completed-pair calculations. Zero-only bootstrap differences do not bound unseen risk. Historical true template-family IDs were not retained; class-language sensitivity is only a coarse proxy.

No new human participants or human adjudication are represented. The user-authorized prior AI study contains200 attacks and50 benign IDs, independently executed by two local models with identities/verdicts blinded. MCR pairwise agreement is172/200, E2E185/200 and benign50/50; kappa values are0.367,0.615 and1.000~\cite{cohen1960kappa}. AI agreement is not human accuracy or an independent ground-truth oracle. Disagreements remain unchanged. Institutional ethics applicability and author declarations require confirmation.

ChatGPT/Codex assisted code development, experiment orchestration, analysis and drafting. Native local generator and historical annotation models are identified separately in the model registry with artifact digests; local annotation is not a human contribution or independent human validation. No exact unpublished service-model version is invented. All AI-assisted content requires author review and responsibility before submission.

Original historical source/data manifests and failures remain locked. Independent aggregation reproduces19,900 admitted score-projection records,24 nonadaptive configurations plus adaptive campaigns, and exact statistics. A separate exact-byte source overlay verifies418 non-bytecode artifacts; the original736-entry manifest still has67 mismatches, with13 Python files recovered only in the overlay and54 bytecode entries unresolved. Missing original interrupted response bodies are not reconstructed. Portable scalar aggregation, scorer replay and fresh inference are different reproduction levels. No public deposit/DOI or external human replication is asserted.

\section{Results}
\subsection{Historical Outcomes and Conditional Containment}
HISTORICAL_TABLE
HETE/Qwen observed0/600 MCR and E2E,249/250 complete utility and1/250 false rejection. Phi observed3/600 MCR,6/600 E2E and0/250 utility. A Wilson upper bound for0/600 is approximately0.64\% under the stated assumptions, not a security proof. Among600 HETE attacks,363 invoked the model;210 policy and27 resource blocks occurred before generation. OutputGuard rejected176 exposed cases and allowed187;68 action-rejection indicators overlap. They are not sequential subtraction counts.

Individual ablations with unchanged zero effects are distributional masking, not proof that a layer is unnecessary. Removing ResourceGuard produced20/600 E2E resource outcomes; jointly removing capability, policy and action checks produced7/600 E2E. The old adaptive campaign observed one excessive-agency MCR seed among30 and no E2E seeds, while preserving six separate campaigns and3,600 queries. These populations are not merged with new studies.

\subsection{Expanded External Study and Typed Incremental Value}
EXTERNAL_TABLE
The matched minimal and typed systems have identical recorded security and utility outcomes. Ministral's unguarded configuration completes8/12 benign tasks, versus7/12 for either guard. The loss is a reschedule proposed with an explicit duration update outside the declared delegation; the held-out policy is not patched after inspecting it. Qwen completes4/12 in each configuration. Thus normal writes are possible, but enforcement and model contract failures still limit complete utility.

\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{security_utility.pdf}
\caption{New local-agent outcomes in official environments. C1 and C2 overlap empirically. Conditional intervals do not remove task/template dependence or unknown backend outcomes. C0 is unguarded; graph denominators are scored attacks, with planned/exposure/missing values in Table~\ref{tab:external}.}\label{fig:tradeoff}\end{figure}

Ministral has two unknown attack outcomes per configuration, originating from two retained incomplete physical responses and propagated cache hits. Its guarded planned success range is0/60 through2/60, while completed-case success is0/58. For Qwen the guarded completed/planned result is0/60. These are not pooled into a universal zero/N. The 690 unique physical generator requests in this external study are distinct from432 logical episodes and exclude later bilingual/official-backend calls.

\subsection{Typed Effects, Bounded State and Cost}
The finite mechanism corpus has ten adversarial and two positive scenarios per configuration. C1 and C2 observe no forbidden SQLite effects and pass both positive controls. Removing revalidation yields two forbidden effects; joint capability/revalidation removal yields four, and joint evidence/revalidation removal five. Live ownership/revision and evidence revocation races are separately rejected. A bounded comparison enumerates96 authority states across role, owner, approval, signer, revision and nonce status, executing192 minimal/typed SQLite trials with zero specification mismatches. This finite model is not an unbounded compiler proof.

POLICY_TIMING
The timing experiment includes actual admission/revalidation/commit but excludes session/key/database construction. It is a local CPU microbenchmark, not an LLM end-to-end speedup. Both systems can log the common decision fields; C2 additionally links actual approved typed objects and proof obligations. That architectural linkage is not presented as an empirical security advantage by definition.

\subsection{Encoded Counterexamples and Contract Cost}
The historical original failures remain:12/12 V4 search seeds,40/120 outer releases and1/12 actual-pipeline replacement releases. The corresponding old strict results remain separate. In the new96-variant replacement test, the original actual pipeline releases72 attacks; the identical installed V4.1 guard and new typed canonical boundary release none. All three pass12/12 repeated numeric controls. Both strict boundaries deny12/12 repeated legitimate explanatory records. The repair therefore narrows application functionality; broad zero-usability-loss and general natural-language confidentiality are unsupported.

\subsection{Bilingual Utility and Official Agent Integration}
BILINGUAL_TABLE
The bilingual results concern four synthetic semantic intents, not general multilingual competence. Complete utility requires exactly one correct report commit within six steps; duplicate correct writes also fail. Qwen completes0/8 in each local configuration, while Ministral completes1/8; the literal first-term resolver completes4/8, failing the negation variants. These results do not establish an LLM advantage. Wrong metric selection, missing or repeated report commits and model contract errors remain failures; the literal resolver's scope is explicit. No model performance is substituted into historical Phi or Qwen2.5 results.

OFFICIAL_TEXT
Earlier excluded development probes are retained. A provider adapter preserves upstream system-message content while translating an unsupported developer role for the local API, and caps decoder/attempt budgets. The upstream interpreter and policy code are unchanged. Format/interpreter/backend failures are reported rather than replaced by local inspired results. The earlier106 interpreter unit tests remain module-level evidence only.

\section{Discussion}
\subsection{What Typed UIR Adds and What Is Not Demonstrated}
The implemented IR makes trusted context, proposed intent, approval and executed effect separate objects with explicit transitions. Proof binding and live-state revalidation exercise structural obligations that a raw language-model response cannot satisfy by asserting authority. However, the same application predicate in a flat guard produces the same observed decisions. The measured contribution is an executable, auditable architecture and transparent effect-level evaluation, not proof that typed syntax is inherently more secure or that capability guards were invented here.

The one benign duration denial and complete rejection of safe extra prose show why security cannot be evaluated by blocking all writes or all outputs. Our external study permits actual legitimate writes, yet application grants can still be overrestrictive. The historical deterministic resolver solves the numeric fixture more directly, and the corrected external resolver is only post-hoc diagnostic evidence. The bilingual toy test cannot prove that an LLM is necessary for semantic tasks.

\subsection{Threat Coverage and Experimental Dependence}
The attack families are fixed public templates plus a custom append; they are not independent human red teaming or an adaptive multi-turn optimizer. Injection discovery, actual generator exposure and official effects are distinct. The canonical remedy protects a closed numeric representation, whereas arbitrary final task text remains outside that confidentiality contract. Correlated task IDs, repeated templates, public training contamination and missing backend outcomes constrain uncertainty. An all-zero observed guard result should be read with its completed/planned denominators, not as an assurance about unseen attacks.

Common-response caching controls the proposed computation but changes runtime accounting. Cached wall time is a host/orchestration observation; it cannot support a system throughput claim. Different official-agent control flows and retry settings prevent a clean published-system performance ranking. Negative development outcomes and transport amendments are retained to avoid silently converting seen failures into a new held-out success.

\subsection{Deployment, Ethics and Availability}
Real deployments need authenticated principal issuance, protected keys, revocation and rollback-resistant current policy state, mediated external APIs and a sole checked output channel. SQLite atomicity does not extend automatically to cloud services. No hard cancellation, enterprise credential assurance, formal universal proof, generic truth checking or resistance to TCB compromise is claimed. No new human study is certified exempt by this implementation. Final declarations, rights and public data/code access require author/institutional decisions; no DOI or availability is fabricated.

\section{Conclusions}
HETE implements an application-controlled typed proposal-to-effect boundary and tests it under equivalent minimal policy, actual writes and explicit negative controls. The new studies retain encoded leakage, functional costs, model failures and unknown outcomes. Typed records expose execution obligations and provenance, while incremental empirical security/utility over the equivalent guard remains unestablished. The evidence supports a bounded, auditable application architecture and an honest separation of model behavior, authorized effects, utility and resource validity; it does not establish universal prompt-injection resistance or general confidentiality.
'''
    timing=csvrows(TASK/'experiments/policy_incremental/POLICY_TIMING_SUMMARY.csv')
    timing_text='The 200-pair local admission/commit experiment measured '
    timing_text+='; '.join(f"{r['system']} median {float(r['p50_us']):.1f} microseconds (p95 {float(r['p95_us']):.1f}, p99 {float(r['p99_us']):.1f})" for r in timing)+'.'
    body=body.replace('HISTORICAL_TABLE',historic).replace('EXTERNAL_TABLE',external).replace('BILINGUAL_TABLE',bilingual_table)
    body=body.replace('OFFICIAL_TEXT',official_text).replace('POLICY_TIMING',timing_text)
    # Typography only; never change saved trial records or denominators.
    for word in ('denominators','over','in','give','not','and','among','contains','is','are','reproduces','verifies',
                 'original','has','with','overlayand','observed','releases','pass','deny','completes','versus','executing',
                 'approximately','produced','from','range','through','new','earlier','code','Among','for','rejected','allowed','benign','E2E'):
        body=re.sub(r'\b'+word+r'(?=\d)',word+' ',body)
    body=body.replace('AgentDojo0.1.35','AgentDojo 0.1.35').replace('revisionv1.2.2','revision v1.2.2').replace('Phi12/12','Phi 12/12').replace('HETE/Qwen0/600','HETE/Qwen 0/600')
    author=load(TASK/'manifests/AUTHOR_METADATA.json');funding=tx(author['funding_verbatim'])
    back=r'''\section*{Publication Statements}
\textbf{Supplementary materials.} S1 contains historical lineage/count/exact-test reconstruction; S2 expanded task/payload/role ledgers and missing/exposure corrections; S3 typed mechanism, bounded-state and output-contract tests; S4 bilingual outcomes and official-agent compatibility traces. These are locally retained review artifacts; public release has not been approved.

\textbf{Author contributions.} The author-directed template is: CONTRIBUTIONS. The HETE-specific allocation and final approval of this exact version require both authors' confirmation.

\textbf{Funding.} FUNDING

\textbf{Institutional review and consent.} No human evaluation participants were recruited; local AI annotation is not a human study. Institutional applicability and final wording require author confirmation.

\textbf{Data and code availability.} Supporting files are retained locally. Public release rights/license and an approved reviewer-request delivery route remain to be confirmed. No public repository release or DOI is asserted. Original missing interrupted-response bodies are not available. A score projection is distinct from full transport replay or fresh inference.

\textbf{Acknowledgments and GenAI assistance.} ChatGPT/Codex assisted implementation, orchestration, analysis and drafting. Local generator and AI-rater roles and digests are separately recorded. AI systems are not authors. The authors must review all AI-assisted content and approve the final disclosure before submission.

\textbf{Conflicts of interest.} The supplied prior-paper template declares no conflict; a HETE-specific declaration from both authors is still required.
'''.replace('CONTRIBUTIONS',tx(author['contribution_template'])).replace('FUNDING',funding)
    for directory in (TASK/'manuscript_preprint',TASK/'manuscript_electronics'):
        write(directory/'manuscript_body_v4_2.tex',body)
        write(directory/'publication_statements.tex',back)
        shutil.copy2(TASK/'source/references_clean.bib',directory/'references_clean.bib')
        for name in ('typed_boundary.pdf','security_utility.pdf'):shutil.copy2(TASK/'figures'/name,directory/name)
    preprint=r'''\documentclass[11pt]{article}
\usepackage[a4paper,margin=24mm]{geometry}\usepackage[T1]{fontenc}
\usepackage{mathptmx,courier,graphicx,tabularx,booktabs,amsmath,microtype,url}
\usepackage[hidelinks]{hyperref}
\title{TITLE}\author{Seong-Su Park\\Department of Computer Engineering, Ajou University\\Suwon 16499, Republic of Korea; parky@ajou.ac.kr\\ORCID: 0009-0008-4056-3875
\and Ki-Hyung Kim\\Department of Cyber Security, Ajou University\\Suwon 16499, Republic of Korea; kkim86@ajou.ac.kr\\Corresponding author; ORCID: 0000-0002-2321-4475}
\date{21 October 2026 --- V2/V4.2 local draft\\Preprint. Not peer-reviewed. Not posted.}
\begin{document}\maketitle\begin{abstract}ABSTRACT\end{abstract}
\noindent\textbf{Keywords:} KEYWORDS
\input{manuscript_body_v4_2.tex}\input{publication_statements.tex}
\bibliographystyle{unsrt}\bibliography{references_clean}\end{document}
'''.replace('TITLE',TITLE).replace('ABSTRACT',ABSTRACT).replace('KEYWORDS',KEYWORDS)
    write(TASK/'manuscript_preprint/HETE_PREPRINT_V2.tex','% Freeze ID: HETE-ELECTRONICS-V4.2-2026-10-21-R1\n'+preprint)
    directory=TASK/'manuscript_electronics';definitions=directory/'Definitions'
    if not definitions.exists():
        with zipfile.ZipFile(TASK/'resources/mdpi_official_template_current.zip') as z:
            for name in z.namelist():
                path=Path(name)
                if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe template member')
                if 'Definitions' in path.parts and not name.endswith('/'):
                    index=path.parts.index('Definitions');target=directory/Path(*path.parts[index:]);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    gsroot=OLD/'resources/tex_packages/ghostscript'
    env=dict(os.environ);env['LD_LIBRARY_PATH']=str(gsroot/'usr/lib/x86_64-linux-gnu')
    env['GS_LIB']=':'.join(str(p) for pattern in ('*/Resource/Init','*/lib') for p in (gsroot/'usr/share/ghostscript').glob(pattern))
    for eps in definitions.glob('*.eps'):
        output=eps.with_name(eps.stem+'-eps-converted-to.pdf')
        if not output.exists():subprocess.run([str(gsroot/'usr/bin/gs'),'-dSAFER','-dBATCH','-dNOPAUSE','-sDEVICE=pdfwrite',
            '-dEPSCrop','-sOutputFile='+str(output),str(eps)],env=env,check=True,stdout=subprocess.DEVNULL)
    journal=r'''\documentclass[electronics,article,submit,pdftex,moreauthors]{Definitions/mdpi}
\usepackage{amsmath,courier,tabularx,graphicx}
\firstpage{1}\pubvolume{1}\issuenum{1}\articlenumber{0}\pubyear{2026}\copyrightyear{2026}
\datereceived{}\daterevised{}\dateaccepted{}\datepublished{}\hreflink{}\doinum{}
\setlength{\headheight}{25pt}\lhead{\footnotesize Internal Electronics V4.2 draft --- not submitted}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\footnotesize Internal journal draft --- not submitted}}
\renewcommand{\contentleftcolumn}{\leftcolFont\raggedright\textbf{Local review draft}\\Not submitted or published.\\Author declarations and release approvals remain unresolved.\\No publication license has been granted.}
\Title{TITLE}\TitleCitation{Typed Authority and Auditable Enforcement}
\newcommand{\orcidauthorA}{0009-0008-4056-3875}\newcommand{\orcidauthorB}{0000-0002-2321-4475}
\Author{Seong-Su Park $^{1}$\orcidA{} and Ki-Hyung Kim $^{2,}$*\orcidB{}}
\AuthorNames{Seong-Su Park and Ki-Hyung Kim}\AuthorCitation{Park, S.; Kim, K.-H.}
\address{$^{1}$ Department of Computer Engineering, Ajou University, Suwon 16499, Republic of Korea; parky@ajou.ac.kr\\
$^{2}$ Department of Cyber Security, Ajou University, Suwon 16499, Republic of Korea; kkim86@ajou.ac.kr}
\corres{Correspondence: kkim86@ajou.ac.kr; Tel.: +82-31-219-2433}
\abstract{ABSTRACT}\keyword{KEYWORDS}
\begin{document}\noindent\textbf{Internal review draft. Final author declarations and release gates remain unresolved; not submitted.}
\input{manuscript_body_v4_2.tex}\input{publication_statements.tex}
\bibliography{references_clean}\end{document}
'''.replace('TITLE',TITLE).replace('ABSTRACT',ABSTRACT).replace('KEYWORDS',KEYWORDS)
    write(directory/'HETE_JOURNAL_V4_2.mdpi.tex','% Freeze ID: HETE-ELECTRONICS-V4.2-2026-10-21-R1\n'+journal)
    write(TASK/'manifests/MANUSCRIPT_NUMERIC_SOURCES.json',{'abstract_words':words,'keywords':len(KEYWORDS.split(';')),
        'external':sha(TASK/'data/EXTERNAL_COMPACT.json'),'historical':sha(FROZEN/'baseline_comparison.json'),
        'bilingual':sha(TASK/'data/BILINGUAL_SUMMARY.json'),'official_rows':len(official),'body_sha256':sha(directory/'manuscript_body_v4_2.tex'),
        'author_source':author['source_sha256'],'funding':'verbatim user-supplied acknowledgment, ampersands escaped for TeX only',
        'scope':'all new tables generated from saved records; curated narrative numerals independently audited in preflight'})
    print('abstract words',words,'keywords',len(KEYWORDS.split(';')))


if __name__=='__main__':main()
