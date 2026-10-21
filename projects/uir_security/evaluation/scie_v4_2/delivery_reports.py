"""Evidence-linked result narratives, model roles, release and submission drafts."""
from .common import *
from .analysis import wilson

import csv
from collections import Counter,defaultdict


def main():
    summary=load(TASK/'data/statistics/EXTERNAL_SUMMARY.json');aggregate=defaultdict(lambda:defaultdict(int))
    for row in summary:
        key=(row['model'],row['config'])
        for name in ('benign_n','benign_utility','benign_write_tasks','benign_complete_with_write','attack_planned_n',
              'attack_scored_n','official_attack_success','injected_content_observed_n','unknown_security_outcomes','raw_goal_proposal_n'):
            aggregate[key][name]+=row[name]
    compact=[{'model':m,'config':c,**dict(v)} for (m,c),v in sorted(aggregate.items())]
    csvwrite(TASK/'data/EXTERNAL_COMPACT.csv',compact);write(TASK/'data/EXTERNAL_COMPACT.json',compact)
    ledger=list(csv.DictReader((TASK/'data/outcome_ledger.csv').open()))
    failures=[{'run_id':r['run_id'],'domain':r['domain'],'model':r['model'],'config':r['config'],
        'backend_failure':r['backend_failure'],'parse_failure':r['parse_failures'],'denied_proposals':r['denied_proposals'],
        'utility':r['utility'],'cause_scope':'observed backend/contract/denial indicators; remaining semantic cause not inferred'}
        for r in ledger if r['utility']=='False']
    csvwrite(TASK/'experiments/multimodel_utility/UTILITY_CONTRACT_FAILURES.csv',failures)
    csvwrite(TASK/'experiments/multimodel_utility/LATENCY_TOKEN_LEDGER.csv',ledger)
    registry=[]
    for filename,role,root in [('generator_0.json','V4.2 external/bilingual generator',TASK),
                              ('generator_1.json','V4.2 external/bilingual and official-agent generator',TASK),
                              ('ai_rater_R1_model.json','historical AI rater R1, not a human',OLD),
                              ('ai_rater_R2_model.json','historical AI rater R2, not AgentDojo generator',OLD)]:
        info=load(root/'manifests'/filename)
        registry.append({'role':role,'model_id':info['name'],'digest':info['digest'],
                         'quantization':info.get('details',{}).get('quantization_level','not recorded'),
                         'source':str((root/'manifests'/filename).relative_to(ROOT))})
    csvwrite(TASK/'data/BACKBONE_ROLE_LOCK.csv',registry);write(TASK/'manifests/MODEL_REGISTRY.json',registry)
    plan=load(TASK/'manifests/AGENTDOJO_V4_2_PROTOCOL_002.json')
    taskledger=[{'domain':t['domain'],'task_id':t['task_id'],'write_task':t['write_required_by_user_scope'],
        'task_prompt_hash':t['prompt_sha256'],'attack_method':method,'attack_payload_hash':digest(payload),
        'official_attack_implementation':method!='custom_append','goal_unchanged':True}
        for t in plan['tasks'] for method,payload in t['payloads'].items()]
    csvwrite(TASK/'experiments/agentdojo_external/EXTERNAL_TASK_LEDGER.csv',taskledger)
    write(TASK/'reports/EXTERNAL_REPORT.md','# Expanded official-environment study\n\n'
        '432 planned unique logical runs completed/failed in place: two generator backbones, three local systems, twelve distinct tasks across three domains, '
        'benign plus five attacks. Sixty task-attack pairings use four upstream fixed attacks and one custom append; repeated templates and tasks are correlated. '
        'Nine task requests delegate writes; successful writes are counted from actual official environment state. The agent receives no task ground_truth, expected answer or security-oracle result. '
        'Official fixed attacker vector discovery uses upstream ground-truth canary preparation outside the agent.\n\n'
        'Exact-request common-response caching is a controlled pairing design: separate policy/environment execution does not imply a fresh model call. '
        'Original logged exposure flags and the corrected actual-generator-input detector are both retained. '
        'Incomplete model responses have unknown security outcomes, including cache propagation from two physical bodies. They are never counted as blocked attacks.\n\n'
        +canonical(compact)+'\n\nThe typed system observes no security/utility gain over the equivalent minimal policy. '
        'Ministral loses one benign reschedule relative to vanilla because the delegated argument policy forbids an explicit duration change. '
        'Do not repair this held-out outcome in place.\n')
    write(TASK/'reports/TYPED_DELTA_NEGATIVE_RESULTS.md','# Matched negative result\n\n'
        'C1 and C2 implement the same application policy; C2 adds actual typed compilation and proof-bound dispatch. '
        'The matched recorded security and utility outcomes are equal. The architecture offers an explicit intermediate obligation/trace and detects malformed or tampered approved objects in controlled tests, '
        'but no empirical incremental security/utility superiority over the flat guard is established. The local admission/commit timing reports overhead, not acceleration.\n\n'
        'C3 v001 has 42 transport faults among72 trials and one benign success. C3 v002 resolves six benign tasks after a serialization fix, without oracle/rule changes; '
        'it is development-only on already-seen IDs. Those results cannot establish model semantic necessity. '
        'The separately registered bilingual literal-resolver probe is synthetic and small.\n')
    write(TASK/'reports/NEGATIVE_LEAKAGE_REGRESSION.md','# Preserved leakage and contract cost\n\n'
        'Historical V4 search12/12 seeds, outer40/120, actual pipeline1/12 and the corresponding V4.1 repairs remain separately locked. '
        'The new fixed-tool corpus has96 synthetic attacks: original actual pipeline releases72, the unchanged V4.1 guard installed at the actual pipeline output boundary releases0, '
        'and the new typed canonical boundary releases0. All three complete12/12 numeric positive controls. '
        'Both strict contracts deny12/12 legitimate explanatory prose records; broad zero-usability-loss is therefore false. '
        'These are one-query boundary replacements, not an adaptive multi-turn LLM red-team search. URL encoding of an ASCII-only canary can be identical to the literal string, '
        'so family names do not imply independent encodings or independent attack ideas. Generic natural-language confidentiality/covert-channel protection is not established.\n')
    write(TASK/'reports/CI_AND_CLUSTER_SENSITIVITY.md','# Statistical status and uncertainty\n\n'
        'Endpoint definitions come from the pre-existing work order; the explicit analysis-family JSON was registered after the first backbone and during the second. '
        'All paired exact McNemar/Holm and task-cluster bootstrap analyses are exploratory. Six domain/backbone C1/C2 comparisons retain planned and scored pairs separately, '
        'excluding unknown paired security values from the exact calculation without dropping them from the ledger. '
        'Task-ID resampling keeps five correlated attack templates together. All-zero differences yield degenerate conditional intervals, not zero unseen risk. '
        'Wilson intervals are conditional on independent binomial sampling/completion; nonrandom backend failure and repeated templates violate simple population inference. '
        'Ministral attack outcomes have two unknown cases per configuration, so planned-N lower/upper bounds are reported alongside scored rates. '
        'Historical true family IDs remain unavailable; the old class-language proxy is not family-disjoint evidence.\n')
    # No human label file is fabricated; only blinded ID links are copied.
    ids=load(OLD/'resources/ai_review_identity_map_private.json')
    csvwrite(TASK/'experiments/human_audit/RATER_BLINDED_IDS.csv',[{'blind_id':r['blind_id'],'source_case_id':r['case_id'],
        'source_role':'historical AI annotation only; no new humans'} for r in ids])
    authors=load(TASK/'manifests/AUTHOR_METADATA.json')
    write(TASK/'submission_private/COVER_LETTER_ELECTRONICS_LGK04C9ZT5.md',
        '# Cover letter draft — HOLD, do not send\n\nDear Guest Editors,\n\n'
        'Please consider “HETE: Typed Authority and Auditable Enforcement for Tool-Using Language-Model Agents” as an Article for Electronics, '
        'Special Issue LGK04C9ZT5, Artificial Intelligence in Cybersecurity: Practices, Challenges, and Innovations. '
        'The study separates model proposals from application-authorized effects through typed authority/evidence records, independent dispatch revalidation and scoped output contracts. '
        'It preserves adverse historical backbone results and encoded-leak counterexamples. An expanded write-capable official-environment evaluation finds no incremental security/utility advantage over an equivalent minimal guard. '
        'The contribution is an auditable execution architecture and failure-preserving evaluation, with finite-sample, backend-compatibility and confidentiality limits. '
        'This fits secure deployment of AI agents and vulnerability mitigation.\n\n'
        'Prior MDPI submission IDs, simultaneous-journal status and any posted preprint remain to be confirmed. No preprint DOI is assigned. '
        'After actual coauthor confirmation, include the required statements verbatim:\n\n'
        '> We confirm that neither the manuscript nor any parts of its content are currently under consideration for publication with or published in another journal.\n'
        '> All authors have approved the manuscript and agree with its submission to Electronics.\n\n'
        'These are conditional draft text, not current factual declarations.\n\nSincerely,\nKi-Hyung Kim (corresponding author from the user-supplied source), Ajou University; kkim86@ajou.ac.kr.\n')
    candidates=[('Florian Tramèr','ETH Zürich','florian.tramer@inf.ethz.ch','https://www.vvz.ethz.ch/Vorlesungsverzeichnis/dozent.view?dozide=10081887&lang=de&semkez=2026S'),
        ('David Wagner','University of California, Berkeley','daw@cs.berkeley.edu','https://www2.eecs.berkeley.edu/Faculty/Homepages/wagner.html'),
        ('Umar Iqbal','Washington University in St. Louis','umar.iqbal@wustl.edu','https://engineering.washu.edu/faculty/Umar-Iqbal.html')]
    csvwrite(TASK/'submission_private/REVIEWER_SUGGESTIONS_PRIVATE.csv',[{'name':n,'affiliation':a,'public_email':e,'primary_source':u,
        'identity_contact_checked':'2026-10-21 primary institutional page','three_year_collaboration_check':'PENDING AUTHOR CONFIRMATION',
        'financial_personal_institutional_conflicts':'UNKNOWN','eligible_for_submission':False} for n,a,e,u in candidates])
    write(TASK/'reports/MDPI_OFFICIAL_SOURCE_CHECK.md',
        '# Official source checks (2026-10-21 KST)\n\n'
        'Special Issue: https://www.mdpi.com/journal/electronics/special_issues/LGK04C9ZT5 (official indexed primary page: deadline2027-01-15, APC CHF2400; direct request returned429). '
        'Author instructions: https://www.mdpi.com/journal/Electronics/instructions (official indexed primary text: about200-word maximum abstract, complete LaTeX ZIP, <=120MB, cover letter and all-author approval). '
        'Preprint guidelines: https://www.preprints.org/help-center/submission-guidelines (direct primary page retrieved). '
        'No acceptance, posted/submitted status, APC payment or license approval is inferred. Reviewer public contacts were checked on institutional primary pages; absence of conflicts was not independently established.\n')
    print('external aggregate rows',len(compact),'failure ledger',len(failures),'reviewer candidates',len(candidates))


if __name__=='__main__':main()
