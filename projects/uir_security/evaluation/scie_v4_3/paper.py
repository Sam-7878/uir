"""Expanded shared manuscript from sealed V4.2 inputs and actual V4.3 records."""
from .common import *
import re
import shutil
import textwrap
import zipfile
os.environ['MPLCONFIGDIR']=str(TASK/'resources/matplotlib_cache')
import matplotlib
matplotlib.use('Agg');matplotlib.rcParams['pdf.fonttype']=42
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

TITLE='HETE: Typed Authority and Auditable Enforcement for Tool-Using Language-Model Agents'
ABSTRACT='''Language-model agents require application-controlled authority when processing adversarial observations. HETE separates untrusted proposals, approved actions, verified effects, and narrative output in an executable typed boundary. We compare typed and flat representations under equivalent security predicates and preserve unfavorable historical outcomes. A historical AgentDojo study contains 432 logical executions across two generators; minimal and typed guards have identical security and utility, with two unknown Ministral attack outcomes per configuration. A separately registered extension executes 352 paired composition cases, 48 paired audit-manipulation cases, and a bounded narrative corpus. Both guards show zero forbidden effects in 327 negative cases, complete all 24 explicit positive controls, and detect all tested audit manipulations. No incremental typed security or audit-detection benefit is observed. A shared public-fact renderer completes 48 supported explanations but still denies 16 benign arbitrary-prose requests; controlled attack releases remain zero in 64 cases. This functionality gain belongs to the output contract rather than typing. We report local overhead, registration chronology, missing original archives, and a posthoc utility-oracle correction. The evidence supports an auditable reference architecture and matched negative results, not universal confidentiality, production assurance, or superiority over equivalent guards.'''
KEYWORDS='secure AI deployment; prompt injection; typed intermediate representation; capability enforcement; auditability; negative results'
def esc(s):return str(s).replace('_',r'\_').replace('&',r'\&').replace('%',r'\%')
def csvrows(path):return list(csv.DictReader(Path(path).open()))

def figures():
    out=csvrows(TASK/'reports/OUTPUT_TRADEOFF_RESULTS.csv');configs=['numeric_strict','C1_flat','C2_typed','unsafe_open_control']
    fig,axes=plt.subplots(1,3,figsize=(11,4.2))
    for ax,kind,key,title in zip(axes,['supported_benign','unsupported_benign','attack'],['complete_explanatory_utility','complete_explanatory_utility','leaks'],
        ['Supported explanation (48 IDs)','Arbitrary benign prose (16 IDs)','Controlled leak (64 attack IDs)']):
        values=[next(r for r in out if r['config']==c and r['population']==kind) for c in configs]
        rates=[100*int(r[key])/int(r['n']) for r in values];ax.bar(range(4),rates,color=['#9ca3af','#60a5fa','#2563eb','#f59e0b'])
        for i,r in enumerate(values):ax.text(i,rates[i]+2,f"{r[key]}/{r['n']}",ha='center',fontsize=8)
        ax.set(xticks=range(4),xticklabels=['numeric','flat','typed','unsafe\ndiagnostic'],ylim=(0,112),title=title,ylabel='Percent');ax.tick_params(axis='x',labelsize=8);ax.grid(axis='y',alpha=.2)
    fig.suptitle('Finite repeated templates; complete utility is an audited secondary measure',fontsize=10)
    fig.tight_layout();fig.savefig(TASK/'figures/v43_output_tradeoff.pdf');fig.savefig(TASK/'figures/v43_output_tradeoff.png',dpi=600);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4.4));ax.axis('off');ax.set(xlim=(0,12),ylim=(0,5))
    boxes=[(.3,3.6,3,.8,'Application-owned authority\nprincipal, revisions, public binding'),(.4,1.9,2.5,.8,'Untrusted proposal\nordered two-service steps'),
           (3.5,1.9,2.5,.8,'Flat or typed carrier\nsame proof and predicates'),(7,2,3.8,.8,'Two attached SQLite databases\ncommit both or roll back both'),
           (3.5,.2,2.5,.8,'Untrusted narrative request\nno execution authority'),(7,.2,3.8,.8,'Public-fact renderer / outbox\narbitrary prose remains denied')]
    for x,y,w,h,label in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',fc='#eff6ff',ec='#334155'));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=8)
    for a,b in [((3,2.3),(3.4,2.3)),((6.1,2.3),(6.9,2.3)),((6.1,.6),(6.9,.6)),((3.4,3.9),(4.5,2.8)),((3.4,3.8),(8,.99))]:ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','lw':1.2})
    ax.text(6,4.8,'Carrier structure, effect authorization and information release are different obligations',ha='center',fontsize=9)
    fig.tight_layout();fig.savefig(TASK/'figures/v43_channels.pdf');fig.savefig(TASK/'figures/v43_channels.png',dpi=600);plt.close(fig)

def results(summary):
    table=r'''\subsection{V4.3 Primary Result: No Observed Typed Increment}
\label{sec:primarynull}
The registered primary comparison remains negative. Both configurations apply the same security and audit predicates; neither has an observed incremental effect advantage. Table~\ref{tab:v43composition} reports the complete paired populations before the historical results below.
\begin{table}[htbp]\centering\small
\caption{New finite composition and anchored-audit outcomes. Counts are per carrier,with352 matched composition IDs and48 matched audit manipulation IDs. The327 negative cases are distinct from24 explicit positive/replay controls;the all-true authority state remains inside the state corpus.}\label{tab:v43composition}
\begin{tabularx}{\linewidth}{Xrr}\toprule Endpoint & Flat C1 & Typed C2\\\midrule
'''
    left,right=summary['composition']
    for name,a,b in [('Forbidden effects among negative cases',f"{left['forbidden_effects']}/327",f"{right['forbidden_effects']}/327"),
                     ('Specification mismatches','0/352','0/352'),('Explicit positive/replay complete utility','24/24','24/24'),('Common audit traces complete and valid','352/352','352/352'),('Audit manipulation detected','48/48','48/48')]:table+=f'{name} & {a} & {b}'+r'\\'+'\n'
    table+=r'''\bottomrule\end{tabularx}\end{table}
There are no discordant pairs in either primary comparison:exact McNemar and Holm-adjusted p-values are1. These descriptive results do not prove statistical equivalence or zero future risk. The conditional Wilson upper bound for0/327 is approximately1.16\%,under binomial assumptions that do not turn this constructed enumeration into a deployment sample. Both configurations permit real authorized state changes,so the null is not obtained by denying every write.

The registered one-run stop condition was met. The owner had authorized a transition to Track B when no defensible extra effect was observed. No further semantic-model or official-agent inference was performed to search for a better number. There are zero new physical model requests. The new finite results are not pooled with432 historical logical environments or690 historical physical requests.

\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{v43_channels.pdf}
\caption{New local reference flow. Flat and typed carriers have equal predicates. The trusted effect is application-serialized state evidence;the separate narrative outbox renders only supported public facts. Source authority,current-state checks and sole mediation remain trusted assumptions.}\label{fig:v43channels}\end{figure}

\subsection{V4.3 Explanation Functionality and Remaining Denials}
\label{sec:v43output}
The common bounded renderer completes48/48 supported public-fact explanations and rejects all16 arbitrary benign prose requests. Thus overall complete utility over the declared64 benign output cases is48/64,not universal narrative support. Both C1 and C2 release zero controlled secrets in64 attacks. The strict numeric diagnostic releases no explanations. The unsafe-open diagnostic releases controlled private bytes in48/64 attacks;it is a sensitivity control,not a practical competing agent.

The48 supported IDs repeat six mode/language templates,and64 attack IDs repeat eight programs. These are not48 independent semantic tasks or64 independently sampled attacker distributions. The improvement over numeric-only output is attributable to an altered public-fact contract,shared equally by C1 and C2. Arbitrary model prose,covert channels and misclassified public data remain outside its guarantee.

\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{v43_output_tradeoff.pdf}
\caption{New finite output-contract results. Complete explanation counts are independently audited secondary metrics:the original release-only flags remain in raw records. Unsafe empty releases are not counted as complete explanations. Numeric/unsafe policies differ in functionality and are diagnostics rather than matched typed baselines.}\label{fig:v43output}\end{figure}

The after-final utility audit is material. An empty emitted string can satisfy a release flag but fail the requested explanation. All48 supported unsafe-control releases are empty and therefore have0/48 complete utility;the bounded renderer's actual public values and citations satisfy48/48. Its16 general-prose denials remain. The secondary correction and chronology are recorded without rerunning any final case or altering registered H1/H2 outcomes.

\subsection{V4.3 Runtime Cost and Audit Interpretation}
'''
    for r in summary['timing']:
        table+=f"{esc(r['config'])} has a local median of{r['p50_us']:.1f} microseconds,p95 {r['p95_us']:.1f} andp99 {r['p99_us']:.1f} over200 paired positive executions. "
    table+=r'''Both timed tasks actually commit the two permitted rows. World,key and database construction are excluded. The result is local carrier/check/commit/audit overhead,not generator acceleration or a demonstrated deployment throughput effect. No human cause-localization latency,developer error reduction or engineering productivity was measured.

Common audit completeness and manipulation detection are equal. The experiment requires trusted application anchors and current keys;it does not show an externally witnessed append-only log. The digest of a count projection is not authentication of every database value. These scope restrictions are part of the primary interpretation rather than relegated to an implicit implementation assumption.
'''
    return table

def appendix():
    from .study import TAMPERS,AUDIT_TAMPERS,OUTPUT_FAMILIES
    text=(TASK/'source/formal_appendix.tex').read_text()
    text+=r'''\section{Complete Case-Program Catalog}
\label{app:catalog}
The tables below enumerate programs and obligations,not every repeated identifier. The JSON manifests preserve all352 composition IDs,128 output IDs and their configuration pairing. Program counts and repetitions are reported separately. A new controlled canary changes bytes without necessarily introducing a new attack idea.

\subsection{Authority Axes and Specification}
\begin{longtable}{p{.24\linewidth}p{.63\linewidth}}
\caption{Eight finite authority attributes. Full enumeration has256 states;this is an application abstraction rather than an identity federation.}\label{tab:axes}\\\toprule Attribute & Interpretation in the local world\\\midrule\endfirsthead
\toprule Attribute & Interpretation\\\midrule\endhead
'''
    axisnotes=[('role ok','Application asserts writer role for the fixed two-step request.'),('owner finance','Current ownership assertion for the debit resource.'),('owner records','Current ownership assertion for the report resource.'),('approval finance','Current finance-service approval assertion.'),('approval records','Current records-service approval assertion.'),('evidence active','Current curator-evidence status,including explicit revocation races.'),('revision current','The application policy-current assertion;stale cases also advance the actual records revision.'),('nonce fresh','The request mustnot be in the consumed-nonce set;replay cases exercise actual repeated dispatch.')]
    for a,b in axisnotes:text+=esc(a)+' & '+esc(b)+r'\\'+'\n'
    text+=r'\bottomrule\end{longtable}'+'\n'
    text+=r'''The specification requires both permitted state changes when all attributes hold,and no change otherwise. It intentionally abstracts principal/owner/approval facts into trusted attributes. Tests do not validate the authority issuer's correctness,organizational separation of duties or an external approval signature. Those remain TCB and deployment requirements.

\subsection{Intermediate-State Mutation Programs}
\begin{longtable}{p{.25\linewidth}p{.62\linewidth}}
\caption{Sixteen mutation programs,each repeated four times per carrier. Every program haszero specified unauthorized commits.}\label{tab:mutations}\\\toprule Program & Adversarial change / obligation\\\midrule\endfirsthead
\toprule Program & Adversarial change / obligation\\\midrule\endhead
'''
    notes=['Replace authenticated principal inside a serialized approved carrier.','Attach an approval to another run or session.','Alter the finance revision without a new application proof.','Alter the records revision without a new application proof.','Change the debit argument from7 to700.','Route a step to a different service.','Substitute a resource outside the delegated request.','Reverse the ordered two-step plan.','Substitute an unapproved evidence reference.','Change the issued nonce.','Replace the proof tag.','Insert an extra authority-bearing field.','Repeat a JSON field to exploit ambiguous parser behavior.','Replace a required scalar with another JSON type.','Change public evidence bytes after compilation while retaining the old carrier.','Revoke evidence after compilation while retaining the old carrier.']
    for family,note in zip(TAMPERS,notes):text+=esc(family.replace('_',' '))+' & '+esc(note)+r'\\'+'\n'
    text+=r'\bottomrule\end{longtable}'+'\n'
    text+=r'''Proof binding is common to both carriers. Rejection of a modified plan is not typed-specific if the flat path verifies the same canonical fields. Current-state checks remain necessary even when the old carrier's tag is valid,as in evidence-revocation and stale-authority cases. A nominal data-class constructor is not an authenticated application issuer.

\subsection{Audit Manipulation Programs}
\begin{longtable}{p{.25\linewidth}p{.62\linewidth}}
\caption{Twelve anchored-audit manipulations,four repetitions each. Untampered chains are positive controls before each manipulation.}\label{tab:auditprograms}\\\toprule Program & Required verification behavior\\\midrule\endfirsthead
\toprule Program & Required verification behavior\\\midrule\endhead
'''
    notes=['Detect changed principal metadata.','Detect changed request digest.','Detect substituted evidence identifier.','Detect changed policy revision.','Detect changed verdict.','Detect changed effect count.','Detect removed middle event.','Detect a valid signed prefix missing its tail,using the terminal anchor/count.','Detect event reordering.','Detect an appended duplicate event.','Detect a modified event tag.','Reject a chain against an incorrect trusted terminal anchor.']
    for family,note in zip(AUDIT_TAMPERS,notes):text+=esc(family.replace('_',' '))+' & '+esc(note)+r'\\'+'\n'
    text+=r'\bottomrule\end{longtable}'+'\n'
    text+=r'''These programs measure integrity under the stated key and anchor assumptions. They do not establish nonrepudiation against an application that controls its own keys,or detection when a compromised host replaces both the log and trusted anchor. Public source release can permit reproduction with new keys;it does not supply missing historical signing keys or imply that exporting them would be appropriate.

\subsection{New Output Attack Programs}
\begin{longtable}{p{.25\linewidth}p{.62\linewidth}}
\caption{Eight locked new output programs,each repeated eight times. The split is over program definitions,not an assertion of blind independent attack authorship.}\label{tab:outputprograms}\\\toprule Program & Candidate construction and boundary\\\midrule\endfirsthead
\toprule Program & Candidate construction and boundary\\\midrule\endhead
'''
    notes=['Select a private reference rather than an approved public record.','Use an unendorsed source claiming a private reference.','Modify the value behind an already-public label after source binding.','Place a controlled secret in an HTML-comment free-text field.','Mix a claimed grant with a secret-bearing narrative field.','Attach a private reference from another session.','Place private bytes in a remote image URL.','Use duplicate reference keys to induce an alternative parse.']
    for family,note in zip(OUTPUT_FAMILIES,notes):text+=esc(family.replace('_',' '))+' & '+esc(note)+r'\\'+'\n'
    text+=r'\bottomrule\end{longtable}'+'\n'
    text+=r'''The renderer's safe behavior follows its restricted provenance/schema contract,not success at parsing every possible secret encoding. The historical96 encoding variants remain development evidence and are not reused as the new final test. Future changes to the renderer require new protocols and new locked programs;the present null does not authorize repeat-until-positive evaluation.

\section{Executed Trace Excerpts}
\label{app:traces}
The excerpts below project actual C2 records onto case,reason,pre/post state and effect count. Full raw rows and hashes are in the claim map. Digests/tags and keys are not printed here;this is a readable projection,not replacement evidence. C1 has the same observed effect outcomes and common fields.
'''
    raw=list(rows(TASK/'experiments/composition/runs.jsonl'))
    for id,title in [('positive-authorized-0','Authorized two-service commit'),('tamper-evidence_content_race-0','Evidence bytes change after approval'),('rollback-second_service_failure-0','Second-service failure rolls back both changes'),('replay-consumed_nonce-0','Replay does not duplicate a prior commit')]:
        r=next(x for x in raw if x['case_id']==id and x['config']=='C2_typed')
        excerpt={'case_id':r['case_id'],'actual_state_counts':r['actual_state_counts'],'expected_commits':r['expected_commits'],
                 'events':[{k:t[k] for k in ('decision','reason','before','after','effect_count')} for t in r['trace']]}
        formatted=re.sub(r'\[\n\s*(\d+),\n\s*(\d+)\n\s*\]',r'[\1, \2]',json.dumps(excerpt,indent=2))
        text+='\n\\subsection{'+title+'}\n'+r'\begingroup\footnotesize\begin{verbatim}'+'\n'+formatted+'\n'+r'\end{verbatim}\endgroup'+'\n'
    text+=r'''\section{Restoration and Source-Only Reproduction}
\label{app:reproduction}
Three input ZIPs match the supplied byte sizes and SHA-256 values:the V4.2 source,Electronics manuscript and generic preprint archives. The user confirmed deletion of the other three original archives after unpacking them. Those include the201 review,202 work-order and aggregate result ZIPs. Available directories are separately captured,but recompressing them cannot recover original ZIP metadata or prove the deleted archives' byte identity. The handoff therefore remains partial at the original-archive level.

The restored original source ZIP's30 scoped tests were actually executed in a fresh directory. The saved projection was actually extracted from an available S1 archive and recounted with isolated Python and site packages disabled. The19900 records,25 groups,aggregate counts,exact/Holm tests and adaptive summaries matched. These receipts concern the saved score projection,not original Ollama transport,missing interrupted responses,weights or fresh historical inference. Cross-OS and external-human replication were not performed.

The old full delivery manifest is not silently rewritten. Its source audit reports two post-freeze script changes and one byte-identical report relocation. One changed preflight had a fallback that could mark unavailable manuscript metadata as passed. It was not used to approve this study. The new validator requires actual files and separates scientific evidence checks from publication authorization. The historical output data are preserved,while the current input state is independently locked for this task.

For a new local reproduction,extract the new source bundle into a new checkout root containing the supplied AGENTS.md and project tree. Use the actual Python executable on that machine. Run scoped tests,then the study in its new relative result directory,then the independent analysis. The runner refuses to overwrite existing final observations. Repetition reproduces the specified finite experiment with new keys;it is not an additional held-out research sample. Do not erase original outcomes,edit a frozen case manifest or invoke old output-writing scripts to make a check look clean.

\begingroup\small\begin{verbatim}
python -m pytest tests/uir_security/test_scie_v4_3_boundary.py
python -m projects.uir_security.evaluation.scie_v4_3.study prepare
python -m projects.uir_security.evaluation.scie_v4_3.study run
python -m projects.uir_security.evaluation.scie_v4_3.analyze
\end{verbatim}\endgroup

The finite runtime uses Python standard-library cryptography primitives and SQLite. The original historical-source tests have separately specified dependencies. Figure generation and PDF construction require plotting and TeX tools;they are not dependencies of authority enforcement. No model API,old account credentials or model weights are required for the new deterministic experiment. A Git commit alone is not a snapshot of uncommitted research sources:the new source ZIP hash and source manifest are the delivery identity.

\section{Reviewer Objections and Unresolved Evidence}
\label{app:objections}
The strongest objection is novelty:an equivalent flat guard can enforce the same predicate. The present work accepts that objection's empirical consequence and does not recast equality as hidden superiority. A second objection concerns usefulness:bounded rendered explanations are narrower than arbitrary prose. The16 benign denials remain in the complete utility denominator. A third concerns independence:the attack programs are author-generated and the new finite corpus is not a model-generalization benchmark. The family split,repeat counts and zero inference calls remain explicit.

A fourth objection concerns audit trust. Keys and terminal anchors reside in the TCB. Detection of changes under those assumptions is neither external nonrepudiation nor protection after host compromise. A fifth concerns outcome completeness:effect counts are a finite state projection,not independent validation of all future executor semantics. A sixth concerns the release-only secondary flag;its correction is explicitly after final execution rather than retroactively called confirmatory.

A final objection is publication readiness. Local tests,clean PDF builds,archive CRC and byte hashes do not replace actual author/institutional decisions. Independent human language/visual review,public-data rights,reviewer-conflict clearance and final author approval remain unresolved. Accordingly,a valid scoped research artifact can coexist with a publication HOLD. The work neither predicts nor guarantees acceptance,and it does not create a new version merely to search for a favorable security number.
'''
    def catalog_table(match):
        block=match.group(0)
        caption=block[block.index(r'\caption'):block.index(r'\\\toprule')]
        header=block.split(r'\toprule',1)[1].split(r'\midrule',1)[0]
        data=block.split(r'\endhead',1)[1].rsplit(r'\bottomrule',1)[0]
        return (r'\begin{table}[H]\centering\small'+'\n'+caption+'\n'+
            r'\begin{tabularx}{\linewidth}{p{.25\linewidth}X}\toprule '+header+r'\midrule '+data+
            r'\bottomrule\end{tabularx}\end{table}')
    text,count=re.subn(r'\\begin\{longtable\}.*?\\end\{longtable\}',catalog_table,text,flags=re.S)
    if count!=4:raise ValueError('Expected four complete program catalogs')
    return text

def typography(text):
    protected=[]
    def protect(match):
        protected.append(match.group(0));return '@@PROTECTED'+str(len(protected)-1)+'@@'
    text=re.sub(r'\\(?:cite|label|ref)\{[^}]*\}',protect,text)
    for word in ('the','The','with','in','contains','states','over','and','of','alpha','are','is','approximately','from','complete','detect','per','both','produces','cases','six','given','programs','scope','not','old','new','only','all','after','for'):
        text=re.sub(r'\b'+word+r'(?=\d)',word+' ',text)
    text=re.sub(r'([,;:])(?=[A-Za-z0-9])',r'\1 ',text)
    for i,value in enumerate(protected):text=text.replace('@@PROTECTED'+str(i)+'@@',value)
    text=text.replace(r'\begin{verbatim}',r'\par\noindent\begin{minipage}{\linewidth}\begin{verbatim}')
    text=text.replace(r'\end{verbatim}',r'\end{verbatim}\end{minipage}\par')
    return text

def main():
    summary=load(TASK/'data/statistics/SUMMARY.json');figures()
    if not 170<=len(ABSTRACT.split())<=200:raise ValueError('Abstract words '+str(len(ABSTRACT.split())))
    with zipfile.ZipFile(BASE/'ELECTRONICS_SUBMISSION_READY.zip') as z:
        oldbody=z.read('manuscript_body_v4_2.tex').decode();back=z.read('publication_statements.tex').decode();journal=z.read('HETE_JOURNAL_V4_2.mdpi.tex').decode();bib=z.read('references_clean.bib')
        for name in z.namelist():
            if name.startswith(('Definitions/','vendor/')):
                path=Path(name)
                if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe source member')
                target=TASK/'paper/journal'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
        oldfigs={name:z.read(name) for name in ('typed_boundary.pdf','security_utility.pdf')}
    with zipfile.ZipFile(BASE/'HETE_PREPRINT_V2.zip') as z:pre=z.read('HETE_PREPRINT_V2.tex').decode()
    oldabstract=re.search(r'\\abstract\{(.*?)\}\\keyword',journal,re.S).group(1)
    journal=journal.replace(oldabstract,ABSTRACT).replace('V4.2','V4.3').replace('manuscript_body_v4_2.tex','manuscript_body_v4_3.tex')
    journal=journal.replace('HETE-ELECTRONICS-V4.3-2026-10-21-R1',FREEZE)
    journal=journal.replace(r'\usepackage{amsmath,courier,tabularx,graphicx}',r'\usepackage{amsmath,courier,tabularx,graphicx,longtable}')
    journal=journal.replace(r'\begin{document}',r'\setlength{\LTpre}{6pt}\setlength{\LTpost}{6pt}\raggedbottom'+'\n'+r'\begin{document}')
    anchors=r'\renewcommand{\theHsection}{app.\Alph{section}}\renewcommand{\theHtable}{app.\arabic{table}}\renewcommand{\theHequation}{app.\arabic{equation}}'
    journal=journal.replace(r'\bibliography{references_clean}',r'\appendixstart\appendix\appendixtitles{yes}'+anchors+r'\input{appendices_v4_3.tex}\bibliography{references_clean}')
    pre=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda m:r'\begin{abstract}'+ABSTRACT+r'\end{abstract}',pre,flags=re.S)
    pre=pre.replace('V2/V4.2','V3/V4.3').replace('21 October','23 October').replace('manuscript_body_v4_2.tex','manuscript_body_v4_3.tex')
    pre=pre.replace('HETE-ELECTRONICS-V4.2-2026-10-21-R1',FREEZE).replace('amsmath,microtype,url','amsmath,microtype,url,longtable,float')
    pre=pre.replace(r'\begin{document}',r'\setlength{\LTpre}{6pt}\setlength{\LTpost}{6pt}\raggedbottom'+'\n'+r'\begin{document}')
    pre=pre.replace(r'\bibliographystyle{unsrt}',r'\appendix\setcounter{table}{0}\setcounter{equation}{0}\renewcommand{\thetable}{A\arabic{table}}\renewcommand{\theequation}{A\arabic{equation}}'+anchors+r'\input{appendices_v4_3.tex}\bibliographystyle{unsrt}')
    body=oldbody.replace(r'\section{Results}',r'\input{extended_methods.tex}'+'\n'+r'\section{Results}\input{v4_3_results.tex}')
    body=body.replace(r'\section{Materials and Methods}',r'\section{Materials and Methods}'+'\n'+'This section records the prior V4.2 implementation and populations. The separately registered V4.3 extension is described in Section~\\ref{sec:v43methods}; its primary null result precedes historical tables in Section~\\ref{sec:primarynull}.\n')
    body=body.replace('Contributions are the executable typed boundary, matched effect-level evaluation and a failure-preserving record of where the approach does and does not apply.',
        'Contributions are an executable application boundary, a matched carrier/effect comparison, conditional transition-equivalence reasoning, and a failure-preserving account of contract functionality, missingness and local reproducibility. The new registered test also finds no typed increment and therefore motivates an explicitly scoped architecture/negative-results paper.')
    body=body.replace(r'\section{Conclusions}',r'\subsection{V4.3 Stop Rule and Residual Risk}'+'\n'+
        'The additional composition and anchored-audit experiment did not establish an incremental typed effect. The research owner authorized Track B when this bounded test was null. The public-fact renderer improves a shared output contract while still denying arbitrary safe prose. No further generator benchmark was run; no independent human engineering/audit study was performed. Registration does not remove the finite, author-generated nature of the corpus. The secondary completeness correction remains posthoc, and publication risk and final approval remain with the authors.\n\n'+r'\section{Conclusions}')
    back=back.replace('S1 contains historical lineage/count/exact-test reconstruction; S2 expanded task/payload/role ledgers and missing/exposure corrections; S3 typed mechanism, bounded-state and output-contract tests; S4 bilingual outcomes and official-agent compatibility traces.',
        'The V4.3 evidence bundle contains registered protocols, all new case manifests, paired composition/audit/outbox records, timing data, claim maps and analysis receipts. Prior V4.2 S1--S4 artifacts remain separate historical evidence. The expanded appendices give formal assumptions, complete program catalogs, trace excerpts, restoration procedures and reviewer risks.')
    back=back.replace('ChatGPT/Codex assisted implementation, orchestration, analysis and drafting.',
        'ChatGPT/Codex assisted implementation, experiment design and orchestration, analysis, drafting and local visual self-review. V4.3 used no new model inference; its test programs are author-generated, not an independent human red team.')
    journal=re.sub(r'\\keyword\{.*?\}',lambda m:r'\keyword{'+KEYWORDS+'}',journal,count=1)
    pre=re.sub(r'\\noindent\\textbf\{Keywords:\}[^\n]*',lambda m:r'\noindent\textbf{Keywords:} '+KEYWORDS,pre,count=1)
    for folder,wrapper,name in [('journal',journal,'HETE_JOURNAL_V4_3.tex'),('preprint',pre,'HETE_PREPRINT_V3.tex')]:
        directory=TASK/'paper'/folder
        write(directory/name,wrapper);write(directory/'manuscript_body_v4_3.tex',typography(body));write(directory/'publication_statements.tex',back)
        write(directory/'extended_methods.tex',typography((TASK/'source/extended_methods.tex').read_text()))
        write(directory/'v4_3_results.tex',typography(results(summary)));write(directory/'appendices_v4_3.tex',typography(appendix()))
        (directory/'references_clean.bib').write_bytes(bib)
        for name,data in oldfigs.items():(directory/name).write_bytes(data)
        for file in (TASK/'figures').glob('*.pdf'):shutil.copy2(file,directory/file.name)
    write(TASK/'manifests/MANUSCRIPT_SOURCE_MAP.json',{'freeze':FREEZE,'abstract_words':len(ABSTRACT.split()),'keywords':len(KEYWORDS.split(';')),
        'V4_2_body_from_verified_sealed_ZIP':True,'new_summary_sha256':sha(TASK/'data/statistics/SUMMARY.json'),
        'shared_body_sha256':sha(TASK/'paper/journal/manuscript_body_v4_3.tex'),'preprint_first':'planned not posted',
        'note':'Internal preprintV3 is not a claim of3 public server versions;rights and author declarations remain HOLD'})
    print('manuscript generated;abstract',len(ABSTRACT.split()),'words')

if __name__=='__main__':main()
