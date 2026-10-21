"""P2 local persistent transaction workflow; no network tools or real accounts."""
import json

from .boundary import Envelope, Session
from .common import TASK, sha, write


def main():
    database=TASK/'data/integration_demo.sqlite'
    if database.exists():
        raise RuntimeError('Demo database already exists; use recorded results or a new task')
    session=Session('analyst',frozenset({'write:report'}),0,frozenset({'doc-v4'}),frozenset({'private-canary'}))
    e=Envelope(session,str(database))
    def action(identity,nonce,revision,principal='analyst'):
        return json.dumps({'tool':'create_report','args':{'id':identity,'body':'trusted evidence report','recipient':'internal'},
                           'principal':principal,'expected_revision':revision,'nonce':nonce})
    steps=[('authorized_write',action('r1','n1',0)),('replayed_authorization',action('r2','n1',1)),
           ('rollback_on_duplicate_report',action('r1','n2',1)),('forged_principal',action('r2','n3',1,'admin')),
           ('second_authorized_write',action('r2','n4',1)),('budget_exhausted',action('r3','n5',2))]
    traces=[{'name':name,**e.commit(raw)} for name,raw in steps]
    counts={'reports':e.db.execute('SELECT count(*) FROM reports').fetchone()[0],
            'committed_actions':e.db.execute('SELECT count(*) FROM actions').fetchone()[0],'revision':e.revision}
    e.close()
    result={'workflow':'trusted Session -> proposal -> capability/argument/revision -> SQLite commit -> audit',
            'traces':traces,'counts':counts,'database_sha256':sha(database),
            'scope':'persistent local sandbox API/SQLite demo; not a distributed enterprise integration',
            'passed':counts=={'reports':2,'committed_actions':2,'revision':2}}
    write(TASK/'data/integration_demo_trace.json',result)
    write(TASK/'reports/tool_trace_report.md','# Persistent local transaction demonstration\n\n'+json.dumps(result,indent=2)+'\n')
    print(json.dumps(counts))


if __name__=='__main__':main()
