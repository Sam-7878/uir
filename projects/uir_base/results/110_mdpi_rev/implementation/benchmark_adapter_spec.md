# FinQA adapter and prospective model amendment

`next_benchmark_adapter.py` is a CUSTOM bounded source-number arithmetic
contract, not the official evaluator. It strictly consumes binary add/subtract/
multiply/divide/greater programs, previous-step references and three declared
constants. No gold program selects runtime evidence or operands. It does not
validate units, periods, semantic operand selection, or arbitrary prose.

The repository's pinned official evaluate.py is loaded independently in parity
checks. Seven executable-intersection fixtures agree; twelve fixtures also
document intentional rejected cases and unsupported official operators. This
is not full parity over all FinQA programs. 172/200 heldout gold programs are
executable by this contract with full source text, an evaluation-only estimate,
not guaranteed runtime retrieval coverage.

Both models use the same question-only lexical retrieval (top 12 report/table
lines), decoding limits, native-answer adapter and program executor. C1 uses a
final answer marker; C8 uses structured programs. End-to-end primary correctness
requires a finished response and exact task value rounded to five decimals on
all 200 indices. Semantic literal, format, contract, execution, and finish states
are reported separately. Unsupported claims are NOT_MEASURED, not zero.

The index set is disjoint from the historical 200, but 71 source documents and
180 companies overlap development. This is not a document/company-generalization
holdout. Original dataset SHA-256 and these overlaps are in adapter_verification.

User-approved prospective amendment: use Qwen3-1.7B rather than Qwen2.5-7B;
freeze a new v2 protocol before inference. Preserve every old result and original
unexecuted protocol. Qwen3 is non-thinking in the primary comparison, with the
same 512 generated-token limit as Phi. Different tokenizers, model sizes and
Q4_0 versus Q4_K_M are explicitly not equalized by that visible budget.
