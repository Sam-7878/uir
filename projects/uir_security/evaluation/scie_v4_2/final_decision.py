"""Work-order closure ledger, explicitly preserving unfulfilled publication gates."""
from .common import *
from .closure_reports import FREEZE_ID


def main():
    baseline=load(TASK/'manifests/BASELINE_LOCK.json');sha0=baseline['git_sha']
    specifications=[
      ('W01','PASS_SCOPED','baseline-lock001; independent recount001','BASELINE_LOCK.json; RAW_TO_CLAIM_MAP.csv; LEGACY_INTEGRITY_REPORT.md; ATTRITION_AND_AMENDMENT.md','19900 records;25 groups;418 nonbytecode verified','54 bytecode unresolved;8 missing interrupted original bodies','historical case IDs in RAW_TO_CLAIM_MAP.csv','Projection/byte scope explicitly separated from transport/fresh inference; no aggregate discrepancies'),
      ('W02','PASS_SCOPED','metric ontology V4.2; offline scorer001','METRIC_SPEC_V4_2.md; TRUSTED_EFFECT_SCHEMA.json; OUTCOME_TAXONOMY.csv; effect_oracles.py','8 effect/exposure tests;432 external outcome rows','Unknown6 logical outcomes from2 physical responses; no generic semantic DLP','outcome_ledger.csv; NEW_BACKEND_ATTRITION.csv','Original exposure detector preserved;3 flags corrected from actual captured model prompts'),
      ('W03','PASS_SCOPED','typed-effect001; bounded-model001','UIR_TYPED_SCHEMA_V4_2.json; typed_engine.py; TYPED_ENFORCEMENT_SEMANTICS.md; DECISION_TRACE_EXAMPLES.jsonl','22 security tests;6 configs x12 scenarios;192 bounded executions','Trusted host/issuer/key store; not protection against hostile Python/TCB compromise','typed_semantics traces;positive_write;positive_read','Actual compiled ApprovedAction/proof and current-state dispatch, not digest-only simulation'),
      ('W04','PASS_WITH_NEGATIVE_RESULT','external002; C3 v001/v002; timing001','MATCHED_SYSTEM_RESULTS.csv; TYPED_DELTA_NEGATIVE_RESULTS.md; POLICY_TIMING_SUMMARY.csv','432 paired environment episodes;72 initial C3;72 seen-ID diagnostic;200 timing pairs','42 C3 v001 transport faults;C3 v002 posthoc,not confirmatory','external run IDs; no_llm_runs.jsonl; no_llm_transport_diagnostic_v002.jsonl','C1=C2 security/utility;no incremental benefit. Legitimate writes succeed but restrictive duration policy loses one task'),
      ('W05','PASS_SCOPED','AgentDojo V4.2 protocol002','EXTERNAL_TASK_LEDGER.csv; attack_trace.jsonl; external_results.csv; EXTERNAL_REPORT.md','3 domains;12 tasks;60 task x attack pairings;2 generators;432 episodes;690 physical requests','Repeated templates/public contamination;nonexposure;2 incomplete physical responses','workspace3,6,7,8; banking3,4,8,13; travel0,1,3,5','Target coverage achieved;60 pairings are correlated, not independent attacks. Scored/planned/exposed denominators retained'),
      ('W06','LIMITED_OFFICIAL_SUBSET','official CaMeL local003; earlier001/002 retained','OFFICIAL_BASELINE_REPRO.md; FIDELITY_MATRIX_V4_2.csv; OFFICIAL_AGENT_CASE_TRACE_003.jsonl; OFFICIAL_LOCAL_CASE_COMPARISON.csv','6 actual official agent trials;3 task IDs;3 excluded development probes','Different interface/policy/retry budgets;no published baseline superiority','workspace/user_task_6;banking/user_task_3;travel/user_task_0 x benign/direct','Official implementation functional on subset,utility1/3;106 old interpreter tests not agent trials;no Progent official reproduction'),
      ('W07','LIMITED_CONTRACT_COST','red-team fixed001; V4.1 exact guard lock','NEGATIVE_LEAKAGE_REGRESSION.md; RED_TEAM_PROTOCOL.json; ADAPTIVE_QUERY_LOG.jsonl; CANONICAL_CONTRACT_AUDIT.csv','96 variants x3 pipelines;12 repeated numeric+12 prose controls per pipeline','No independent human red team/adaptive optimizer;strict prose utility0/12','v42-output-000 onward;old V4/V4.1 run IDs retained','Original72/96 releases;strict0/96 but12/12 safe prose denied. No zero-usability-loss claim'),
      ('W08','LIMITED_NEGATIVE_UTILITY','bilingual001; generator role locks','BACKBONE_ROLE_LOCK.csv; UTILITY_CONTRACT_FAILURES.csv; BILINGUAL_FAILURE_LEDGER.csv; MULTIMODEL_PARETO.md; LATENCY_TOKEN_LEDGER.csv','64 logical bilingual trials;8 IDs;4 semantic intents;2 generators','C3 blocks repeat deterministic cases;no new Phi unseen evaluation;small synthetic sample','bilingual-en/ko-0..3; external model/config IDs','Qwen0/8,Ministral1/8 per local config;C3 4/8. Repeated/no commits retained;no LLM-necessity claim'),
      ('W09','LIMITED_AI_ALTERNATIVE','historical blinded AI protocol; user-approved alternative','ANNOTATION_CODEBOOK_V4_2.md; RATER_BLINDED_IDS.csv; ADJUDICATION_LOG.md; JUDGE_VALIDATION_REPORT.md; IRB_STATUS.md','250 distinct blinded cases per AI rater;200 attack+50 benign','No humans recruited;no human validation/adjudication;no IRB determination invented','old blinded IDs preserved in RATER_BLINDED_IDS.csv','AI agreement86.0%/92.5%,kappa.367/.615;user explicitly authorized AI alternative. Original human requirement not marked PASS'),
      ('W10','LIMITED_EXPLORATORY','stats001 (late); independent legacy exact recount','STATS_PROTOCOL_V4_2.json; PAIRED_COMPARISON.csv; CLUSTER_SENSITIVITY.json; CI_AND_CLUSTER_SENSITIVITY.md','6 paired domain/backbone comparisons;2000 task-cluster bootstrap samples','Analysis family registered after first generator/during second;unknown pairs excluded only from completed stats','matched task_id/method/model IDs;historical coarse class-language proxy','No confirmatory superiority claim;degenerate bootstrap not unseen-risk bound;family IDs unavailable historically'),
      ('W11','PASS_SCOPED','TCB/resource contracts V4.2','THREAT_MODEL_SCOPE_V4_2.md; TCB_ASSUMPTIONS_V4_2.md; RESOURCE_BOUNDARY_AUDIT.md','actual pre/post effects and finite budget/race tests','No streaming hard cancellation,production key service,distributed transaction or universal wall-clock proof','typed mechanism traces;timing/external traces','Authority signing keys private per local session;unkeyed hashes are byte binding,not authenticity/WORM'),
      ('W12','HOLD_RIGHTS_AND_EXTERNAL_REPLICATION','release matrix001; portable recount001','DATA_CODE_RELEASE_PLAN.md; LICENSE_PROVENANCE.csv; SANITIZATION_AUDIT.md; PUBLIC_PRIVATE_RELEASE_MATRIX.md; THIRD_PARTY_REPRO_REPORT.md','stdlib projection recount and fresh-directory TeX checks','No human privacy sample audit;no institutional rights approval;no fresh OS/external human replication','SANITIZATION_MACHINE_SCAN.csv;PORTABLE_RECOUNT.json','Machine scan and local execution do not authorize public release or recover missing transport;no DOI fabricated'),
      ('W13','PASS_WITH_NARROWED_CLAIMS','manuscript V4.2 R1','NOVELTY_AND_CLAIMS_MATRIX.md; RELATED_WORK_DELTA_V4_2.md; SCOPE_FIT_PARAGRAPH.md; manuscript_body_v4_2.tex','technical Materials and Methods;prior mechanisms attributed','No typed security superiority;architecture/auditability contribution only','MANUSCRIPT_NUMERIC_SOURCES.json','Scope-fit and reviewer risk explicit;prior capability/isolation mechanisms not claimed invented'),
      ('W14','PASS_TECHNICAL_DRAFT','generic V2; journal V4.2 R1','MDPI_COMPLIANCE_REPORT.md; HETE_JOURNAL_V4_2_FINAL.pdf; CLEAN_BUILD_LOG.txt; figure PDF/600dpi PNG','177-word abstract;6 keywords;2 figures;numbered references','Draft declarations remain unresolved;not a submission-approved manuscript','PREFLIGHT_REPORT.json;visual review contact sheets','Fresh official template;source/figures/tables preserved;final build/visual evidence required'),
      ('W15','HOLD_AUTHOR_DECLARATIONS','author metadata user-directed a10; exact funding','AUTHOR_DECLARATION_FORM.md; publication_statements.tex; AI_USAGE_DISCLOSURE.md; DATA_AVAILABILITY_FINAL.md; RIGHTS_APPROVAL.md','2 authors;ORCIDs;corresponding Kim;user-supplied IITP funding verbatim','HETE-specific contributions/COI/sponsor role/APC,all-author version approval,rights/IRB unresolved','AUTHOR_METADATA.json source SHA;unsigned form','Prior-paper approval not HETE approval;Coummunications spelling retained as supplied,not silently corrected'),
      ('W16','HOLD_PREPRINT_RELEASE','generic article V2','HETE_PREPRINT_V2.zip; PREPRINT_READINESS_CHECKLIST.md; PREPRINT_TO_JOURNAL_CHANGELOG.md','generic PDF/source;no MDPI Definitions in preprint','No actual posting,DOI,license/all-author release receipt','generic package manifest','Separate from journal template;not posted/not peer-reviewed stated honestly'),
      ('W17','HOLD_APPROVAL_AND_CONFLICT_AUDIT','cover letter draft;SI LGK04C9ZT5','COVER_LETTER_ELECTRONICS_LGK04C9ZT5.md; REVIEWER_SUGGESTIONS_PRIVATE.csv; SUBMISSION_FIELDS_CHECKLIST.md','3 verified identity/contact candidate records','Recent3-year author conflicts unknown;mandatory author declarations unsigned;APC approval unknown','primary reviewer URLs recorded privately','No reviewer contact sent;no SuSy submission;required approval sentences remain conditional draft'),
      ('W18','HOLD_RELEASE_TECHNICAL_CHECKS_SEPARATE','preflight001; freeze R1','ELECTRONICS_SUBMISSION_READY.zip; HETE_JOURNAL_V4_2_FINAL.pdf; PREFLIGHT_REPORT.json; SUBMISSION_DECISION.json','nonzero PDF/CRC/source/fresh-directory checks;<=120MB','Final author approval and G4 unresolved;READY filename not permission','CLEAN_BUILD_LOG.txt;bundle SHA manifest','Invalid old407-byte template not used;earlier0-byte uploaded finding preserved;new compiled PDF packaged'),
      ('W19','PASS_BOUNDED_OPTIONAL','bounded-model001','BOUNDED_MODEL_PROTOCOL.json; BOUNDED_MODEL_TRACE.jsonl; MODEL_CHECK_REPORT.md','96 states;192 actual minimal/typed executions;0 mismatches','Finite reference model only,not universal proof','role/owner/approval/signer/revision/nonce state IDs','Enumerated state coverage is explicit;no arbitrary program/verifier theorem'),
      ('W20','OPTIONAL_NOT_COMPLETED','scope boundary V4.2','THREAT_MODEL_SCOPE_V4_2.md; RESOURCE_BOUNDARY_AUDIT.md','toy multi-tool/writes tested;production0','No formal independent red-team campaign or distributed/production assurance','existing finite traces only','Optional production/cloud expansion remains future work,not fabricated completion')]
    records=[]
    for w,status,protocol,files,count,exclusions,ids,notes in specifications:
        records.append({'work_item':w,'status':status,'baseline_SHA':sha0,'protocol_version':protocol,'produced_file_list':files,
            'count':count,'exclusions':exclusions,'raw_IDs':ids,'reviewer_notes':notes,'PASS_FAIL_HOLD_reason':notes,'freeze_id':FREEZE_ID})
    csvwrite(TASK/'reports/WORK_ORDER_W01_W20_STATUS.csv',records)
    write(TASK/'reports/WORK_ORDER_W01_W20_STATUS.md','# V4.2 work-order closure ledger\n\nFreeze: '+FREEZE_ID+
        '\n\nFull required columns (status, baseline SHA, protocol, file list, counts, exclusions, raw IDs, notes, reason) are in WORK_ORDER_W01_W20_STATUS.csv. '
        'PASS_SCOPED means the specified finite engineering evidence exists; it never means publication authorization.\n\n| Item | Status | Evidence / limitation |\n|---|---|---|\n'+
        '\n'.join(f"| {r['work_item']} | {r['status']} | {r['reviewer_notes']} |" for r in records)+'\n')
    decision={'freeze_id':FREEZE_ID,'decision':'HOLD','submitted':False,'preprint_posted':False,'public_release_performed':False,
        'G0':{'status':'PASS_SCOPED','reason':'Independent projection/count/hash lineage; original missing data and changed-byte scope explicitly preserved; final preflight must remain PASS'},
        'G1':{'status':'PERFORMED_NARROWED_CLAIMS','reason':'Actual typed/compiler/live effect path, equivalent minimal guard and authorized writes;no incremental observed security/utility. Scientific risk acceptance by authors unsigned'},
        'G2':{'status':'LIMITED_DISCLOSED','reason':'3 domains/12 tasks/60 correlated pairings/2 generators;AI alternative only;unknown backends and exploratory statistics;low utility/contract costs retained'},
        'G3':{'status':'HOLD','technical_format':'see PREFLIGHT_REPORT.json','reason':'HETE-specific final all-author contribution/COI/declaration/version approval,IRB wording and cover-letter assertions not confirmed'},
        'G4':{'status':'HOLD','reason':'No institutional rights/public license/reviewer-access route/no-simultaneous-submission receipt/final signed release decision;candidate conflicts and APC authorization unresolved'},
        'human_validation':False,'AI_alternative_authorized_by_user':True,'author_identity_and_funding_source_confirmed':True,
        'author_all_approval':False,'rights_approved':False,'reviewer_conflicts_cleared':False,
        'required_final_action':'Both authors/institution review exact PDF and bundle hashes, approve actual contributions/COI/sponsor/APC/rights/IRB/access, confirm no parallel journal submission and sign the risk/release form. Do not replace unknowns with invented approvals.'}
    write(TASK/'SUBMISSION_DECISION.json',decision)
    write(TASK/'submission_private/FINAL_GO_HOLD_SIGNOFF.md','# Final author decision — unsigned\n\nFreeze '+FREEZE_ID+
        '\n\nCurrent decision: HOLD. G0 scoped PASS; G1 performed with claims narrowed; G2 limited and disclosed; G3/G4 HOLD. '
        'Authors must review low utility, minimal=typed outcomes, safe-prose rejection, missing backend outcomes and late analysis registration, and choose conservative submission or further research. '
        'Approve only against the final PDF and ZIP SHA values in DELIVERY_MANIFEST.json; this file itself does not approve them.\n\n'
        'Author Seong-Su Park approval/receipt/date/hash: not supplied.\n\nAuthor Ki-Hyung Kim approval/receipt/date/hash: not supplied.\n\n'
        'Institutional release and rights receipt: not supplied.\n\nSponsor role/APC and no simultaneous journal review: not confirmed.\n')
    write(TASK/'reports/FINAL_EXECUTION_REPORT_KO.md',f'''# HETE Electronics V4.2 실행 보고서

Freeze ID: `{FREEZE_ID}`. 개발·실험·원고·로컬 패키지 준비는 수행했으며, **실제 투고·공개는 HOLD**입니다. 저자의 최종 승인과 자료 공개 권한을 추정하지 않았습니다. W01–W20의 상세 증빙·제외 사유·프로토콜·원시 ID는 WORK_ORDER_W01_W20_STATUS.csv에 있습니다.

## 실제 수행과 주요 결과

- Ubuntu26.04.1, 루트 `.venv_cuda` Python3.14.4, RTX3090의 작업 전용 Ollama를 사용했습니다. 기존 태스크 결과와 원고는 수정하지 않았습니다.
- 19,900건의 역사적 **점수 투영**을 별도 집계했고 수치·exact McNemar/Holm이 일치합니다. 원본736개 manifest 중67개 불일치 사실, 별도 overlay의418개 non-bytecode 검증, 미복원54개 bytecode와 누락된 중단 응답8건을 보존했습니다. 원래 transport나 추론을 복원했다고 주장하지 않습니다.
- 실제 typed compiler → proof-bound ApprovedAction → 현재 권한 재검증 → 실행기 경로를 구현했습니다. 동등한 최소 가드와 같은 정책·입력 기회를 사용했고, 보안·유용성에서 **추가 효과는 관측되지 않았습니다**.
- 공식 AgentDojo 환경: 3domain·12task·60 task×attack pairing·2generator·3구성,432개의 별도 환경 실행입니다. 동일 요청 응답을 공유하므로 독립 물리 추론432회라는 뜻이 아닙니다. 고유 물리 요청690건과 논리 요청 비용을 구분했습니다.
- Qwen3-4B: 최소/typed 모두 정상4/12, 공격0/60. Ministral14B: 모두 정상7/12, 평가 완료 공격0/58, 계획60 중2건은 미완료 backend 응답으로 **unknown**입니다. 이2건을 차단 성공으로 세지 않았습니다. 정책 때문에 정상 reschedule 한 건을 잃은 사실도 보존했습니다.
- 실제 공식 CaMeL 코드·정책을 로컬 모델에 연결해6회를 실행했습니다. 정상1/3, 공격 목표0/3이며 서로 다른 인터페이스·정책·재시도 예산 때문에 HETE 우월성의 증거로 쓰지 않습니다. 제외된 개발 실패와 API 역할 변환 전후 본문을 보존했습니다.
- 96종 출력 교체 공격에서 원래 actual pipeline은72건을 방출했습니다. 동일 V4.1 guard 설치와 새 typed canonical 경계는0/96이지만, 안전한 정상 설명문도12/12 차단했습니다. 숫자 계약에서의 효과를 일반 자연어 기밀성이나 비용 없는 개선으로 확대하지 않았습니다.
- 한·영4의미 의도×2언어8ID 실험에서 구성별 Qwen0/8, Ministral1/8입니다. 고정 resolver는4/8이며 부정문에서 실패했습니다. 중복된 정상 쓰기도 완전 성공으로 세지 않았습니다. LLM의 필수성·다국어 우월성을 주장할 수 없습니다.
- 보안 회귀 테스트170개 통과. 유한 상태96개×2구성192회에서는 reference specification 불일치0건입니다. 무한 상태 형식 증명이 아닙니다.

## 원고와 패키지

저널용 HETE_JOURNAL_V4_2_FINAL.pdf와 ELECTRONICS_SUBMISSION_READY.zip, generic article 형식 HETE_PREPRINT_V2.zip을 별도로 준비합니다. 초록177단어·키워드6개, 실제 타입/승인 규칙/TCB/공정 대조군/비노출·unknown/실패·통계 한계·자료 계보를 Methods와 Results에 반영했습니다. 그림은 vectorPDF와600dpiPNG 및 생성 소스를 보존합니다. ZIP의 READY/FINAL 이름은 투고 승인 표시가 아닙니다.

저자·교신저자·소속·ORCID는 지정한 DLG a10 원고를 참조했고 IITP 사사는 사용자 제공 문구를 그대로 반영했습니다. 다른 논문의 저자 승인 문장을 HETE 승인으로 전용하지 않았습니다. 공유 코어 소스는 복제하지 않았고 모든 새 태스크 출력은 이 results 폴더에 모았습니다.

## 보류 사유와 검토 자료

G0는 명시된 범위의 무결성 검증입니다. G1은 동등한 결과에 맞춰 architecture/auditability 중심으로 주장을 축소했습니다. G2는 AI-AI agreement만 있으며 인간 검증이 아닙니다. 분석 family 등록이 첫 backbone 이후이므로 새 통계는 exploratory로 표시했습니다. 독립 인간 심사·fresh OS 재현·공개 권리 검토가 완료된 것으로 표시하지 않았습니다.

G3/G4: 이 원고의 실제 저자 기여·COI·후원기관 역할·APC·IRB 적용 문구, 자료/코드 공개와 심사자 접근 경로, 중복 저널 투고 여부 및 최종 전원 승인이 필요합니다. 심사자 후보3인의 신원·공개 연락처는 확인했으나 최근3년 이해관계 확인은 미완료입니다. 필수 커버레터 승인 두 문장은 미서명 초안에만 남겼습니다. DOI·접수증·게시 사실을 만들지 않았습니다.

검토 시작점: SUBMISSION_DECISION.json, submission_private/AUTHOR_DECLARATION_FORM.md, FINAL_GO_HOLD_SIGNOFF.md, PREFLIGHT_REPORT.json, DELIVERY_MANIFEST.json. 저자의 구체적 버전 승인 전까지 투고/게시하지 않습니다.
''')
    print('W01-W20 ledger20; release decision HOLD')


if __name__=='__main__':main()
