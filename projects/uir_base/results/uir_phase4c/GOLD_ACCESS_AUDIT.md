# Phase UIR-4C gold-access audit

Audit rule: model-generation modules may read only pre-registered runtime files. Expected claims, answers, programs, execution answers, and hallucination labels may be opened only by post-generation scorers. HaluEval's presented candidate answer is a benchmark stimulus, not a label; the unselected alternative and its label are excluded from runtime files.

| File/function | Field/access | Phase | Status and reason |
|---|---|---|---|
| `freeze_inputs.py::_score_internal` | internal expected claims/outcome | pre-registration, scoring partition only | Allowed: written only to a separate scoring file never opened by a runner. |
| `freeze_inputs.py::freeze_halueval` | `right_answer` or `hallucinated_answer` | pre-registration stimulus selection | Allowed: official HaluEval requires presenting one candidate answer. No candidate type or label is written to runtime data. |
| `run_actual_baselines.py` | no scoring file or gold field | generation | Allowed. |
| `run_official_benchmarks.py` | no official source file and no gold value | generation | Allowed. It opens only stripped frozen runtime files. |
| `score_actual_evidence.py::score` | internal expected claims/outcomes | post-generation scoring | Allowed. |
| `score_official_benchmarks.py::score_finqa` | `qa.exe_ans`, `qa.program` | post-generation scoring | Allowed. |
| `score_official_benchmarks.py::score_halueval` | candidate provenance against right/hallucinated alternatives | post-generation scoring | Allowed. |
| `official_sources/FinQA/evaluate.py` | official FinQA gold result/program | post-generation scorer dependency | Allowed; never imported by a generation runner. |
| `test_phase4c_authenticity.py` | source gold fields | test-only source/runtime partition audit | Allowed; no prediction is produced. |

Static searches also include `ground_truth`, `official_ground_truth`, `gold`, `exe_ans`, `right_answer`, `hallucinated_answer`, `success_probability`, `success_rate`, and `target_accuracy`. No generation path uses any such value to construct a prediction.

`forbidden_pre_generation_gold_access = 0`
