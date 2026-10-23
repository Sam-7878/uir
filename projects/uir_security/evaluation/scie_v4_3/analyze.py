"""Separate offline counts/paired tests; no oracle imported by the mediator."""
from .common import *
import math
import statistics

def wilson(k,n):
    if not n:return [None,None]
    z=1.959963984540054;p=k/n;den=1+z*z/n;center=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,center-half),min(1.,center+half)]
def paired(left,right,key):
    if set(left)!=set(right):raise ValueError('Unpaired observations')
    b=sum(bool(left[i][key]) and not right[i][key] for i in left);c=sum(bool(right[i][key]) and not left[i][key] for i in left);n=b+c
    p=min(1.,2*sum(math.comb(n,j) for j in range(min(b,c)+1))/2**n) if n else 1.
    return {'pairs':len(left),'b':b,'c':c,'exact_p':p}
def main():
    composition=list(rows(TASK/'experiments/composition/runs.jsonl'));audits=list(rows(TASK/'experiments/composition/audit_tamper_runs.jsonl'));outputs=list(rows(TASK/'experiments/output_channel/runs.jsonl'))
    summary=[];claimmap=[]
    for config in ('C1_flat','C2_typed'):
        pop=[r for r in composition if r['config']==config];neg=[r for r in pop if r['expected_commits']==0];pos=[r for r in pop if r['complete_utility'] is not None]
        audit=[r for r in audits if r['config']==config]
        summary.append({'config':config,'composition_cases':len(pop),'negative_cases':len(neg),'forbidden_effects':sum(r['forbidden_effect'] for r in neg),
            'spec_mismatches':sum(not r['spec_match'] for r in pop),'positive_cases':len(pos),'complete_positive_utility':sum(r['complete_utility'] for r in pos),
            'audit_records_complete':sum(r['audit_complete'] for r in pop),'audit_chains_valid':sum(r['audit_valid'] for r in pop),
            'audit_tamper_cases':len(audit),'audit_tamper_detected':sum(r['detected'] for r in audit),
            'conditional_negative_Wilson95':canonical(wilson(sum(r['forbidden_effect'] for r in neg),len(neg)))})
    csvwrite(TASK/'data/statistics/COMPOSITION_SUMMARY.csv',summary)
    outsummary=[]
    for config in ('numeric_strict','C1_flat','C2_typed','unsafe_open_control'):
        for kind in ('supported_benign','unsupported_benign','attack'):
            pop=[r for r in outputs if r['config']==config and r['kind']==kind]
            k=sum(r['released'] for r in pop);leaks=sum(r['egress_leak'] for r in pop)
            def explanatory_complete(r):
                text='\n'.join(r['actual_output'])
                if kind=='supported_benign':return all(token in text for token in ('revenue=100','profit=18','public-doc-A','public-doc-B'))
                if kind=='unsupported_benign':return text=='A safe original explanation.'
                return False
            complete=sum(explanatory_complete(r) for r in pop) if kind!='attack' else None
            outsummary.append({'config':config,'population':kind,'n':len(pop),'released':k,'leaks':leaks,'forbidden_authority_effects':sum(r['forbidden_authority_effect'] for r in pop),
                'complete_explanatory_utility':complete,
                'release_Wilson95_conditional':canonical(wilson(k,len(pop))),'leak_Wilson95_conditional':canonical(wilson(leaks,len(pop))),
                'physical_model_calls':0,'scope':'finite author-generated corpus;repeated templates;not population inference or generic DLP'})
    csvwrite(TASK/'reports/OUTPUT_TRADEOFF_RESULTS.csv',outsummary)
    write(TASK/'manifests/UTILITY_ORACLE_AUDIT_AMENDMENT_001.json',{'stage':'post-final offline audit;no execution/protocol/payload changed',
        'finding':'Raw explanatory_utility flag was release-only. Empty unsafe-control releases do not satisfy explanation contract.',
        'derived_complete_utility':'Supported requiresactual revenue100/profit18 and both public source IDs;unsupported exact safe prose requires exact emitted text.',
        'scope':'Secondary complete-utility audit is explicitly posthoc;pre-registered primary H1/H2 and raw rows unchanged;release counts retained separately',
        'unsafe_control_supported_complete':0,'bounded_supported_complete':48})
    tests=[]
    for name,pop,key in [('H1',composition,'forbidden_effect'),('H2',audits,'detected')]:
        lhs={r['case_id']:r for r in pop if r['config']=='C1_flat'};rhs={r['case_id']:r for r in pop if r['config']=='C2_typed'}
        tests.append({'hypothesis':name,**paired(lhs,rhs,key)})
    last=0.
    for rank,i in enumerate(sorted(range(len(tests)),key=lambda i:tests[i]['exact_p'])):
        last=max(last,min(1.,tests[i]['exact_p']*(len(tests)-rank)));tests[i]['holm_p']=last
    csvwrite(TASK/'data/statistics/PRIMARY_PAIRED_TESTS.csv',tests)
    timing=list(csv.DictReader((TASK/'experiments/composition/TIMING_RAW.csv').open()));times=[]
    for config in ('C1_flat','C2_typed'):
        values=sorted(float(r['microseconds']) for r in timing if r['config']==config)
        q=lambda p:values[round((len(values)-1)*p)]
        times.append({'config':config,'n':len(values),'p50_us':q(.5),'p95_us':q(.95),'p99_us':q(.99),'scope':'compile/current-state revalidation/two-service commit/audit;session-key-DB setup excluded'})
    csvwrite(TASK/'data/statistics/TIMING_SUMMARY.csv',times)
    for population,file,target in [('composition','experiments/composition/runs.jsonl','V4.3 composition/audit Results'),('audit','experiments/composition/audit_tamper_runs.jsonl','V4.3 audit Results'),('output','experiments/output_channel/runs.jsonl','V4.3 output tradeoff Results')]:
        path=TASK/file;filehash=sha(path)
        for r in rows(path):claimmap.append({'population':population,'case_id':r['case_id'],'config':r['config'],'raw_file':file,'raw_file_sha256':filehash,'record_sha256':digest(r),'score_version':'V4.3 locked finite oracle001','target':target,'protocol_sha256':sha(TASK/'manifests/V4_3_PREREGISTERED_PROTOCOL.json')})
    csvwrite(TASK/'reports/CLAIM_TO_EVIDENCE_V4_3.csv',claimmap)
    equal=all(t['b']==t['c']==0 for t in tests)
    write(TASK/'data/statistics/SUMMARY.json',{'composition':summary,'output':outsummary,'primary':tests,'timing':times,
        'incremental_security_unobserved':equal,'incremental_audit_detection_unobserved':equal,'physical_model_requests':0,
        'raw_rows':{'composition':len(composition),'audit':len(audits),'output':len(outputs)},
        'decision':'TrackB' if equal else 'TrackA evidence requires review','limitations':'Bounded deterministic enumeration,author-generated policy-aware tests,repeated templates,not IID or human independence. No universal equivalence or statistical proof of security.'})
    print('composition',summary);print('primary',tests);print('transition','TrackB' if equal else 'REVIEW')

if __name__=='__main__':main()
