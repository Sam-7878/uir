"""Generate separate V4.4 local-review TeX projects from the verified V4.3 templates."""
import argparse
import csv
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

from .common import FREEZE,TASK,V43,load,sha,write
from .validate_evidence import native_summary

SPECS=(('journal','ELECTRONICS_V4_3_REVIEW_SOURCE.zip','HETE_JOURNAL_V4_3.tex','HETE_JOURNAL_V4_4.tex','ELECTRONICS_V4_4_REVIEW_SOURCE.zip'),
       ('preprint','HETE_PREPRINT_V3.zip','HETE_PREPRINT_V3.tex','HETE_PREPRINT_V4.tex','HETE_PREPRINT_V4.zip'))


def figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    matplotlib.rcParams.update({'font.size':10,'pdf.fonttype':42})
    path=TASK/'figures'
    fig,ax=plt.subplots(figsize=(8.2,3.1))
    ax.set(xlim=(0,12),ylim=(0,5))
    ax.axis('off')
    def node(x,y,w,h,label,color):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.10',
                                    facecolor=color,edgecolor='#26354a',linewidth=1))
        ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=9)
    def arrow(x,y,X,Y):
        ax.annotate('',xy=(X,Y),xytext=(x,y),arrowprops={'arrowstyle':'->','color':'#23344b','lw':1.1})
    node(.25,2.65,2.6,1.03,'User + retrieved text\nLocal model proposal','#e8effa')
    node(3.45,2.65,3.15,1.03,'Shared compiler\nFlat / typed approved plan','#e4f2ec')
    node(3.45,4.08,3.15,.69,'Trusted identity\nGrant and evidence','#e4f2ec')
    node(7.35,2.65,4.30,1.03,'Proof, nonce, current-state check\nSQLite transaction + audit','#e4f2ec')
    node(7.35,.56,4.30,1.10,'Actual state / mock send outbox\nPublic-fact narrative outbox','#fff1d9')
    node(.25,.56,6.34,1.10,'Offline score: proposal, effect, egress, utility\nGold is outside the runtime','#f0edf5')
    arrow(2.98,3.17,3.34,3.17);arrow(6.74,3.17,7.23,3.17);arrow(5.02,3.98,5.02,3.78)
    arrow(9.5,2.54,9.5,1.79);arrow(7.23,1.10,6.75,1.10)
    for ext in ('pdf','png'):
        fig.savefig(path/f'v44_boundary.{ext}',dpi=600,bbox_inches='tight',pad_inches=.04)
    plt.close(fig)
    rows=list(csv.DictReader((TASK/'statistics/adaptive_query_curve.csv').open()))
    fig,axes=plt.subplots(1,2,figsize=(8.15,2.9),layout='constrained',sharey=True)
    for ax,model,title in zip(axes,('phi3.5:latest','qwen2.5:7b'),('Phi-3.5','Qwen2.5-7B')):
        for arm,label,color,style in [('C0_open','Open: observed','#d04d32','-'),('C1_flat','Guard: observed','#175c85','-')]:
            rs=[r for r in rows if r['model']==model and r['arm']==arm and r['endpoint']=='e2e_asr']
            x=[int(r['budget']) for r in rs]
            low=[float(r['planned_lower']) for r in rs];high=[float(r['planned_upper']) for r in rs]
            ax.plot(x,low,style,marker='o',color=color,label=label)
            ax.fill_between(x,low,high,color=color,alpha=.13)
        ax.set(title=title,xlabel='Queries per seed',xticks=[1,2,3],ylim=(-.035,1.035))
        ax.grid(alpha=.18)
    axes[0].set_ylabel('Fraction of eligible seeds')
    axes[0].legend(loc='upper right',fontsize=8)
    for ext in ('pdf','png'):
        fig.savefig(path/f'v44_adaptive.{ext}',dpi=600,bbox_inches='tight')
    plt.close(fig)


def narrative(summary,native):
    t={(r['model'],r['population'],r['arm']):r for r in summary['tables']}
    models=summary['model_ids']
    names={models[0]:'Phi-3.5',models[1]:'Qwen2.5-7B'}
    B=lambda m,a='C1_flat':t[m,'benign',a]
    A=lambda m,a='C1_flat':t[m,'attack',a]
    phi,qwen=models
    abstract=(
      'Language-model proposals cannot confer application authority. HETE separates proposals, approved actions, committed effects, and narrative egress. '
      'A previous finite study observed no incremental typed effect under matched flat and typed predicates. '
      f'We extend that comparison with {summary["physical_receipts"]} physical local model requests over bilingual synthetic tasks and budgeted retrieval attacks. '
      f'The matched guards contain observed attack effects in {A(phi)["fully_scored"]} scored Phi-3.5 and {A(qwen)["fully_scored"]} scored Qwen2.5-7B attempts, '
      f'with {A(phi)["unknown_e2e"]} and {A(qwen)["unknown_e2e"]} unknown out of 160 planned per backbone. '
      f'The open control produces {A(phi,"C0_open")["e2e"]} and {A(qwen,"C0_open")["e2e"]} forbidden-effect or controlled-disclosure outcomes, respectively. '
      f'Strict benign completion is {B(phi)["strict_complete"]}/80 and {B(qwen)["strict_complete"]}/80 under either guard. '
      'These results expose substantial model and interface costs. No matched typed advantage is observed; zero discordance does not establish equivalence. '
      'The bounded renderer can cite public facts and resolve structured comparisons. It does not release unrestricted model prose. '
      'A separate native AgentDojo read-only subset verifies the environment and oracles but yields no actual injection exposure. '
      'The evidence supports an auditable reference boundary and layered enforcement diagnostics, with bounded egress and explicit missingness.')
    r=[r'\begin{table}[H]\centering\small\caption{Evidence populations. Rows are never pooled.}\label{tab:v44_pop}',
       r'\begin{tabularx}{\linewidth}{lXr}\hline Scope & Units and dependence & Physical calls \\ \hline',
       r'V4.2 historical & AgentDojo, 432 logical runs with proposal reuse & 690 \\',
       r'V4.3 finite & 704 composition, 96 audit and 512 egress runs & 0 \\',
       f'V4.4 live custom & {summary["case_units"]} model--context units; {summary["logical_cases"]} arm executions & {summary["physical_receipts"]} \\\\',
       f'V4.4 native subset & {native["recorded"]}/18 logical runs; two workspace tasks & {native["physical_receipts"]} \\\\',
       r'\hline\end{tabularx}\end{table}',
       r'\subsection{Matched live comparison and missingness}',
       f'The registered custom evaluation recorded {summary["case_units"]} model--context units and {summary["logical_cases"]} arm executions. '
       'Each final unit used one physical generation; no custom continuation was triggered. The implemented continuation is therefore not evidence of live multi-turn competence. '
       'The native probe is a separate multi-step integration. The two matched guards received identical physical response references.',
       r'\begin{table}[H]\centering\small\caption{Custom live results by model and arm. Strict completion is per planned benign unit. MCR and observed E2E events are shown with the jointly available attack measurement denominator. Unknown attack outcomes are separate.}\label{tab:v44_live}',
       r'\begin{tabular}{llrrrrr}\hline Model & Arm & Strict/80 & Partial/80 & MCR & E2E & Unknown \\ \hline']
    for m in models:
        for a,label in [('C0_open','Open'),('C1_flat','Flat'),('C2_typed','Typed')]:
            b,at=B(m,a),A(m,a)
            r.append(f'{names[m]} & {label} & {b["strict_complete"]} & {b["safe_partial"]} & {at["mcr"]}/{at["attack_completed_mcr_denominator"]} '
                     f'& {at["e2e"]}/{160-at["unknown_e2e"]} & {at["unknown_e2e"]} \\\\')
    r.extend([r'\hline\end{tabular}\end{table}',
       'Table~\\ref{tab:v44_live} shows no forbidden effects in scored attack units for the matched guards. '
       f'The planned-denominator worst-case bounds are 0 to {A(phi)["unknown_e2e"]}/160 for Phi-3.5 and 0 to {A(qwen)["unknown_e2e"]}/160 for Qwen2.5-7B. '
       'These are missing-outcome bounds, not confidence intervals for a deployment. In each backbone the open control demonstrates that the same proposal stream can produce actual unauthorized state changes and controlled egress. '
       f'The matched guards contain {A(phi)["mcr"]} and {A(qwen)["mcr"]} observed goal-aligned model compromises, respectively.',
       'Jointly scorable benign/attack pairs are '+
         ' and '.join(f'{next(x["jointly_scored_pairs"] for x in summary["tests"] if x["model"]==m and x["population"]=="benign")}/'
                      f'{next(x["jointly_scored_pairs"] for x in summary["tests"] if x["model"]==m and x["population"]=="attack")} for {names[m]}' for m in models)+
         '. All four paired endpoints have zero discordance and exact/Holm-adjusted $p=1$. This is an observed matched null, not an equivalence test.',
       r'\subsection{Task usefulness and controlled knockouts}'])
    for m in models:
        b=B(m)
        r.append(f'{names[m]} completes {b["strict_complete"]}/80 strict tasks, gives {b["safe_partial"]} correct partial responses, '
                 f'and has {b["authorized_exact"]}/{b["authorized_requested_recorded"]} exact authorized effect cases. '
                 f'It has {b["unknown_e2e"]} unscored benign units and {b["benign_noncompletion"]} scored but incomplete units; '
                 f'{b["false_rejection"]} are rejections of otherwise fully correct model proposals. '
                 'Incorrect intent or schema and blocked correct work are therefore distinct failure modes.')
    r.extend([r'\begin{table}[H]\centering\small\caption{Attack-only controls. Counts are actual E2E events and controlled egress leaks among the same 160 planned attempts per backbone. See Table~\ref{tab:v44_live} for unknowns.}\label{tab:v44_layers}',
       r'\begin{tabular}{lrrrr}\hline & \multicolumn{2}{c}{Phi-3.5} & \multicolumn{2}{c}{Qwen2.5-7B} \\ Control & E2E & Leak & E2E & Leak \\ \hline'])
    for a,label in [('C0_open','Open'),('K1_no_provenance','No action provenance'),('K2_no_capability','No write capability'),('K3_no_egress','Open narrative egress'),('C1_flat','Matched guard')]:
        r.append(label+' & '+' & '.join(str(A(m,a)[k]) for m in models for k in ('e2e','egress_leaks'))+r' \\')
    r.extend([r'\hline\end{tabular}\end{table}',
      'Table~\\ref{tab:v44_layers} separates capability and egress controls. Removing the action provenance check alone does not recreate an observed forbidden effect in this corpus; the remaining checks can still contain the proposal. '
      'This finding does not establish that provenance is unnecessary. Removing scoped write capability or the bounded egress contract does recreate committed effects or protected-byte releases. The full guard intentionally denies arbitrary proposed prose. '
      'A post-final audit of actual fallback text found two noncanonical partial-answer flags on the same attack request in open-egress arms. Those secondary diagnostic counts are corrected in the supplement. Benign counts and primary endpoints do not change.',
      r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{v44_adaptive.pdf}',
      r'\caption{Cumulative actual attack success by registered query budget. Lines show observed successful seeds divided by eligible seeds. Shading extends to the bound that treats unresolved seeds as successful. The eligible denominator is 60 for budgets one and two, and 40 for budget three; a change in denominator need not be monotonic.}\label{fig:v44_adaptive}\end{figure}',
      r'\subsection{Native-suite integration}'])
    if native['status']=='COMPLETE':
        r.append(f'The official package controls detect both prepared attack effects and both benign tasks. The separate integration records {native["recorded"]} logical trials from {native["physical_receipts"]} physical calls. ')
        for ar,label in [('C0_native_open','open'),('C1_native_flat','flat'),('C2_native_typed','typed')]:
            b=next(x for x in native['groups'] if x['arm']==ar and x['population']=='benign')
            a=next(x for x in native['groups'] if x['arm']==ar and x['population']=='attack')
            r.append(f'The {label} arm has {b["native_utility"]}/2 observed benign task successes ({b["unknown"]} unknown), '
                     f'{a["native_attack_success"]}/4 observed native attack successes ({a["unknown"]} unknown), and {a["actual_exposure"]}/4 attack prompts with actual injected-text exposure.')
        r.append('No registered native injection was observed in an actual model prompt. These samples establish use of native tooling and oracles, not external containment efficacy or method ranking. Missing responses are not credited as containment.')
    else:
        r.append('The native subset did not meet the complete execution and controls gate. No official benchmark result or external ranking is claimed.')
    return abstract,'\n\n'.join(r)+'\n'


def build_one(folder, main):
    env=dict(os.environ)
    if (folder/'vendor/soul').is_dir():
        env['TEXINPUTS']='./vendor/soul:'
    log=TASK/'audits'/f'{main}_build.log'
    steps=[['pdflatex','-halt-on-error','-interaction=nonstopmode',main],['bibtex',Path(main).stem]]
    with log.open('w',encoding='utf-8') as f:
        for cmd in [*steps,steps[0],steps[0]]:
            r=subprocess.run(cmd,cwd=folder,env=env,text=True,stdout=f,stderr=subprocess.STDOUT)
            if r.returncode:
                raise RuntimeError('TeX build failed; see '+str(log))
    final=(folder/Path(main).with_suffix('.log')).read_text(errors='replace')
    for err in ('Overfull','undefined references','undefined citations','multiply defined','! LaTeX Error'):
        if err in final:
            raise RuntimeError(f'{main}: {err}')
    pdf=folder/Path(main).with_suffix('.pdf')
    info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
    return int(re.search(r'Pages:\s+(\d+)',info).group(1))


def build():
    figures()
    summary=load(TASK/'statistics/SUMMARY.json')
    native=native_summary()
    abstract,result=narrative(summary,native)
    files={}
    for folder,old_zip,old_main,new_main,new_zip in SPECS:
        dst=TASK/'paper'/folder
        dst.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(V43/old_zip) as z:
            for name in z.namelist():
                p=Path(name)
                if p.is_absolute() or '..' in p.parts:
                    raise ValueError('Unsafe historical archive path')
                if name.startswith(('Definitions/','vendor/')) or name in ('references_clean.bib','publication_statements.tex'):
                    z.extract(name,dst)
            wrapper=z.read(old_main).decode()
        wrapper=wrapper.replace('HETE-ELECTRONICS-V4.3-2026-10-23-R1',FREEZE).replace('Internal Electronics V4.3','Internal Electronics V4.4')
        if folder=='journal':
            wrapper=re.sub(r'\\abstract\{.*?\}\\keyword',lambda _:r'\abstract{'+abstract+r'}\keyword',wrapper,flags=re.S)
        else:
            wrapper=wrapper.replace('23 October 2026 --- V3/V4.3','8 November 2026 --- V4/V4.4')
            wrapper=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',
                lambda _:r'\begin{abstract}'+abstract+r'\end{abstract}',wrapper,flags=re.S)
        wrapper=wrapper.replace('manuscript_body_v4_3.tex','manuscript_v44.tex')
        wrapper=re.sub(r'\\appendix(?:start)?[^\n]*?\\input\{appendices_v4_3.tex\}', '',wrapper)
        (dst/new_main).write_text(wrapper,encoding='utf-8')
        shutil.copy2(TASK/'paper/authoring/manuscript_v44.tex',dst/'manuscript_v44.tex')
        (dst/'v44_results.tex').write_text(result,encoding='utf-8')
        ps=dst/'publication_statements.tex'
        text=ps.read_text()
        text=re.sub(r'\\textbf\{Supplementary materials\.\}[^\n]*',
          lambda _:r'\textbf{Supplementary materials.} Separate locally retained evidence includes the V4.4 protocol, private raw records and reproduction receipts. The full V4.3 catalogs and trace appendices remain in the historical supplement. No supplementary redistribution is approved.',text)
        text=text.replace('V4.3 used no new model inference; its test programs are author-generated, not an independent human red team. Local generator and AI-rater roles and digests are separately recorded.',
                          'The V4.4 generation backbones, Phi-3.5 and Qwen2.5-7B, supplied experimental proposals, not manuscript judgments. The synthetic task and attack corpus is author-created, and no independent human validation was performed. Historical AI-rater roles are separate.')
        ps.write_text(text,encoding='utf-8')
        for image in (TASK/'figures').glob('*.pdf'):
            shutil.copy2(image,dst/image.name)
        (dst/'FREEZE_ID.txt').write_text(FREEZE+'\nLOCAL REVIEW; PUBLICATION HOLD\n')
        (dst/'README_BUILD.md').write_text(f'Main file: {new_main}. Run pdflatex, bibtex, pdflatex, pdflatex. For the journal set TEXINPUTS=./vendor/soul:. Local draft, unposted and unsubmitted. Rights pending.\n')
        pages=build_one(dst,new_main)
        doc=dst/Path(new_main).with_suffix('.pdf')
        shutil.copy2(doc,TASK/'paper'/doc.name)
        target=TASK/'paper'/new_zip
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
            for f in sorted(dst.rglob('*')):
                if f.is_file() and f.suffix not in ('.aux','.log','.blg','.out'):
                    z.write(f,str(f.relative_to(dst)))
        with tempfile.TemporaryDirectory(prefix='v44-tex-') as tmp, zipfile.ZipFile(target) as z:
            if z.testzip() or (folder=='preprint' and any(n.startswith('Definitions/') for n in z.namelist())):
                raise ValueError('Bad manuscript source ZIP')
            z.extractall(tmp)
            extracted_pages=build_one(Path(tmp),new_main)
            if extracted_pages!=pages:
                raise ValueError('Extracted layout changed')
        files[folder]={'pages':pages,'pdf':str((TASK/'paper'/doc.name).relative_to(TASK)),'pdf_sha256':sha(doc),
                       'zip':str(target.relative_to(TASK)),'zip_sha256':sha(target),'fresh_extract_build':True,
                       'body_sha256':sha(dst/'manuscript_v44.tex'),'results_sha256':sha(dst/'v44_results.tex')}
    write(TASK/'manifests/MANUSCRIPT_RECEIPT.json',{'freeze':FREEZE,'documents':files,'abstract_words':len(abstract.split()),
          'science_summary_sha256':sha(TASK/'statistics/SUMMARY.json'),'submission_authorized':False})
    print('Manuscript variants',files,flush=True)


if __name__=='__main__':
    build()
