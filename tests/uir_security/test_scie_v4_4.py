from dataclasses import replace
import json

import pytest

from projects.uir_security.evaluation.scie_v4_4.adaptive import final_note
from projects.uir_security.evaluation.scie_v4_4.backend.ollama import classify
from projects.uir_security.evaluation.scie_v4_4.dataset import build_case, generate, runtime_prompt
from projects.uir_security.evaluation.scie_v4_4.engine import Invalid, World, parse
from projects.uir_security.evaluation.scie_v4_4.judges import score
from projects.uir_security.evaluation.scie_v4_4.run_frozen_campaign import model_observations


def refund():
    return build_case('pilot','refund',0,'en')


@pytest.mark.parametrize('arm', ['C1_flat','C2_typed'])
def test_current_state_replay_and_tamper(arm):
    case,gold=refund()
    w=World(case,arm)
    action=gold['effects']
    carrier,tag=w.compile(action,'n1')
    if arm=='C1_flat':
        modified={**carrier,'principal':'someone_else'}
    else:
        modified=replace(carrier,principal='someone_else')
    assert w.dispatch(modified,tag) is None
    assert w.dispatch(carrier,tag)==[]
    assert w.dispatch(carrier,tag) is None
    assert w.result()['effects']==action
    stale=w.compile(action,'n2')
    w.rev+=1
    assert w.dispatch(*stale) is None
    assert w.result()['effects']==action


@pytest.mark.parametrize('mutation',['principal','approval','record','owner','revision'])
def test_dispatch_is_bound_to_live_authority(mutation):
    case,gold=build_case('pilot','dispatch',0,'en')
    w=World(case,'C2_typed')
    plan=w.compile(gold['effects'],'n')
    if mutation=='principal':
        w.principal='not_owner'
    elif mutation=='approval':
        w.approval='revoked'
    elif mutation=='record':
        w.records[gold['refs'][0]]['value']+=1
    elif mutation=='owner':
        w.grants[0]['recipient']='not_owner'
    else:
        w.rev+=1
    assert w.dispatch(*plan) is None
    assert w.result()['effects']==[] and w.result()['outbox']==[]


def test_no_live_recheck_knockout_distinguishes_layer():
    case,gold=refund()
    outcomes=[]
    for arm in ('C1_flat','K4_no_live_recheck'):
        w=World(case,arm)
        plan=w.compile(gold['effects'],'n')
        w.approval='revoked'
        w.dispatch(*plan)
        outcomes.append(w.result()['effects'])
    assert outcomes==[[],gold['effects']]


def test_unauthorized_send_is_real_outbox_not_marker():
    case,gold=build_case('pilot','dispatch',0,'en')
    action=list(gold['effects'][0]); action[2]='bad@example.invalid'
    for arm in ('C0_open','C1_flat','C2_typed','K2_no_capability'):
        w=World(case,arm)
        plan=w.compile([action],'n')
        if plan: w.dispatch(*plan)
        actual=w.result()
        if arm in ('C0_open','K2_no_capability'):
            assert actual['effects']==[action]
            assert actual['outbox'][0]['to']==action[2]
        else:
            assert not actual['effects'] and not actual['outbox']


def test_restricted_ref_actual_egress_and_projection():
    case,_=refund()
    ref=next(k for k in case['records'] if k.startswith('private'))
    token=case['records'][ref]['value']
    for arm in ('C0_open','C1_flat','C2_typed','K1_no_provenance','K3_no_egress'):
        w=World(case,arm)
        proposal={'actions':[['read',ref]],'answer':{'mode':'single','refs':[ref],'language':'en'}}
        r=w.apply(proposal,'n')
        projected=model_observations(r or [])
        assert token not in json.dumps(projected)
        leaked=any(token in o['text'] for o in w.result()['outbox'])
        assert leaked==(arm in ('C0_open','K3_no_egress'))


def test_atomic_rollback_and_cross_world_proof():
    case,gold=refund()
    case['grants'].append({**case['grants'][0],'ceiling':100})
    w=World(case,'C1_flat')
    a=gold['effects'][0]
    carrier,tag=w.compile([a,[*a[:3],9]],'n')
    assert World(case,'C2_typed').dispatch(carrier,tag) is None
    assert w.dispatch(carrier,tag) is None and not w.result()['effects']


def test_oracle_data_and_canary_not_in_model_input():
    runtime,gold=generate('final')
    for item,expected in zip(runtime,gold):
        surface=item.get('attack_surface')
        prompt=runtime_prompt(item,final_note(surface,0) if surface else '')
        assert not {'expected_effects','gold','attack_goal','judge_metadata'}&set(item)
        assert all(v['value'] not in prompt for v in item['records'].values() if v['visibility']=='restricted')
        assert 'approved_snapshot' not in prompt and expected['cluster'] not in prompt


def test_decoder_rejects_duplicates_and_confusables():
    with pytest.raises(Invalid):
        parse('{"actions":[],"actions":[],"answer":{}}')
    with pytest.raises(Invalid):
        parse(json.dumps({'actions':[['read','pub-Ｈ00a']],'answer':{'mode':'none','refs':[],'language':'en'}}))


def test_incomplete_response_not_counted_as_safe():
    options={'num_ctx':4096,'num_predict':176}
    assert classify({'done':True,'done_reason':'length','response':'{}'},options)=='INCOMPLETE_RESPONSE'
    case,gold=refund()
    row={'status':'TIMEOUT','call_ids':[],'proposals':[],'actual':{'outbox':[],'effects':[]}}
    assert score(row,case,gold,{})['e2e_asr'] is None
