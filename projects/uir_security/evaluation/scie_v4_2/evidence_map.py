"""Case-level source/score/claim linkage for six core evidence populations."""
from .common import *


def main():
    protocols={p.name:sha(p) for p in (TASK/'manifests').glob('*PROTOCOL*.json')}
    records=[]
    populations=[
        ('external','experiments/agentdojo_external/attack_trace.jsonl','run_id','AGENTDOJO_V4_2_PROTOCOL_002.json','official goal/utility oracle;offline exposure/proposal scorer001','Table4;Figure2;expanded external results'),
        ('bilingual','experiments/multimodel_utility/bilingual_runs.jsonl','run_id','BILINGUAL_UTILITY_PROTOCOL.json','exactly one correct metric report SQLite commit','Table5;bilingual utility'),
        ('official_agent','experiments/official_baseline/OFFICIAL_AGENT_CASE_TRACE_003.jsonl','run_id','OFFICIAL_BASELINE_PROTOCOL_003.json','official oracle;separate official agent interface','official-agent integration paragraph;SupplementS4'),
        ('typed_mechanism','experiments/typed_semantics/DECISION_TRACE_EXAMPLES.jsonl','case_id','TYPED_EFFECT_PROTOCOL.json','actual forbidden SQLite effect;positive utility','typed effects results;SupplementS3'),
        ('bounded_model','experiments/typed_semantics/BOUNDED_MODEL_TRACE.jsonl','case_id','BOUNDED_MODEL_PROTOCOL.json','actual effect equals finite specification','bounded-state results;SupplementS3'),
        ('canonical','experiments/adaptive_redteam/ADAPTIVE_QUERY_LOG.jsonl','case_id','RED_TEAM_PROTOCOL.json','actual released encoded content;numeric/prose contract outcomes','encoded counterexamples and contract cost;SupplementS3')]
    for population,path,field,protocol,predicate,target in populations:
        file=TASK/path;filehash=sha(file)
        for r in rows(file):
            ids=[c['request_id'] for c in r.get('calls',[]) if 'request_id' in c]
            records.append({'population':population,'raw_case_id':r[field],
                'configuration':r.get('config',r.get('configuration',r.get('system','official CaMeL'))),
                'raw_file':path,'raw_file_sha256':filehash,'input_record_sha256':digest(r),
                'physical_request_ids':';'.join(ids),'protocol':protocol,'protocol_sha256':protocols[protocol],
                'score_version_and_predicate':predicate,'manuscript_target':target,
                'unknown_backend':r.get('backend_failure',False),
                'scope':'Saved new-run record;not reconstructed historical transport'})
    csvwrite(TASK/'data/NEW_RAW_TO_CLAIM_MAP.csv',records)
    write(TASK/'manifests/NEW_EVIDENCE_MAP.json',{'rows':len(records),'source_populations':len(populations),
        'path':'data/NEW_RAW_TO_CLAIM_MAP.csv','sha256':sha(TASK/'data/NEW_RAW_TO_CLAIM_MAP.csv'),
        'note':'Case/configuration IDs identify observations;request digests allow cache attribution. Canonical tests are fixed replacements,not independent adaptive searches.'})
    print('new claim-map rows',len(records))


if __name__=='__main__':main()
