import json
import sqlite3
from dataclasses import replace

import pytest

from projects.uir_security.evaluation.scie_v4_2.typed_engine import (
    ApprovedAction,AuthorityStore,Budget,Capability,Gates,MinimalGuard,PolicyRevision,
    TrustedSession,TypedInterpreter,
)


def engine(cls=TypedInterpreter,gates=Gates(),principal='owner',approved=True):
    session=TrustedSession('run-1',principal,PolicyRevision(2),
        (Capability('write_report','report-1',True),),frozenset({'report-1'}),
        frozenset({'report-1'}) if approved else frozenset(),Budget(max_steps=3))
    store=AuthorityStore(session);store.add_signer('curator',1)
    store.endorse('doc-1','verified body','curator','report')
    db=sqlite3.connect(':memory:');db.execute('CREATE TABLE report (id TEXT PRIMARY KEY, body TEXT)')
    def execute(tool,args):
        with db:db.execute('INSERT INTO report VALUES (?,?)',(args['id'],args['body']))
        return {'ok':True},True
    schema={'type':'object','properties':{'id':{'type':'string'},'body':{'type':'string'}},
            'required':['id','body'],'additionalProperties':False}
    obj=cls(store,{'write_report':schema},execute,
        lambda t,a,s:s.owners.get(a['id'])==s.session.principal,
        lambda t,a:a['id'],{'write_report':'report'},gates)
    return obj,db


@pytest.mark.parametrize('cls',[TypedInterpreter,MinimalGuard])
def test_positive_replay_and_actual_committed_effect(cls):
    e,db=engine(cls)
    result=e.submit('write_report',{'id':'report-1','body':'approved'},'n',['doc-1'])
    assert result['executor_invoked'] and result['state_mutated']
    assert db.execute('SELECT body FROM report').fetchone()==('approved',)
    assert e.submit('write_report',{'id':'report-1','body':'again'},'n',['doc-1'])['reason']=='replay'


def test_compiled_object_proof_and_dispatch_mutation_are_bound():
    e,db=engine();approved,event=e.compile('{"tool":"write_report","args":{"id":"report-1","body":"ok"}}','n',['doc-1'])
    assert isinstance(approved,ApprovedAction)
    tampered=replace(approved,arguments_json='{"id":"report-1","body":"tampered"}')
    assert e.dispatch(tampered,event)['reason']=='proof'
    assert db.execute('SELECT count(*) FROM report').fetchone()[0]==0


@pytest.mark.parametrize('field,value',[('principal','admin'),('expected_revision',True),('trusted',True)])
def test_untrusted_json_cannot_mint_authority(field,value):
    e,db=engine();obj={'tool':'write_report','args':{'id':'report-1','body':'ok'},field:value}
    assert e.compile(json.dumps(obj),'n',['doc-1'])[0] is None
    assert db.execute('SELECT count(*) FROM report').fetchone()[0]==0


@pytest.mark.parametrize('change',['revision','ownership','revocation'])
def test_toctou_rechecks_live_trusted_state(change):
    e,db=engine()
    def race(store):
        if change=='revision':store.update_revision(3)
        if change=='ownership':store.owners['report-1']='another-principal'
        if change=='revocation':store.revoked.add(('curator',1))
    r=e.submit('write_report',{'id':'report-1','body':'ok'},'n',['doc-1'],before_dispatch=race)
    assert r['admitted'] and not r['executor_invoked']
    assert db.execute('SELECT count(*) FROM report').fetchone()[0]==0


def test_revoked_key_and_scope_are_not_hash_truth():
    e,db=engine();store=e.store
    assert store.verify_evidence('doc-1','report')
    assert not store.verify_evidence('doc-1','arbitrary_facts')
    store.revoked.add(('curator',1));assert not store.verify_evidence('doc-1','report')
    store.add_signer('curator',2);store.endorse('doc-2','verified body','curator','report',2)
    assert store.verify_evidence('doc-2','report')
    assert e.submit('write_report',{'id':'report-1','body':'ok'},'n',['doc-2'])['state_mutated']


@pytest.mark.parametrize('value',[True,False,-1,1.0,'2',None])
def test_revision_rejects_bool_float_and_rollback(value):
    with pytest.raises(ValueError):PolicyRevision(value)


def test_store_revision_only_advances():
    e,_=engine()
    with pytest.raises(ValueError):e.store.update_revision(1)


def test_explicit_approval_required_for_legitimate_write():
    e,db=engine(approved=False)
    assert e.submit('write_report',{'id':'report-1','body':'ok'},'n',['doc-1'])['reason']=='approval'
    assert not db.execute('SELECT * FROM report').fetchall()


@pytest.mark.parametrize('bad',['{"tool":"x","tool":"write_report","args":{}}',
                              '{"tool":"write_report","args":{"id":"report-1","body":NaN}}',
                              '{"tool":"ｗrite_report","args":{}}'])
def test_malformed_or_confusable_uir_never_reaches_executor(bad):
    e,db=engine();assert e.compile(bad,'n',['doc-1'])[0] is None
    assert not db.execute('SELECT * FROM report').fetchall()


def test_canonical_numeric_egress_and_post_call_resource_overrun():
    e,_=engine();good={'entity':'AAPL','metric':'revenue','value':100,'fiscal_year':2023,'citations':['doc-1']}
    assert e.release(good,'numeric_v4_1',good)['egress_released']
    assert not e.release(good|{'summary':'encoded-leak'},'numeric_v4_1',good)['egress_released']
    e.model_tokens=999999
    assert e.release('hello')['reason']=='post_call_budget'
