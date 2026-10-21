"""Bind manuscript statements/figures to saved data, without new inference."""
import csv
import json
import os
import shutil
from pathlib import Path

from .common import FROZEN, TASK, csv_write, load, sha, write


def main():
    body=(TASK/'manuscript_private/manuscript_body.tex').read_text()
    abstract=(TASK/'manuscript_private/HETE_PREPRINT_V1.tex').read_text()
    baseline=load(FROZEN/'baseline_comparison.json');phi=load(FROZEN/'multi_model_results.json')['phi3.5:latest']
    rows=[];failures=[]
    expected=[('Qwen E2E',baseline['HETE']['e2e']['count'],0,'baseline_comparison.json/HETE/e2e'),
              ('Qwen utility',baseline['HETE']['utility']['count'],249,'baseline_comparison.json/HETE/utility'),
              ('Phi MCR',phi['mcr']['count'],3,'multi_model_results.json/phi/mcr'),
              ('Phi E2E',phi['e2e']['count'],6,'multi_model_results.json/phi/e2e'),
              ('Phi utility',phi['utility']['count'],0,'multi_model_results.json/phi/utility')]
    for claim,actual,written,source in expected:
        rows.append({'claim':claim,'actual':actual,'written':written,'source':source,'matched':actual==written})
    funnel=load(TASK/'data/funnel_audit.json')['counts']
    for key,n in [('attack_attempted',600),('llm_invoked',363),('output_guard_rejected',176),
                  ('action_gate_rejected',68),('trusted_effect_committed',0)]:
        rows.append({'claim':key,'actual':funnel[key],'written':n,'source':'data/funnel_audit.json','matched':funnel[key]==n})
    with (TASK/'data/outer_boundary_summary.csv').open() as stream:outer=list(csv.DictReader(stream))
    for row,n in zip(outer,[40,0,120],strict=True):
        rows.append({'claim':row['configuration']+' outer leak','actual':int(row['forbidden_egress']),'written':n,
                     'source':'data/outer_boundary_summary.csv','matched':int(row['forbidden_egress'])==n})
    with (TASK/'data/full_pipeline_replacement_summary.csv').open() as stream:full={r['configuration']:r for r in csv.DictReader(stream)}
    for key,n in [('V4_original',1),('V4_1_canonical',0),('no_both_action_checks',5),('no_output',11)]:
        rows.append({'claim':key+' full pipeline','actual':int(full[key]['forbidden']),'written':n,
                     'source':'data/full_pipeline_replacement_summary.csv','matched':int(full[key]['forbidden'])==n})
    for phrase in ('utility $249/250$','E2E $6/600$','utility $0/250$',
                   'not a claim that all 736 original manifest entries pass','Human validation remains false'):
        if phrase not in body:failures.append('expected manuscript scope/number missing: '+phrase)
    if 'Preprint. Not peer-reviewed.' not in abstract:failures.append('preprint status')
    for r in rows:
        if not r['matched']:failures.append(r['claim'])
    csv_write(TASK/'data/CLAIM_NUMERIC_CROSSCHECK.csv',rows)
    write(TASK/'manifests/CLAIM_AUDIT.json',{'passed':not failures,'failures':failures,
          'source_sha256':sha(TASK/'manuscript_private/manuscript_body.tex'),
          'numeric_statements_checked':len(rows),'scope':'curated key statements plus generated historical and pilot tables; not automatic semantic proof of all prose'})
    write(TASK/'reports/HETE_CLAIMS_LEDGER.md','# Claim-to-evidence ledger\n\n'
          '| Claim | Evidence | Permitted wording / limit |\n|---|---|---|\n'
          '| Historical security/utility | TABLE_RECONCILIATION.csv, standalone REPLAY_RESULT.json | Exact original denominators, including adverse Phi; no universal security |\n'
          '| Funnel containment | funnel_audit.json with original IDs | Overlapping gate indicators; only 363/600 attacks invoked the model |\n'
          '| Statistical difference | exact_statistics_recomputed.json | Five paired E2E comparisons, Holm; local inspired baselines only |\n'
          '| 0/600 uncertainty | per_class_language_intervals.csv, cluster_sensitivity.csv | Conditional Wilson upper 0.6362%; no unseen-task bound |\n'
          '| Source integrity | frozen_recovery_receipt.json, SCOPED_RELEASE_VERIFICATION.json | 418 non-bytecode entries with explicit overlay; full original manifest fails |\n'
          '| Compromised-model boundary | model_substitution_traces.jsonl, full_pipeline_replacement.jsonl | Original encoded failure retained; new V4.1 narrow application guard, finite test only |\n'
          '| Adaptive/outer check | attack_trace.jsonl, outer_boundary_traces.jsonl | Direct white-box output search and synthetic new fixture; not published attack-agent reproduction |\n'
          '| External benchmark | benchmark_results.jsonl, public_benchmark_domain_results.csv | 48 real official-environment trials, four read-only tasks; two models; actual exposure separate |\n'
          '| Incremental typed contribution | minimal vs typed pilot; no_llm_control_summary.json | No incremental security/utility benefit established; deterministic fixture directly solvable |\n'
          '| AI review | ai_labels_R1/R2.jsonl, ai_judge_agreement.json | 500 independently executed annotations; human_validation=false, not oracle accuracy |\n'
          '| Phi format compatibility | phi_dev_runs.jsonl | New transcription dev probe 12/12 each format; not held-out retuning success |\n'
          '| Runtime guarantees | RESOURCE_SEMANTICS.md, tool_trace_report.md | Checkpoints and local SQLite transactions; no hard cancellation or distributed rollback |\n'
          '| Public availability / author declarations | publication_gates.json | Pending; no posted/submitted/public DOI assertion |\n\n'
          'CLAIM_NUMERIC_CROSSCHECK.csv checks key hard-coded numbers against saved evidence; the historical and pilot tables are generated from JSON records. '
          'This is an internal source/evidence review, not an independent third-party review.\n')
    os.environ.setdefault('MPLCONFIGDIR',str(TASK/'resources/matplotlib_cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(9,3.8))
    for label,value in [('Qwen2.5',baseline['HETE']),('Phi-3.5',phi)]:
        x=100*value['utility']['count']/250;y=100*value['e2e']['count']/600
        axes[0].scatter(x,y,s=65);axes[0].annotate(label,(x,y),xytext=(4,9),textcoords='offset points')
    external=load(TASK/'data/public_benchmark_summary.json')
    for r in external:
        if r['config']!='typed_hete':continue
        x=100*r['benign_utility']/r['benign_n'];y=100*r['attack_success']/r['attack_n']
        label='Qwen3-4B' if 'qwen3:' in r['model'] else 'Ministral-14B'
        axes[1].scatter(x,y,s=65);axes[1].annotate(label,(x,y),xytext=(-65,9),textcoords='offset points')
    for ax,title in zip(axes,['Frozen custom: 250 benign / 600 attacks','Official-environment pilot: 4 / 4 per model'],strict=True):
        ax.set(xlabel='Complete benign utility (%)',ylabel='E2E attack success (%)',xlim=(-8,113),ylim=(-.1,1.6),title=title)
        ax.grid(alpha=.2)
    fig.suptitle('Different populations: compare models within each panel only',fontsize=10)
    fig.tight_layout();fig.savefig(TASK/'figures/backbone_tradeoff.pdf');fig.savefig(TASK/'figures/backbone_tradeoff.png',dpi=160);plt.close(fig)
    target=TASK/'resources/FIGURE_SOURCE';target.mkdir(exist_ok=True)
    shutil.copy2(Path(__file__),target/'claim_audit_and_backbone_figure.py')
    print('numeric statements',len(rows),'failures',failures)
    return int(bool(failures))


if __name__=='__main__':raise SystemExit(main())
