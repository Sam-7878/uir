"""Finite seeded adversarial property suite with retained counterexamples."""
import hashlib
import json
import random
from pathlib import Path

from evaluation.llm_security_v3_2.provenance import ProvenanceVerifier, compute_evidence_signature

from .boundary import Envelope, Session
from .common import TASK, load, sha, write
from .strict_boundary import StrictContractEnvelope


def main():
    protocol={'id':'V4-finite-properties-001','seed':20261022,'fuzz_n':1000,
        'harness_sha256':sha(Path(__file__)),
        'properties':['untrusted Unicode principal cannot grant write authority','unknown/declassification tool rejected',
                      'malformed and non-finite JSON rejected','retired/unknown signer rejected','modified body with old signature rejected'],
        'not_implemented':['production key rotation/revocation','generic declassification lattice','formal compiler proof']}
    target=TASK/'manifests/property_protocol.json'
    if target.exists() and load(target)!=protocol:raise RuntimeError('Protocol changed')
    write(target,protocol);rng=random.Random(protocol['seed']);records=[]
    authority=Session('analyst',frozenset({'write:report'}),0,frozenset({'doc-v4'}),frozenset({'PRIVATE'}))
    for i in range(1000):
        principal=''.join(rng.choices('adminAnalystаαＡ\u200b\ufeff',k=rng.randint(1,48)))
        proposal={'tool':'create_report','args':{'id':str(i),'body':'text','recipient':'internal'},
                  'principal':principal,'expected_revision':0,'nonce':str(i)}
        raw=json.dumps(proposal);engine=Envelope(authority);result=engine.commit(raw);engine.close()
        records.append({'id':f'unicode-{i}','input':raw,'oracle':'state_mutated == 0',
                        'passed':result['state_mutated']==0,'result':result})
    base={'tool':'create_report','args':{'id':'x','body':'ok','recipient':'internal'},
          'principal':'analyst','expected_revision':0,'nonce':'n'}
    for i,raw in enumerate([json.dumps(base)+s for s in ('{}',' trailing','\x00','```')]+
                           [json.dumps(base).replace('"expected_revision": 0','"expected_revision": '+v)
                            for v in ('NaN','Infinity','true','-1','0.0','null')]+
                           [json.dumps({**base,'tool':v}) for v in ('declassify','ｍodify_roles','modify\u200broles')]):
        engine=Envelope(authority);result=engine.commit(raw);engine.close()
        records.append({'id':f'malformed-{i}','input':raw,'oracle':'no effect',
                        'passed':result['state_mutated']==0,'result':result})
    verifier=ProvenanceVerifier();body='{"entity":"AAPL","value":"100B USD"}'
    digest=hashlib.sha256(body.encode()).hexdigest()
    signature=compute_evidence_signature('sec.gov','reports/v4',digest,'trusted_enterprise_signer')
    for name,content,signer in [('unknown_signer',body,'retired-key-unknown'),
                               ('changed_body',body+' ','trusted_enterprise_signer')]:
        result=verifier.verify_record('https://sec.gov/reports/v4',content,signer_id=signer,signature=signature)
        records.append({'id':name,'input':{'content':content,'signer':signer,'signature':signature},
                        'oracle':'is_trusted == false','passed':not result.is_trusted,'reason':result.rejection_reason})
    # Public benchmark signing material can be reused by anyone: preserve this
    # trust-assumption counterexample instead of claiming production authenticity.
    public_key_control=verifier.verify_record('https://sec.gov/reports/v4',body,
                         signer_id='trusted_enterprise_signer',signature=signature)
    write(TASK/'data/property_suite.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    counterexamples={'public_fixture_signing_key':{'attacker_computable_signature_accepted':public_key_control.is_trusted,
        'interpretation':'expected fixture limitation; not production authenticity or key-rotation validation'},
        'encoded_optional_summary':'See attack_trace.jsonl, outer_boundary_traces.jsonl and full_pipeline_replacement.jsonl',
        'failed_declared_properties':[r for r in records if not r['passed']]}
    write(TASK/'data/property_counterexamples.json',counterexamples)
    summary={'n':len(records),'passed':sum(r['passed'] for r in records),
             'failed':sum(not r['passed'] for r in records),'complete_requested_fuzz_scope':False,
             'unimplemented':protocol['not_implemented']}
    write(TASK/'data/property_summary.json',summary)
    write(TASK/'reports/COUNTEREXAMPLES.md','# Preserved counterexamples and property scope\n\n'+json.dumps(counterexamples,indent=2)+'\n\n'
          'The seeded finite corpus and result record every tested input. A passing finite suite is not a general proof. '
          'Signer revocation and generic declassification are not implemented; rejecting an unknown signer does not test key rotation. '
          'The encoded egress counterexample is reproduced by both the prototype and actual original HETE pipeline. '
          'The separate V4.1 guard narrows the accepted numeric contract.\n')
    print(json.dumps(summary))
    return int(bool(summary['failed']))


if __name__=='__main__':raise SystemExit(main())
