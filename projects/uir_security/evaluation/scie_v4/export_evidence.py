"""Prepare a LOCAL candidate supplementary payload, never upload/publish it.

Synthetic confidential fixture strings are consistently tokenized. All outcomes
are rejudged; a mismatch blocks the candidate release instead of changing labels.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter

from evaluation.llm_security_v3_2.judges.security_evaluator import SecurityEvaluatorV32
from evaluation.llm_security_v3_2.schema.oracle_case import OracleCase

from .common import FROZEN, TASK, load, rows, sha, write


def main():
    oracle={r['case_id']:r for r in load(FROZEN/'datasets/oracle.json')}
    runtime=load(FROZEN/'datasets/runtime.json')
    tokens=set()
    for rc in runtime:
        for key in ('session_secret','hidden_instruction','foreign_tenant_secret'):
            value=rc.get('session_metadata',{}).get(key)
            if isinstance(value,str) and value:
                tokens.add(value)
    redactions={value:'REDACTED_SYNTHETIC_'+hashlib.sha256(value.encode()).hexdigest()[:16] for value in tokens}
    def scrub(value):
        if isinstance(value,str):
            for secret,placeholder in redactions.items():
                value=value.replace(secret,placeholder)
            return value
        if isinstance(value,list):return [scrub(v) for v in value]
        if isinstance(value,dict):return {k:scrub(v) for k,v in value.items()}
        return value
    candidate=TASK/'resources/publication_candidate_local';candidate.mkdir(exist_ok=True)
    evaluator=SecurityEvaluatorV32();metrics=['model_compromised','e2e_attack_succeeded','complete_task_success','false_rejection']
    mismatches=[];groups=Counter();record_count=0
    with (candidate/'per_case_records.jsonl').open('w',encoding='utf-8') as output:
        for source in sorted((FROZEN/'raw_runs').glob('*.jsonl')):
            for outer in rows(source):
                records=outer['queries'] if source.stem=='adaptive' else [outer]
                for index,record in enumerate(records):
                    oc=scrub(oracle[record['case_id']]);execution=scrub(record['execution'])
                    verdict=evaluator.evaluate_case(execution,OracleCase.from_dict(oc))
                    for key in metrics:
                        if bool(verdict.get(key))!=bool(record['verdict'].get(key)):
                            mismatches.append({'run':source.stem,'case_id':record['case_id'],'metric':key})
                    projection={'run':source.stem,'case_id':record['case_id'],'system':record['system'],'model':record['model'],
                        'is_attack':record['is_attack'],'attack_class':record['attack_class'],'language':record['runtime_case']['language'],
                        'execution':execution,'verdict':scrub(record['verdict']),'oracle':oc,
                        'termination_and_counters':[{'done':c.get('response',{}).get('done'),
                             'done_reason':c.get('response',{}).get('done_reason'),'finish_reason':c.get('finish_reason'),
                             'input_tokens':c.get('input_tokens'),'output_tokens':c.get('output_tokens')} for c in record['calls']],
                        'original_record_json_sha256':hashlib.sha256(json.dumps(record,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
                        'transformation':'consistent tokenization of synthetic private-context fixture strings; not original raw bytes'}
                    if source.stem=='adaptive':
                        projection.update(campaign=outer['campaign'],seed_case_id=outer['seed_case_id'],query_number=index+1)
                    output.write(json.dumps(projection,ensure_ascii=False)+'\n');groups[source.stem]+=1;record_count+=1
    # Check no known synthetic token survives serialization.
    content=(candidate/'per_case_records.jsonl').read_text()
    leaks=[hashlib.sha256(secret.encode()).hexdigest() for secret in tokens if secret in content]
    receipt={'candidate_only':True,'public_release_authorized':False,'records':record_count,'groups':dict(groups),
             'synthetic_private_strings_tokenized':len(tokens),'known_private_string_leaks':len(leaks),
             'score_replay_mismatches':mismatches,'payload_sha256':sha(candidate/'per_case_records.jsonl'),
             'originals_modified':False,'passed':not leaks and not mismatches,
             'limits':'targeted fixture tokenization is not a guarantee that no unidentified personal or proprietary text remains; author rights/release review pending'}
    write(TASK/'manifests/sanitized_evidence_audit.json',receipt)
    write(candidate/'README.md','# Local supplementary candidate\n\n'
        'Not published. Contains a tokenized projection of the original admitted executions plus per-case oracles and recorded verdicts. '
        'Original raw generations remain in the hash-anchored V3.2 input. The projection retains tool proposals, admitted calls, executor results, mutations, released outputs, terminal statuses and actual counters. '
        'Synthetic confidential fixture values have been consistently tokenized; independently rejudged metric equality is checked in sanitized_evidence_audit.json. '
        'Full prompts and request/response transport bodies are not included in this projection; it is a score-reconstruction payload, not a byte-identical full inference replay.\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in {'groups','score_replay_mismatches'}}))
    print('score_replay_mismatches',len(mismatches))
    return 0 if receipt['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
