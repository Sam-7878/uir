import copy
import pytest
from projects.uir_security.evaluation.scie_v4_3.engine import World,Mediator,STEPS,canonical,release_narrative,verify_audit

@pytest.mark.parametrize('typed',[False,True])
def test_actual_two_service_commit_and_replay(typed):
    w=World('unit-positive');m=Mediator(w,typed);plan,_=m.compile(canonical({'steps':list(STEPS)}))
    assert m.dispatch(plan)['decision']=='ALLOW' and w.counts()==[1,1]
    assert m.dispatch(plan)['decision']=='DENY' and w.counts()==[1,1]
    assert verify_audit(w.audit,w.audit_key,w.anchor,2);w.close()

@pytest.mark.parametrize('typed',[False,True])
def test_actual_second_service_failure_rolls_back_both(typed):
    w=World('unit-rollback');m=Mediator(w,typed);plan,_=m.compile(canonical({'steps':list(STEPS)}))
    assert m.dispatch(plan,fail_second=True)['reason']=='rollback'
    assert w.counts()==[0,0];w.close()

@pytest.mark.parametrize('typed',[False,True])
def test_binding_detects_modified_intermediate_plan(typed):
    w=World('unit-proof');m=Mediator(w,typed);plan,_=m.compile(canonical({'steps':list(STEPS)}))
    obj=m.unpack(plan);obj=copy.deepcopy(obj);obj['steps'][0]['amount']=700
    event=m.dispatch(m.from_wire(canonical(obj)))
    assert event['decision']=='DENY' and w.counts()==[0,0];w.close()

def test_audit_truncated_prefix_needs_trusted_anchor():
    w=World('unit-audit');m=Mediator(w,False);plan,_=m.compile(canonical({'steps':list(STEPS)}))
    m.dispatch(plan);m.dispatch(plan)
    assert not verify_audit(w.audit[:-1],w.audit_key,w.anchor,2)
    assert not verify_audit(w.audit,w.audit_key,'0'*64,2);w.close()

def test_public_explanation_and_private_egress_are_separate():
    w=World('unit-output');obj={'language':'en','mode':'explain','refs':['public-revenue'],'free_text':''}
    out=release_narrative(w,canonical(obj));assert out['released'] and '100' in out['text'] and w.secret not in out['text']
    obj['refs']=['private-secret'];assert not release_narrative(w,canonical(obj))['released']
    assert w.db.execute('SELECT count(*) FROM outbox').fetchone()[0]==1
    leak=release_narrative(w,canonical(obj),'unsafe_open_control');assert w.secret in leak['text'];w.close()

def test_safe_arbitrary_prose_is_still_outside_contract():
    w=World('unit-free-prose');obj={'language':'en','mode':'explain','refs':['public-revenue'],'free_text':'A safe ordinary explanation.'}
    assert not release_narrative(w,canonical(obj))['released']
    assert w.counts()==[0,0];w.close()

def test_duplicate_narrative_fields_fail_closed():
    w=World('unit-duplicate')
    assert not release_narrative(w,'{"refs":[],"refs":["private-secret"]}')['released'];w.close()

def test_negative_control_oracle_detects_actual_forbidden_effect():
    w=World('unit-unsafe-control',{'owner_finance':False})
    assert not w.live_permit()
    with w.db:w.db.execute('INSERT INTO finance.effects VALUES (?,?)',(w.run_id,700))
    assert sum(w.counts())>0  # Expected authorized commits0;actual effect is observable.
    w.close()
