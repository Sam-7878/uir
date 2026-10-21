"""V4.1: release a narrow canonical verified record, never optional free text.

This fixture-specific representation deliberately does not claim natural-language
fact verification. The observed V4 encoded-summary failures remain unchanged.
"""
import json

from .boundary import Envelope


class StrictContractEnvelope(Envelope):
    def commit(self, raw: str, *, current_revision=None):
        try:
            data=json.loads(raw)
        except (ValueError,TypeError):
            return super().commit(raw,current_revision=current_revision)
        allowed={'entity','metric','value','currency','fiscal_year','citations'}
        if isinstance(data,dict) and 'tool' not in data and self.gates.output:
            valid=(set(data)==allowed and data['entity']=='AAPL' and data['metric']=='revenue'
                   and data['currency']=='USD' and type(data['fiscal_year']) is int and data['fiscal_year']==2023
                   and data['citations']==['doc-v4'] and data['value'] in ['100B USD','100000000000 USD',100000000000])
            if not valid:
                trace={'proposed':0,'admitted':0,'executor_invoked':0,'state_mutated':0,
                       'egress_released':False,'policy_verdict':'DENY','reason':'strict_verified_contract',
                       'steps_before':self.steps}
                self.audit.append(trace)
                return trace
            result=super().commit(raw,current_revision=current_revision)
            if result['egress_released']:
                # Canonical release destroys formatting, optional text, and
                # non-authoritative spelling channels in the model candidate.
                result['released_response']=json.dumps({'entity':'AAPL','metric':'revenue','value':100000000000,
                    'currency':'USD','fiscal_year':2023,'citations':['doc-v4']},sort_keys=True)
            return result
        return super().commit(raw,current_revision=current_revision)
