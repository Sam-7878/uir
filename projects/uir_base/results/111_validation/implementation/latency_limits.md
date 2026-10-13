# Timing scope

The protocol specifies five warm common-guard repetitions for each compilable
development request. Initial measurements include frontend/artifact processing
and TWO backend checks; they exclude module imports. The saved initial label
“load-inclusive” is not a GPU cold-start measurement. Warm values time only
guard/renderer, so comparing them to whole frontend time is invalid.

New GPU renderer requests have wall timestamps, token counts/finish/load timing
and a first-load marker, one request per case/condition. They are descriptive
single-run distributions, not repeated transformer efficiency estimates.
Policy early refusal and deterministic-only workload reduction are separate from
transformer arithmetic acceleration. No generic speed advantage is claimed.
