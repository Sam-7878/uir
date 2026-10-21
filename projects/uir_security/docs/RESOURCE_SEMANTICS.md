# Resource semantics

| Stage | Measured/enforced item | Practical limit |
|---|---|---|
| Preflight | estimated user input size, configured output/context tokens | estimate is not the backend's actual tokenization |
| Checkpoint | tool calls, generation steps, admitted operations | prevents the next operation; does not refund prior work |
| Post-call | actual input/output tokens and elapsed time | detects overshoot already incurred |
| Transport | timeout for a model HTTP request | not a tested guarantee that server/GPU generation stops immediately |

Historical V3.2 uses a 180-second transport timeout and a separate 30-second elapsed
guard. It does not demonstrate streaming cancellation or a hard wall-clock bound.
The V4 mechanism harness checks transaction-step budgets. The local AgentDojo adapter
uses six model/tool steps, a 180-second HTTP timeout, and recorded backend counters.
No new hard-cancellation guarantee is claimed. GPU memory reports are device-wide;
unknown per-process allocation is not reported as zero. Timing includes rejected
paths and admitted backend work; missing original interruption latency stays missing.

The historical benign-length supplement and its severe 900-token utility loss remain
part of the evidence. Longer input is a utility sensitivity, not evidence of an
improved V4 resource guard. See task-local latency quantiles, resource traces and
the explicit preflight/checkpoint/post-call taxonomy.
