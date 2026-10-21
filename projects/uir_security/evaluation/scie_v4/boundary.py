"""V4 research boundary: proposals never mint authority; SQLite effects are local.

This is a new mechanism test implementation, not a replacement for V3.2 evidence.
The caller supplies an authenticated session; authentication and key storage are TCB
assumptions. No oracle, attack class, or expected verdict enters this module.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass

from llm_trust.security.output_guard import OutputGuard


@dataclass(frozen=True)
class Session:
    principal: str
    capabilities: frozenset[str]
    revision: int
    evidence_ids: frozenset[str]
    confidential: frozenset[str]
    allowed_recipient: str = 'internal'
    max_amount: int = 10
    max_steps: int = 2


@dataclass(frozen=True)
class Gates:
    capability: bool = True
    arguments: bool = True
    principal: bool = True
    revalidation: bool = True
    replay: bool = True
    output: bool = True
    resource: bool = True


class Envelope:
    def __init__(self, session: Session, database: str = ':memory:', gates: Gates = Gates()):
        self.session = session
        self.gates = gates
        self.db = sqlite3.connect(database, isolation_level=None)
        self.db.execute('CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, body TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS actions (nonce TEXT PRIMARY KEY, payload TEXT)')
        self.revision = session.revision
        self.steps = 0
        self.seen: set[str] = set()
        self.audit: list[dict] = []

    def commit(self, raw: str, *, current_revision: int | None = None) -> dict:
        trace = {'proposed': 0, 'admitted': 0, 'executor_invoked': 0, 'state_mutated': 0,
                 'egress_released': False, 'policy_verdict': 'DENY', 'reason': '',
                 'raw_sha256': hashlib.sha256(raw.encode()).hexdigest(), 'steps_before': self.steps}
        def reject(reason):
            trace['reason'] = reason
            self.audit.append(dict(trace))
            return trace
        def no_duplicates(pairs):
            data = {}
            for key, value in pairs:
                if key in data:
                    raise ValueError('duplicate JSON key')
                data[key] = value
            return data
        try:
            data = json.loads(raw, object_pairs_hook=no_duplicates,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
        except (ValueError, TypeError):
            return reject('schema')
        if not isinstance(data, dict):
            return reject('schema')
        if 'tool' not in data:
            verdict = OutputGuard().validate(raw, expected_schema_id='financial_summary_v3_2',
                admissible_evidence_ids=set(self.session.evidence_ids),
                confidential_tokens=set(self.session.confidential),
                evidence_claims={e: {'entity': 'AAPL', 'metric': 'revenue', 'value': '100B USD',
                                     'currency': 'USD', 'fiscal_year': 2023} for e in self.session.evidence_ids})
            if self.gates.output and not verdict.is_safe:
                return reject('output:' + verdict.status.value)
            trace.update(egress_released=True, policy_verdict='ALLOW')
            self.audit.append(dict(trace))
            return trace
        trace['proposed'] = 1
        required = {'tool', 'args', 'principal', 'expected_revision', 'nonce'}
        if (set(data) != required or not isinstance(data['args'], dict)
                or not isinstance(data['nonce'], str) or not data['nonce']
                or not isinstance(data['principal'], str)
                or type(data['expected_revision']) is not int or data['expected_revision'] < 0):
            return reject('schema')
        tool, args, nonce = data['tool'], data['args'], data['nonce']
        if tool not in {'create_report', 'wire_transfer'}:
            return reject('registry')
        capability = {'create_report': 'write:report', 'wire_transfer': 'write:transfer'}[tool]
        if self.gates.principal and data['principal'] != self.session.principal:
            return reject('principal')
        if self.gates.capability and capability not in self.session.capabilities:
            return reject('capability')
        if self.gates.arguments:
            if tool == 'create_report':
                valid = set(args) == {'id', 'body', 'recipient'} and all(isinstance(v, str) for v in args.values())
                valid = valid and args.get('recipient') == self.session.allowed_recipient
                valid = valid and not any(token in json.dumps(args) for token in self.session.confidential)
            else:
                valid = set(args) == {'amount', 'recipient'} and type(args.get('amount')) is int
                valid = valid and 0 < args['amount'] <= self.session.max_amount and args['recipient'] == self.session.allowed_recipient
            if not valid:
                return reject('arguments')
        if self.gates.resource and self.steps >= self.session.max_steps:
            return reject('resource')
        # Permission/revision snapshot is checked again at dispatch, not just admission.
        trace['admitted'] = 1
        effective_revision = self.revision if current_revision is None else current_revision
        if self.gates.revalidation and (data['expected_revision'] != effective_revision or capability not in self.session.capabilities):
            return reject('revalidation')
        if self.gates.replay and nonce in self.seen:
            return reject('replay')
        try:
            self.db.execute('BEGIN IMMEDIATE')
            trace['executor_invoked'] = 1
            if tool == 'create_report':
                self.db.execute('INSERT INTO reports VALUES (?, ?)', (args['id'], args['body']))
            self.db.execute('INSERT INTO actions VALUES (?, ?)', (nonce, raw))
            self.db.execute('COMMIT')
        except (sqlite3.Error, KeyError, TypeError):
            self.db.execute('ROLLBACK')
            return reject('transaction_rollback')
        self.steps += 1
        self.revision += 1
        self.seen.add(nonce)
        trace.update(state_mutated=1, policy_verdict='ALLOW')
        self.audit.append(dict(trace))
        return trace

    def close(self):
        self.db.close()
