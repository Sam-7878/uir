"""Review, source map and M01-M10 status without invented signatures."""
from .common import *
import re
import subprocess

def main():
    summary=load(TASK/'data/statistics/SUMMARY.json');pages={}
    for folder,name in [('journal','HETE_JOURNAL_V4_3.pdf'),('preprint','HETE_PREPRINT_V3.pdf')]:
        info=subprocess.check_output(['pdfinfo',str(TASK/'paper'/folder/name)],text=True);pages[folder]=int(re.search(r'Pages:\s+(\d+)',info).group(1))
    objections=[
        ('Typed novelty','Registered704 composition/96 audit rows remain C1=C2;primary paired p1','No superiority;architecture/negative-results scope;conditional argument only','HIGH:equivalent capability checks are prior mechanisms'),
        ('Weak flat baseline','Same proof,current state,evidence,executor and common audit schema','Shared implementation controls policy confounding','Cannot measure independent developer error rates or productivity'),
        ('Prose utility cost','Bounded public rendering48/48;general benign prose0/16','Report full64 benign population and restricted template scope','Not unrestricted generated explanations or general DLP'),
        ('Pseudo independent sample size','256 enumerated states,six explanation templates,eight attack programs','ID counts and program/family counts separately reported','Author-generated policy-aware corpus;no blind external red team'),
        ('Audit authenticity','Runtime HMAC plus trusted in-process terminal anchor','Common-field completeness and tamper detection only','No WORM,external witness,nonrepudiation or host-compromise protection'),
        ('Effect oracle breadth','Actual attachedSQLite row counts under fixed two-step request','Count projection/stateful transaction scope explicit','Not independent correctness of arbitrary executor values or crash durability'),
        ('Posthoc metric change','Original release-only flag preserved;new secondary completeness audit explicit','No final execution rerun;registered H1/H2 unchanged','Secondary utility result is not confirmatory preregistration'),
        ('Missing handoff archives','Three originalZIP hashes match;three originals deleted by user','Folder snapshot locked separately;M01 PARTIAL','Cannot claim6/6 original upload identity'),
        ('Historical source drift','Two post-freeze scripts changed;one report relocated exactbytes','Current snapshot compared to sealed sourceZIP;oldpreflight skip not used','Older full delivery verification does not pass unchanged today'),
        ('External agent ranking','Only prior six official CaMeL trials;different budgets/interface','Smoke integration and architecture only','No official competitor superiority'),
        ('Human and OS independence','No new human raters;fresh execution sameUbuntu/rootvenv','AI-only historical labels;local self-review identified','SecondOS and external human English/visual review NOT RUN'),
        ('Publication approval','No exact-version author signatures/rights/APC/IRB receipt','Scientific evidence validity distinct from authorization','Preprint/journal release HOLD')]
    csvwrite(TASK/'reports/REVIEWER_OBJECTION_RESPONSE_MATRIX.csv',[{'objection':a,'evidence':b,'response':c,'remaining_risk':d} for a,b,c,d in objections])
    review=f'''# V4.3 SCIE-oriented self-review — not an independent human review

Journal draft{pages['journal']}pages;generic preprint{pages['preprint']}pages,including extended methods,conditional transition reasoning,complete program catalogs,actual trace projections and reproduction/ethics limitations. Abstract186 words;6 keywords. No arbitrary page target or acceptance guarantee is used. Electronics official Aims & Scope states no maximum paper length and requires experimental/method detail:https://www.mdpi.com/journal/Electronics/about . Direct author/SI pages returned429 during this run;do not claim fresh verification of every submission detail. Preprints.org sourceZIP requirements were directly read:https://www.preprints.org/help-center/submission-guidelines . Actual submission must recheck current official rules.

Most important finding:incremental typed security/audit detection remains unobserved. A further704 composition and96 audit rows didnot create a type-specific advantage. The paper now says this before historical result tables. The conditional equivalence argument is not claimed as a new universal security proof. The bounded renderer's feature gain is common to flat/typed and still denies all16 safe arbitrary-prose cases. Forty-eight supported IDs repeat six templates;there isno new multilingual or neural-necessity evidence.

This review is by the implementing agent. Independent human language/visual review was not performed,and no reviewer's acceptance decision is predicted. All-author/institutional release and scientific-risk decisions remain unsigned. See REVIEWER_OBJECTION_RESPONSE_MATRIX.csv and the paper's detailed limitations;the lack of demonstrated novelty remains a material Major Revision/Reject risk.
'''
    write(TASK/'reports/SCIE_REVIEW_V4_3.md',review);write(DOC/'SCIE_REVIEW_V4_3.md',review)
    claims=[
        ('V4.3 matched null','0/327 forbidden each;24/24 explicit controls;48/48 audit detections','tab:v43composition','experiments/composition/runs.jsonl; audit_tamper_runs.jsonl','Finite matched effects;not proof of general equality'),
        ('V4.3 output feature','48/48 supported;0/16 arbitrary benign;0/64 controlled leaks','sec:v43output;fig:v43output','experiments/output_channel/runs.jsonl;OUTPUT_TRADEOFF_RESULTS.csv','Common contract change;secondary utility audit posthoc'),
        ('V4.3 local overhead','200 positive pairs;p50/p95/p99 from saved ledger','V4.3 runtime subsection','experiments/composition/TIMING_RAW.csv','No generator throughput or human-effort claim'),
        ('V4.2 external results','432 logical;690 physical;Qwen4/12,0/60;Min7/12,0/58+2unknown','tab:external','V4.2 frozen raw and compact results','Historical separate population;no pooling'),
        ('V4.2 output tradeoff','Original72/96 leaks;strict0/96;legitimate prose12/12 denied','Encoded counterexamples subsection','V4.2 canonical audit','Historical96 are development fornewstudy,not reusedfinal'),
        ('V4.2 bilingual','Qwen0/8;Min1/8;literal4/8','tab:bilingual','V4.2 bilingual raw','No new semantic inference/M05 claim'),
        ('Legacy projection','19900 records,25 groups','Restoration appendix','REPRODUCTION_RECEIPTS.json;RESTORED_PROJECTION_RECOUNT.json','Not missing original transport or fresh inference'),
        ('Original handoff identity','3ZIPs MATCH;3 user-confirmed deleted originals','Restoration appendix','HANDOFF_MANIFEST.json;HANDOFF_RESOLUTION.json','Unpacked folder isnot original ZIP byte identity'),
        ('Publication status','Unposted and unsubmitted;author/rights decisions pending','Publication Statements;release appendix','FINAL_GO_HOLD_DECISION.json','Research permission isnot final manuscript approval')]
    csvwrite(TASK/'reports/PAPER_CLAIM_AUDIT.csv',[{'claim':a,'reported_quantity':b,'manuscript_label':c,'raw_evidence':d,'scope':e} for a,b,c,d,e in claims])
    status=[
        ('M01','PARTIAL_ARCHIVE_IDENTITY','3 originalZIP hashes match;3 deleted/unverifiable;extracted30tests and19900/25 recount executed','HANDOFF_MANIFEST.json;HANDOFF_RESOLUTION.json;RESTORE_SMOKE_TEST.md'),
        ('M02','HOLD_ACTUAL_AUTHOR_RIGHTS','Identity/funding user-directed;exact-version contributions,COI,APC,IRB,rights and signatures not supplied','submission_private/*.md;FINAL_GO_HOLD_DECISION.json'),
        ('M03','TRACKB_AFTER_REGISTERED_NULL','Owner-approved one-run TrackA;704 composition+96 audit rows,no increment;fallback authorized','SCIENTIFIC_POSITIONING_DECISION.md;PRIMARY_PAIRED_TESTS.csv'),
        ('M04','SCOPED_OUTPUT_CONTRACT','512 output executions;48 supported/16 unsupported benign IDs;64 attack IDs;no typed-only gain;secondary posthoc completeness audit','OUTPUT_CHANNEL_CONTRACT_V4_3.md;OUTPUT_TRADEOFF_RESULTS.csv;EXFIL_FAMILY_SPLIT.json'),
        ('M05','NOT_RUN_CONDITIONAL_TRACKB','No new semantic benchmark or model requests;old8cases not relabeled as generalization','SEMANTIC_BENCHMARK_PREREG_V4_3.md;SEMANTIC_TASK_MANIFEST.json'),
        ('M06','LIMITED_NO_NEW_RANKING','PriorAgentDojo/CaMeL limitations retained;no new official superiority or Progent reproduction','AGENTDOJO_V4_3_PROTOCOL.json;OFFICIAL_BASELINE_FAIRNESS_MATRIX.csv;EXTERNAL_NEGATIVE_RESULT_REPORT.md'),
        ('M07','SCOPED_LOCAL_REPRODUCTION','OriginalZIP30tests and actualprojection recounted;newstudy sourceZIP/freshTeX receipts separate;no crossOS/human independence','REPRODUCTION_RECEIPTS.json;FRESH_DELIVERY_VERIFICATION.json;INDEPENDENT_AUDIT.md'),
        ('M08','AI_ONLY_RESTRICTED','Humanfalse;historicalAIagreementnot accuracy;controlled finite canary/effect oracles','AI_ONLY_LIMITATION.md;JUDGE_ERROR_ANALYSIS.csv;ETHICS_DECISION_RECORD.md'),
        ('M09','EXPANDED_LOCAL_REVIEW_EXTERNAL_PENDING',f'Journal{pages["journal"]}pages/preprint{pages["preprint"]};full methods/catalogs/traces;external human English/visual review NOTRUN','paper/journal;paper/preprint;SCIE_REVIEW_V4_3.md;PAPER_CLAIM_AUDIT.csv'),
        ('M10','SUBMISSION_AND_PREPRINT_HOLD','Preprint-first plan documented;no signatures/rights/DOI/receipts fabricated','FINAL_GO_HOLD_DECISION.json;SUBMISSION_DECISION_V4_3.json')]
    csvwrite(TASK/'reports/M01_M10_STATUS.csv',[{'item':a,'status':b,'count_and_reason':c,'produced_files':d,'freeze':FREEZE} for a,b,c,d in status])
    write(TASK/'SUBMISSION_DECISION_V4_3.json',load(TASK/'manifests/FINAL_GO_HOLD_DECISION.json'))
    # Source map includes generating code and actual shared manuscript inputs.
    sourcefiles=list(Path(__file__).parent.glob('*.py'))+list((TASK/'source').glob('*.tex'))+[ROOT/'tests/uir_security/test_scie_v4_3_boundary.py']
    for folder in ('journal','preprint'):sourcefiles += list((TASK/'paper'/folder).glob('*.tex'))+list((TASK/'paper'/folder).glob('*.bib'))
    write(TASK/'manifests/FINAL_SOURCE_MANIFEST.json',{'freeze':FREEZE,'files':{str(p.relative_to(ROOT)):sha(p) for p in sorted(sourcefiles)},
        'figures':{str(p.relative_to(TASK)):sha(p) for p in (TASK/'figures').glob('*') if p.is_file()},'claim_map_sha256':sha(TASK/'reports/CLAIM_TO_EVIDENCE_V4_3.csv'),
        'registration_sources_unchanged':True,'public_release_authorized':False})
    write(TASK/'submission_private/COVER_LETTER_DRAFT.md',f'''# Conditional cover letter — do not submit before approval

Dear Editors,

We prepare the manuscript “HETE: Typed Authority and Auditable Enforcement for Tool-Using Language-Model Agents” for Electronics,Special Issue LGK04C9ZT5. It implements an application-controlled authority boundary and reports matched flat/typed comparisons,actual state changes,an explicit negative result and bounded narrative-contract costs. A newly registered finite comparison again findsno incremental typed security or audit-detection benefit. The contribution is scoped architecture and reproducible negative evidence,not superiority over existing capability guards.

Preprint-first release is planned but hasnot occurred;no DOI or server receipt exists. If authors approve posting,insert the real receipt/version and update this letter before journal submission. Institutional release rights,reviewer conflicts and final author declarations remain unresolved.

Required text below is UNSIGNED/UNCONFIRMED,not an assertion of approval:

> We confirm that neither the manuscript nor any parts of its content are currently under consideration for publication with or published in another journal.
> All authors have approved the manuscript and agree with its submission to Electronics.

Corresponding author from the user-directed source:Ki-Hyung Kim. Final signing date,manuscript/bundle SHA and authorization receipts:NOT PROVIDED. Freeze{FREEZE}.
''')
    tech=load(TASK/'PREFLIGHT_REPORT.json') if (TASK/'PREFLIGHT_REPORT.json').is_file() else None
    technical=f"{tech['technical_checks_passed']}/{tech['technical_checks_total']} PASS" if tech and tech.get('scientific_evidence_valid') else '최종 패키지 검증 전 또는 실패 상태;PREFLIGHT_REPORT.json 확인'
    report=f'''# HETE V4.3 실행 결과

Freeze`{FREEZE}`. **Track A 한 차례 검증 후 Track B로 전환했습니다. 실제 preprint 게시·저널 투고·공개는 HOLD입니다.**

## 신규 과학 결과

- Ubuntu 26.04.1과 루트 `.venv_cuda` Python 3.14.4를 사용했습니다. 새 모델 추론은 0회입니다.
- 사전 등록한 다중 서비스 비교는 352개 paired ID × 2구성 = 704회입니다. 두 시스템 모두 327개 부정 사례에서 금지 효과 0건, 352개 전체에서 명세 불일치 0건입니다. 명시적 정상·재생 컨트롤 24/24 완료와, 모든 권한 조건이 참인 상태에서의 별도 정상 효과를 구분했습니다.
- 같은 필드와 terminal anchor를 사용하는 감사 변조 시험은 48 ID × 2 = 96회이며, 양쪽 모두 48/48을 검출했습니다. Primary H1/H2의 McNemar/Holm 값은 모두 p=1입니다. Typed UIR의 추가 보안·감사 검출 효과는 관측되지 않았습니다. 개발 생산성이나 사람의 원인 추적 시간은 측정하지 않았습니다.
- 분리된 출력 계약 시험은 128 ID × 4정책 = 512회입니다. 공통 공개 사실 렌더러는 지원 설명 48/48을 완료하지만 자유형 정상 설명 16/16은 여전히 거부합니다. 실제 outbox에서 두 가드 모두 통제된 공격 누출 0/64이며, 의도적인 unsafe 진단에서는 48/64가 누출됩니다. 기능 개선은 타입 고유 효과가 아니라 공통 계약 변경의 효과입니다.
- 방출 여부만으로 설명 완료를 세던 원시 flag의 한계를 후속 감사에서 확인했습니다. 원본은 보존했고, 실제 값·인용을 요구하는 secondary 완료 지표를 사후 분석으로 분리했습니다. Final 실행은 재시험하지 않았습니다.
- 기존 AgentDojo 논리 실행 432회·물리 요청 690회, unknown, encoded 누출 72/96·정상 설명 12/12 거부, 낮은 한·영 성공률과 AI-only 한계를 별도 역사적 결과로 유지했습니다. M05/M06의 신규 모델·경쟁자 확장은 Track B 중단 규칙에 따라 하지 않았습니다.

## 재현성과 보존

원래 코드 ZIP을 추출한 테스트 30개와 실제 19,900행·25그룹의 점수 투영 recount를 다시 실행했습니다. 루트 보안 회귀 테스트 181개가 통과했습니다. 새 ZIP의 소스 테스트·전체 유한 실험 재산출·두 TeX 빌드는 FRESH_DELIVERY_VERIFICATION.json의 실제 receipt로 구분합니다. 현재 기술 검증: {technical}.

입력 6개 중 3개 ZIP은 manifest의 크기·SHA와 일치합니다. 나머지 3개는 사용자가 원본 삭제를 확인했으므로 원본 ZIP의 바이트 동일성을 미검증으로 남겼습니다. 풀린 폴더의 현재 입력은 별도로 동결했습니다. V4.2 이후 수정된 스크립트 2개와 이동 보고서 1개의 차이도 기록했고 되돌리지 않았습니다. M01은 원본 archive 차원에서 PARTIAL입니다. 이전 자료나 실패 이력은 수정하지 않았습니다.

## 논문·출판 판정

저널 원고 {pages['journal']}쪽, generic 프리프린트 {pages['preprint']}쪽으로 확장했습니다. 초록은 186단어·키워드는 6개입니다. 동등 정책 가정, 조건부 전이 논증, 전체 프로그램 목록, 실제 trace 예시, 오버헤드, 계보, 부분 인계, 사후 oracle 감사, 통계 및 공개 한계를 본문과 부록에 기술했습니다. 분량 자체의 목표보다 필요한 방법과 근거를 우선했고, 근거 없는 새 효과는 추가하지 않았습니다.

HETE_JOURNAL_V4_3.pdf / ELECTRONICS_V4_3_REVIEW_SOURCE.zip과 HETE_PREPRINT_V3.pdf/zip은 별도 산출물입니다. 내부 V3는 preprints.org에 세 버전이 게시되었다는 뜻이 아닙니다. 승인 후 preprints.org에 먼저 게시하고 실제 DOI·receipt를 받은 뒤 Electronics 특집호에 투고하는 순서를 준비했습니다.

M02/G3/G4: 최종 저자 기여·COI·후원기관 역할·APC·IRB 적용·공개 권리·접근 경로·심사자 충돌·정확한 원고 버전의 전원 승인은 미확정입니다. 저자 정보와 사사는 앞서 지정한 출처와 문구를 사용했습니다. 외부 인간 영문·시각 검수와 두 번째 OS 재현은 NOT RUN입니다. 연구 진행 및 Track B 전환 승인을 최종 출판 승인으로 전용하지 않았습니다. 과학적 차별성의 심사 위험은 여전히 남아 있습니다.

상세 검토 시작점: M01_M10_STATUS.csv, SCIENTIFIC_POSITIONING_DECISION.md, SCIE_REVIEW_V4_3.md, REVIEWER_OBJECTION_RESPONSE_MATRIX.csv, PREFLIGHT_REPORT.json, SUBMISSION_DECISION_V4_3.json.
'''
    write(TASK/'reports/FINAL_EXECUTION_REPORT_KO.md',report)
    write(DOC/'HETE_V4_3_EXECUTION_REPORT_2026-10-23.md',report)
    print('review and M01-M10 reports;pages',pages,'technical',technical)

if __name__=='__main__':main()
