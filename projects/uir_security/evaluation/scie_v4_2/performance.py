"""Matched CPU admission/commit microbenchmark, separate from cached inference."""
from .common import *
from .mechanism import instance

import random
import time
import numpy as np


def main():
    freeze(TASK/'manifests/POLICY_TIMING_PROTOCOL.json',{'id':'HETE-policy-timing-V4.2-001','n_per_system':200,
        'seed':421021,'systems':['minimal','typed'],'source_sha256':sha(Path(__file__)),
        'scope':'same authorized SQLite write; timer excludes session/key/database construction, includes admission/proof/revalidation/transaction; not GPU or application end-to-end latency'})
    rng=random.Random(421021);records=[]
    for i in range(200):
        order=['minimal','typed'];rng.shuffle(order)
        for system in order:
            e,db=instance(system);start=time.perf_counter_ns()
            event=e.submit('write_report',{'id':'report-1','body':'same authorized record'},'n',['doc-1'])
            elapsed=(time.perf_counter_ns()-start)/1000.
            assert event['state_mutated'];db.close()
            records.append({'pair':i,'system':system,'latency_us':elapsed,'actual_write':True})
    csvwrite(TASK/'experiments/policy_incremental/POLICY_TIMING_RAW.csv',records)
    summary=[{'system':s,'n':200,'p50_us':float(np.quantile([r['latency_us'] for r in records if r['system']==s],.5)),
        'p95_us':float(np.quantile([r['latency_us'] for r in records if r['system']==s],.95)),
        'p99_us':float(np.quantile([r['latency_us'] for r in records if r['system']==s],.99))} for s in ('minimal','typed')]
    csvwrite(TASK/'experiments/policy_incremental/POLICY_TIMING_SUMMARY.csv',summary);print(canonical(summary))


if __name__=='__main__':main()
