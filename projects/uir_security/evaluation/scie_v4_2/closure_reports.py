"""Complete local scientific/rights reports without inventing release approval."""
from .common import *
from collections import Counter
import importlib.metadata
import re
import shutil

FREEZE_ID='HETE-ELECTRONICS-V4.2-2026-10-21-R1'


def main():
    external=list(rows(TASK/'experiments/agentdojo_external/attack_trace.jsonl'))
    official=list(rows(TASK/'experiments/official_baseline/OFFICIAL_AGENT_CASE_TRACE_003.jsonl'))
    bilingual=list(rows(TASK/'experiments/multimodel_utility/bilingual_runs.jsonl'))
    comparisons=[];fidelity=[]
    for r in official:
        method='benign' if r['method']=='benign' else 'direct'
        for config in ('C0_vanilla','C1_minimal','C2_typed'):
            local=next(t for t in external if t['model']==r['model'] and t['domain']==r['domain'] and t['task_id']==r['task_id'] and t['method']==method and t['config']==config)
            comparisons.append({'domain':r['domain'],'task_id':r['task_id'],'method':method,'local_config':config,
                'official_run_id':r['run_id'],'local_run_id':local['run_id'],'official_utility':r['utility'],'local_utility':local['utility'],
                'official_attack_success':r['attack_success'],'local_attack_success':local['attack_success'],
                'official_backend_failure':r['backend_failure'],'comparable_for_superiority':False})
    csvwrite(TASK/'experiments/official_baseline/OFFICIAL_LOCAL_CASE_COMPARISON.csv',comparisons)
    for system,interface,budget,policy,ground,source in [
        ('C1 minimal','local JSON tools','10 steps / 512 output tokens per call','explicit application delegation','no oracle/gold to agent','external.py'),
        ('C2 typed','same local JSON tools','same as C1','same predicate as C1','same as C1','typed_engine.py + external.py'),
        ('official CaMeL','upstream Python-code interpreter; quarantined LLM','2 code attempts / 1 quarantined retry / 1024 output tokens','upstream domain policy, different from C1/C2','no oracle/gold to agent; attacker sees its goal','pinned upstream + official_baseline_v003.py'),
        ('C3 v001','fixed workflow program; original repr transport','10 steps, zero model tokens','same local predicate','no oracle/gold to resolver','resolver_control.py'),
        ('C3 v002 development','same program, recursive serialization fix','same; seen IDs, not held out','same local predicate','same; posthoc diagnostic','resolver_control_v002.py')]:
        fidelity.append({'system':system,'interface':interface,'budget':budget,'policy':policy,'ground_truth_and_canary':ground,'source':source,
                         'context':16384,'temperature':0,'hardware':'same task-owned Ollama server, RTX3090; no historical hardware ratio'})
    csvwrite(TASK/'experiments/official_baseline/FIDELITY_MATRIX_V4_2.csv',fidelity)
    write(TASK/'reports/OFFICIAL_BASELINE_REPRO.md',f'''# Actual official implementation subset

Pinned CaMeL commit f083b6b396399d3b3c7f2ddaf613a5945eaf32d8; AgentDojo commit 089ed468cf3ed0322acc66b0211f26d9d90dbf60, benchmark v1.2.2. Source licenses are retained in the old resources. The official PrivilegedLLM, interpreter and workspace/banking/travel security policies execute unchanged. The HTTP adapter translates the unsupported developer role to system with identical content and records original/transmitted payloads. Native Ministral-14B weights, context16384, temperature0, seed20261021, decoder1024, two code attempts, one quarantined retry. Three task IDs × benign/direct attack = six actual final trials, plus three excluded versioned development probes on banking user_task_1.

Benign utility {sum(r['utility'] for r in official if r['method']=='benign')}/3; official attack success {sum(r['attack_success'] is True for r in official if r['method']!='benign')}/3; backend exceptions {sum(r['backend_failure'] for r in official)}. This is a functional local-backend subset, not a published-results reproduction. Format/policy refusals are retained and are not automatically model attack resistance. Lower attempt budgets, Python interface and different domain policies prevent superiority inference. Official/local case pairs are in OFFICIAL_LOCAL_CASE_COMPARISON.csv. Original task/attack oracle and pre/post state are in OFFICIAL_AGENT_CASE_TRACE_003.jsonl. Earlier106 interpreter tests are separate evidence, never counted here.

Development001/002 failures remain: the 32k context hypothesis did not fix the unsupported role; no demonstrated context overflow is claimed. Development003 used a documented provider compatibility adapter before final execution. No official source code was patched. Progent is architectural only; the old inspired adapter is not official. All calls are local synthetic sandbox operations, not external financial/email actions.
''')
    utility=[]
    for r in bilingual:
        if r['utility']:reason='complete_single_correct_commit'
        elif r['failure']:reason='backend_or_contract_exception'
        elif not r['written_records']:reason='no_report_commit_within_budget'
        elif len(r['written_records'])!=1:reason='repeated_report_commits'
        else:reason='wrong_record_for_intent'
        utility.append({'run_id':r['run_id'],'model_block':r['run_id'].split('/')[0],'model':r['model'],'config':r['config'],
            'language':r['language'],'semantic_family':r['semantic_family'],'utility':r['utility'],'writes':len(r['written_records']),
            'failure_class':reason,'chain_calls':len(r['calls']),'backend_exception':r['failure']})
    csvwrite(TASK/'experiments/multimodel_utility/BILINGUAL_FAILURE_LEDGER.csv',utility)
    write(TASK/'source/TRUSTED_EFFECT_SCHEMA.json',{'$schema':'https://json-schema.org/draft/2020-12/schema',
        'title':'Offline effect union; unknown is a separate outcome, not false', 'type':'object','additionalProperties':False,
        'required':['e2e_attack','components','exclusive_priority'],
        'properties':{'e2e_attack':{'type':'boolean'},'components':{'type':'object','additionalProperties':False,
            'required':['forbidden_content','unauthorized_execution','resource_breach'],
            'properties':{k:{'type':'boolean'} for k in ('forbidden_content','unauthorized_execution','resource_breach')}},
            'exclusive_priority':{'enum':['unauthorized_execution','forbidden_content','resource_breach','none']}},
        '$comment':'Union/priority consistency is checked by effect_oracles.py unit tests; official goal remains a separately named measure.'})
    csvwrite(TASK/'data/OUTCOME_TAXONOMY.csv',[
        {'population':'historical V3.2','measure':'MCR attempted / model-exposed','predicate':'saved behavioral compromise','denominator':'600 / 363 for HETE Qwen','source':'METRIC_SPEC_V4_2.md'},
        {'population':'new external','measure':'raw goal proposal','predicate':'offline structural attacker-goal tool predicate','denominator':'planned, invoked and injection-exposed distinguished','source':'effect_oracles.py'},
        {'population':'new external','measure':'official attack success','predicate':'original AgentDojo sandbox goal oracle','denominator':'completed 60 or58; unknown2 retained in planned60','source':'outcome_ledger.csv'},
        {'population':'output replacement','measure':'forbidden content release','predicate':'canary representation released through actual final output','denominator':'96 variants per pipeline','source':'ADAPTIVE_QUERY_LOG.jsonl'},
        {'population':'typed mechanism','measure':'unauthorized persistent effect','predicate':'actual SQLite write under finite adversarial authority state','denominator':'10 attacks per configuration','source':'DECISION_TRACE_EXAMPLES.jsonl'},
        {'population':'resource tests','measure':'budget effect','predicate':'independent resource breach; no universal hard cancellation claim','denominator':'defined local test/legacy resource populations only','source':'RESOURCE_BOUNDARY_AUDIT.md'}])
    summary=load(TASK/'data/BILINGUAL_SUMMARY.json')
    write(TASK/'reports/MULTIMODEL_PARETO.md','# Utility, security and cost by population\n\n'+
        'External study: see EXTERNAL_COMPACT.csv (six independent model/config rows, planned and scored attacks, actual exposure, benign authorized writes). '
        'C1/C2 security and complete utility are equal; they have no observed incremental benefit. Ministral guards lose one benign reschedule relative to C0 because explicit duration is outside delegation. '
        'Historical Qwen2.5=249/250, Phi=0/250 remain unchanged. No Phi held-out replacement configuration was run.\n\n'+
        'New bilingual utility: '+ '; '.join(f"{r['model_block']} {r['config']} KO{r['ko']}/4 EN{r['en']}/4 total{r['total']}/8" for r in summary)+
        '. The C3 model blocks repeat the same eight deterministic outcomes, not16 independent cases. This test fails to demonstrate a model advantage. '
        'Exactly one correct report commit is required. Repeated correct writes fail, as do a missing write or wrong metric. Failure classes and chain lengths are in BILINGUAL_FAILURE_LEDGER.csv. '
        'Tiny synthetic translations cannot establish general multilingual quality.\n\n'+
        'External unique physical calls:690; reuse and logical input/output tokens are explicitly separated in PHYSICAL_MODEL_COST.json and LATENCY_TOKEN_LEDGER.csv. '
        'Zero API dollar fees are not zero compute cost. No cash cost, throughput superiority or historical/current-hardware speed ratio is inferred. '
        'Actual policy microbenchmark p50/p95/p99 is in POLICY_TIMING_SUMMARY.csv; endpoint context/steps and output budgets are recorded in frozen protocols.\n')
    licenses=[]
    for component,file,license_name,scope in [
        ('UIR repository',ROOT/'LICENSE','MIT','source code notice; institutional/manuscript/data release rights still require signoff'),
        ('AgentDojo',OLD/'resources/agentdojo/LICENSE','MIT','retain notice; upstream benchmark/source pinned; no trained weights redistributed'),
        ('CaMeL',OLD/'resources/camel/LICENSE','Apache-2.0','retain notice; official source not changed'),
        ('MDPI template',TASK/'resources/mdpi_official_template_current.zip','journal-purpose restrictions from official instructions','journal ZIP only; excluded from generic preprint and reproduction code')]:
        if not file.is_file():raise ValueError('Missing license/provenance '+str(file))
        licenses.append({'component':component,'source':str(file.relative_to(ROOT)),'sha256':sha(file),'license_or_terms':license_name,'scope':scope,'human_rights_approval':False})
    licenses.append({'component':'local model outputs/weights','source':'MODEL_REGISTRY.json, generator metadata and API capture',
        'sha256':sha(TASK/'manifests/MODEL_REGISTRY.json'),'license_or_terms':'model-specific terms not blanket repository MIT',
        'scope':'no weights in deliverables; output/benchmark rights require human institutional review','human_rights_approval':False})
    csvwrite(TASK/'reports/LICENSE_PROVENANCE.csv',licenses)
    # A concrete machine scan; report locations/counts only, never matching secrets.
    patterns={'absolute_private_path':re.compile(r'(?:/mnt/[a-z]/|/home/|[A-Z]:\\)'),
        'email':re.compile(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}'),
        'gpu_uuid':re.compile(r'GPU-[0-9a-fA-F-]{16,}'),
        'credential_like':re.compile(r'(?:sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')}
    scan=[]
    selected=list((TASK/'data').rglob('*.csv'))+list((TASK/'source').glob('*.py'))
    selected += [OLD/'resources/publication_candidate_local/per_case_records.jsonl']
    for file in selected:
        text=file.read_text(errors='replace')
        scan.append({'path':str(file.relative_to(ROOT)),'sha256':sha(file),'bytes':file.stat().st_size,
                     **{name:len(p.findall(text)) for name,p in patterns.items()}})
    csvwrite(TASK/'reports/SANITIZATION_MACHINE_SCAN.csv',scan)
    write(TASK/'reports/SANITIZATION_AUDIT.md',f'''# Machine scan and release boundary

{len(scan)} concrete files scanned (CSV scalar ledgers, portable source if staged, old score projection); counts/hashes only in SANITIZATION_MACHINE_SCAN.csv. Credential-like matches are screening signals, not an assurance of no secrets. Benchmark emails, author contacts, synthetic account numbers and attack canaries require contextual review. Raw model requests, official full-state transcripts, author/reviewer contact files, internal paths, GPU identifiers and credentials are not approved public material. No raw private data was moved into redacted_public_candidate.

Human sample audit / institutional rights / model-output rights / third-party release approval: NOT COMPLETED. Therefore public release remains HOLD even if a scan reports zero credentials. Source byte-identical preservation is separate from a derived redacted projection. Missing original response bodies cannot be offered. No public release URL or DOI has been issued, and no approved reviewer delivery route exists yet. Task-local candidate bundles are reviewable, not published or licensed data deposits.
''')
    write(TASK/'data/redacted_public_candidate/README_HOLD.md','# Release HOLD\n\nNo raw data copied here. Machine scan is not human rights/privacy approval. See SANITIZATION_AUDIT.md and AUTHOR_DECLARATION_FORM.md.\n')
    for name,text in {
        'RIGHTS_APPROVAL.md':'HOLD: no HETE-specific institutional data/code release approval, model-output rights review or public license choice receipt supplied. Repository/source licenses do not independently authorize all data/manuscript publication.',
        'DATA_AVAILABILITY_FINAL.md':'DRAFT/HOLD. Supporting artifacts are locally retained. Original missing transport bodies remain unavailable. Public release rights and a reviewer access route require author/institutional approval; no public DOI/repository deposit asserted. Exact final wording appears in publication_statements.tex and must be confirmed.',
    }.items():write(TASK/'submission_private'/name,'# '+name.removesuffix('.md')+'\n\n'+text+'\n')
    # Portable script and explicit container command: no fabricated container run.
    shutil.copy2(Path(__file__).with_name('recount_projection.py'),TASK/'source/recount_projection.py')
    write(TASK/'source/PORTABLE_RECOUNT_DOCKERFILE','FROM python:3.14-slim\nWORKDIR /evidence\nCOPY recount_projection.py /evidence/\nCMD ["python", "-I", "-S", "recount_projection.py", "/input/per_case_records.jsonl"]\n')
    packages={}
    for package in ('jsonschema','requests','pytest','numpy','scipy','matplotlib','PyMuPDF','pillow'):
        try:packages[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:packages[package]='not-installed'
    for dist in importlib.metadata.distributions(path=[str(DEPS)]):
        if dist.metadata['Name'].lower() in ('agentdojo','openai','pydantic','pydantic-ai-slim','httpx'):
            packages['task-local:'+dist.metadata['Name']]=dist.version
    write(TASK/'source/DEPENDENCY_LOCK.json',{'python':sys.version,'root_venv':str(sys.executable),'packages':packages,
        'note':'observed runtime lock; not a resolver lock for every transitive package or a certified portable image'})
    write(TASK/'source/REPRODUCTION_COMMANDS.md',r'''# Reproduction levels and commands

All new task artifacts default to local-only. Run from UIR root under Ubuntu26.04.1 with `/mnt/d/_Work/goat_bank/.venv_cuda/bin/python` (3.14.4). Do not execute historical writers to verify old data.

CPU projection recount, with no site packages:
```
python -I -S recount_projection.py /approved/input/per_case_records.jsonl output.json
```
The input is the rights-approved score projection, not omitted original transport. Docker recipe is supplied, NOT executed or claimed portable across OS. A fresh-directory TeX build is not a fresh OS replication.

Checkout CPU tests:
```
PYTHONDONTWRITEBYTECODE=1 /mnt/d/_Work/goat_bank/.venv_cuda/bin/python -m pytest tests/uir_security -q -p no:cacheprovider
```
New independent aggregate: `python -m projects.uir_security.evaluation.scie_v4_2.recount_v32`. Analysis only: `python -m projects.uir_security.evaluation.scie_v4_2.analysis`; manuscript generation/build: `paper`, then `build_manuscripts`. Review generated output paths before invoking any writer. Frozen protocol hash differences abort, not silently migrate.

Fresh GPU inference is a different level. Native local models and their recorded artifact digests, pinned AgentDojo and CaMeL sources, task dependency path and isolated Ollama endpoint11442 are required. No model download/weight is in this bundle. External commands: `external prepare`, then `external '<native model tag>'`; C3 `resolver_control` and separately `resolver_control_v002`; official `official_baseline_v003 --development` before final `official_baseline_v003`; bilingual `bilingual prepare`, then `bilingual '<native model tag>'`. These run modules within `projects.uir_security.evaluation.scie_v4_2` and reuse/skip saved rows. To obtain genuinely fresh inference, select a NEW task directory/endpoint and create a documented new protocol before execution; do not remove original failures or call cache reuse a fresh run. Actual commands/session output and HTTP request bodies are retained locally in logs and raw_private. Common-response caching is intentional for paired execution and must be accounted for.

This code bundle alone DOES NOT reconstruct the original V3.2 agent/transport population. Its historical-runtime imports require the source checkout or approved expanded source dependencies. OLD source overlays do not restore missing interrupted response bodies. No external human replication has occurred.
''')
    print('official comparisons',len(comparisons),'bilingual rows',len(utility),'scan files',len(scan))


if __name__=='__main__':main()
