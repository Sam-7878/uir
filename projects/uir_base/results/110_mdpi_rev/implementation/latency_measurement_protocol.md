# Local request timing scope

RTX3090 UUID GPU-ab53069a-3217-ee09-80f8-748b5fdbd156, one loaded model,
sequential requests, loopback-only transport, one repetition per request, no retry.
Raw request logs record queue/start/end timestamps, total request duration, token
counts/runtime metadata in original responses, first-load-inclusive flag and
batch_size=1. Phi matched development also records gate/template/projection stages.

The first model request is separated from subsequent warm requests and early
rejections. Quantiles describe observed requests, not repeated-measurement
reliability or cold-load distribution (the first-load stratum has one observation).
CPU template timing is an actual measured stage plus gate, not its complete
application end-to-end latency. Do not compare it as a transformer speedup.

Historical latency remains historical_batch_shared_latency. Old run batch time
assigned to each case is not an independent request-level p95/p99 measurement.
Fresh and counterfactual replay timing/cost remain different evidence kinds.
