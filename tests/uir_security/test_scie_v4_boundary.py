"""State/effect properties for the new V4 mechanism study; no old evidence edited."""
import json
import random
import string

import pytest

from evaluation.scie_v4.boundary import Envelope, Gates, Session


def session():
    return Session('analyst',frozenset({'write:report'}),0,frozenset({'doc-v4'}),frozenset({'private-canary'}))


def action(**changes):
    return {'tool':'create_report','args':{'id':'r','body':'ok','recipient':'internal'},
            'principal':'analyst','expected_revision':0,'nonce':'n'} | changes


def test_authenticated_positive_and_replayed_write():
    e=Envelope(session())
    assert e.commit(json.dumps(action()))['state_mutated']==1
    repeat=action(expected_revision=1,args={'id':'r2','body':'ok','recipient':'internal'})
    assert e.commit(json.dumps(repeat))['reason']=='replay'
    assert e.db.execute('SELECT count(*) FROM reports').fetchone()[0]==1


def test_transaction_failure_rolls_back_action_and_report():
    e=Envelope(session());assert e.commit(json.dumps(action()))['state_mutated']==1
    denied=e.commit(json.dumps(action(nonce='n2',expected_revision=1)))
    assert denied['reason']=='transaction_rollback'
    assert e.db.execute('SELECT count(*) FROM actions').fetchone()[0]==1
    assert e.revision==1


@pytest.mark.parametrize('revision',[True,False,-1,'0',None,1.0])
def test_revision_is_an_exact_nonnegative_integer(revision):
    assert Envelope(session()).commit(json.dumps(action(expected_revision=revision)))['reason']=='schema'


def test_dispatch_detects_permission_revision_change():
    trace=Envelope(session()).commit(json.dumps(action()),current_revision=1)
    assert trace['admitted']==1 and trace['executor_invoked']==0
    assert trace['reason']=='revalidation'


def test_capability_and_dispatch_checks_mask_one_another():
    value=action(tool='wire_transfer',args={'amount':1,'recipient':'internal'})
    for capability,revalidation,expected in [(True,True,0),(False,True,0),(True,False,0),(False,False,1)]:
        e=Envelope(session(),gates=Gates(capability=capability,revalidation=revalidation))
        assert e.commit(json.dumps(value))['state_mutated']==expected


def test_seeded_unicode_principal_non_escalation():
    rng=random.Random(20261021)
    alphabet=string.ascii_letters+'аαＡ\u200b\ufeff'
    for _ in range(500):
        principal=''.join(rng.choices(alphabet,k=rng.randint(1,32)))
        trace=Envelope(session()).commit(json.dumps(action(principal=principal)))
        assert trace['state_mutated']==0


@pytest.mark.parametrize('suffix',[' trailing','{}','\n```','\x00'])
def test_whole_json_is_required(suffix):
    assert Envelope(session()).commit(json.dumps(action())+suffix)['reason']=='schema'


def test_duplicate_key_rejected():
    text=json.dumps(action()).replace('"principal": "analyst"','"principal":"admin","principal":"analyst"')
    assert Envelope(session()).commit(text)['reason']=='schema'
