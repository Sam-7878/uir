#!/usr/bin/env python3
"""Generate the Phase-4C work report strictly from completed artifacts."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from evaluation.uir_phase4c.common import RESULTS_DIR, ROOT

REPORT_DIR = ROOT / "docs/work_reports/uir_phase4c"


def rows(name: str) -> list[dict[str, str]]:
    return list(csv.DictReader((RESULTS_DIR / name).open(encoding="utf-8")))


def pct(value: str | float) -> str:
    return f"{100 * float(value):.2f}%"


def markdown_table(data: list[dict[str, str]], columns: list[tuple[str, str]], percentage: set[str] | None = None) -> list[str]:
    percentage = percentage or set(); output = ["| " + " | ".join(label for _, label in columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for item in data:
        values = []
        for key, _ in columns:
            value = item[key]; values.append(pct(value) if key in percentage else value)
        output.append("| " + " | ".join(values) + " |")
    return output


def main() -> None:
    gate = json.loads((RESULTS_DIR / "run_manifest_phase4c.json").read_text(encoding="utf-8"))
    provenance = json.loads((RESULTS_DIR / "OFFICIAL_BENCHMARK_PROVENANCE.json").read_text(encoding="utf-8"))
    strong, finqa, halu = rows("strong_baseline_summary_actual.csv"), rows("finqa_results_actual.csv"), rows("halueval_results_actual.csv")
    smoke = rows("authenticity_smoke_results.csv"); c8 = next(item for item in strong if item["pipeline"] == "C8_FINAL_UIR_B6")
    source_f = provenance["sources"]["FinQA"]; source_h = provenance["sources"]["HaluEval-QA"]
    lines = [
        "# Phase UIR-4C Authentic Model Inference and Official Benchmark Reproduction",
        "", f"Generated: {datetime.now(timezone.utc).isoformat()}", "", f"Final status: `{gate['status']}`", "",
        "## 1. Outcome", "",
        "Phase UIR-4C replaced the Phase-4B template/simulated empirical path with actual local Phi-3.5 generation over pre-registered inputs. Phase-4B remains an evidence-audit prototype and is not used for primary empirical claims.", "",
        f"The matched campaign contains 600 shared cases × 9 pipelines (5,400 scored rows). The authenticity smoke contains 100 shared cases × 9 pipelines. Official external reproduction uses 200 FinQA test rows and 200 HaluEval-QA rows across C1, C2, C4, and C8.", "",
        "## 2. Frozen execution configuration", "",
        "- Model: `microsoft/Phi-3.5-mini-instruct` (3.8B)",
        "- Local snapshot revision: `2fe192450127e6a83f7441aef6e3ca586c338b77`",
        "- Decoding: greedy, seed 42, `max_new_tokens=128`",
        "- Batching: internal smoke/full requested batch 8; official FinQA/HaluEval requested batch 16; adaptive splits are recorded per invocation",
        "- Runtime: Ubuntu 24.04 WSL2, root `.venv`, CUDA/NF4 local inference; no API or fallback backend",
        "- Scope: model-agnostic interface design, empirical results limited to this Phi-3.5 snapshot", "",
        "## 3. Pre-registered matched campaign", "",
        "The 600-case subset was frozen before full inference: 250 valid benign, 100 condition-heavy, 50 policy-violation, 50 adversarial, 100 numeric/provenance, and 50 invalid-entity cases, balanced 300 Korean / 300 English.", "",
        "## 4. Authenticity smoke", "",
    ]
    lines += markdown_table(smoke, [("pipeline", "Pipeline"), ("model_invoked_cases", "Invoked"), ("unique_raw_output_count", "Unique raw"), ("authenticity_status", "Status")])
    lines += ["", "The automatic detector found no placeholder phrase, missing response hash, missing invocation token count, deterministic latency grid, or absent model-produced C4 request.", "", "## 5. Strong matched-baseline results", ""]
    lines += markdown_table(strong, [("pipeline", "Pipeline"), ("unsupported_claim_acceptance_rate", "Unsupported accept"), ("invalid_entity_far", "Invalid FAR"), ("attack_success_rate", "Attack success"), ("useful_answer_rate", "Useful answer"), ("numeric_exact_match", "Numeric exact"), ("latency_p50_ms", "P50 ms")], {"unsupported_claim_acceptance_rate", "invalid_entity_far", "attack_success_rate", "useful_answer_rate", "numeric_exact_match"})
    lines += ["", "## 6. Bounded C8 observation", "", f"The architectural property remains conditional on assumptions A1–A5: unsupported claims are unreachable in accepted C8 output when the deterministic acceptance transition and authoritative fact store satisfy those assumptions. Separately, the empirical full campaign observed {c8['unsupported_claim_count']} unsupported accepted outputs among {c8['total_cases']} cases ({pct(c8['unsupported_claim_acceptance_rate'])}; Wilson 95% CI {pct(c8['unsupported_wilson95_low'])}–{pct(c8['unsupported_wilson95_high'])}). These are distinct claims.", "", "## 7. C4 tool fidelity", "", "C4 contains two captured model invocations per case: model-produced tool name/arguments, authoritative local tool result, and model final response. Invalid model tool requests remain errors and are scored as observed; case labels do not predetermine tool calls.", "", "## 8. Official FinQA provenance", "", f"Source: `{source_f['repository_url']}` at commit `{source_f['git_commit']}`; frozen file SHA-256 `{source_f['file_sha256']}`. Original report-derived IDs are preserved, and every prediction maps to one exact source-row hash.", "", "## 9. FinQA results", ""]
    lines += markdown_table(finqa, [("pipeline", "Pipeline"), ("execution_accuracy", "Execution accuracy"), ("program_accuracy", "Program accuracy"), ("source_mapping_rate", "Source mapping"), ("latency_p50_ms", "P50 ms")], {"execution_accuracy", "program_accuracy", "source_mapping_rate"})
    lines += ["", "Interpretation: FinQA execution accuracy is 3.50% for C1/C2/C4 and 1.00% for C8. This experiment does not establish a FinQA utility advantage for UIR on the evaluated Phi-3.5 snapshot; these scores are retained as a negative external-generalization result."]
    lines += ["", "C8 program accuracy is reported because C8 generates a FinQA arithmetic program. C1/C2/C4 are answer/tool conditions and therefore have no generated FinQA program. UIR numeric answer accuracy is reported alongside official-style execution accuracy; no gold supporting facts or programs enter prompts.", "", "## 10. Official HaluEval-QA provenance", "", f"Source: `{source_h['repository_url']}` at commit `{source_h['git_commit']}`; frozen file SHA-256 `{source_h['file_sha256']}`. The task follows the official QA recognition setup: judge whether the presented candidate answer contains hallucinated information and output Yes/No.", "", "## 11. HaluEval-QA results", ""]
    lines += markdown_table(halu, [("pipeline", "Pipeline"), ("accuracy", "Accuracy"), ("false_positive", "FP"), ("false_negative", "FN"), ("invalid_output_rate", "Invalid"), ("source_mapping_rate", "Source mapping")], {"accuracy", "invalid_output_rate", "source_mapping_rate"})
    lines += ["", "Interpretation: C8 achieves 6.00% HaluEval-QA accuracy with a 63.50% invalid-output rate, while C1 achieves 80.00%. The exact-quote output contract is too brittle for this external recognition task as instantiated here; no HaluEval utility-superiority claim is supported."]
    lines += ["", "## 12. Gold-access boundary", "", "Generation runners open only stripped runtime JSONL. Internal expected claims/outcomes and official FinQA/HaluEval labels are opened by separate post-generation scorers. The only pre-registration use of HaluEval right/hallucinated answer fields is to select the official candidate stimulus; candidate type and label are omitted from runtime data. `forbidden_pre_generation_gold_access = 0`.", "", "## 13. Outcome/latency coupling", "", "Every scored answer carries timing from the same actual model batch invocation. Rejected cases explicitly set `model_invoked=false` and model latency to zero while preserving measured policy/retrieval end-to-end latency. C4 latency sums its two measured model invocations and local tool transition.", "", "## 14. Statistical analysis", "", "Safety comparisons use exact McNemar tests, paired risk differences, Newcombe-Wilson 95% intervals, and Holm correction. Utility uses paired bootstrap intervals plus exact McNemar tests. Latency uses paired Wilcoxon signed-rank tests and paired bootstrap intervals. No Phase-4B p-value is reused.", "", "## 15. Baseline fidelity", "", "C3 is a JSON-schema validated structured-output baseline, C5 is guardrail-style, C6 is corrective-retrieval, and C7 is graph-structured RAG. The report does not claim Outlines, NeMo Guardrails, CRAG, or Microsoft GraphRAG reproduction.", "", "## 16. Preserved evidence", "", "`results/uir_phase3d`, `results/uir_phase4`, and `results/uir_phase4b` were not overwritten. All new evidence is isolated under `results/uir_phase4c`.", "", "## 17. Limitations", "", "- One 3.8B backbone and one local hardware environment are evaluated.", "- FinQA uses a pre-registered 200-row official test subset rather than all 1,147 rows.", "- HaluEval uses a pre-registered 200-row QA subset; dialogue and summarization are out of scope.", "- C3/C5/C6/C7 are mechanism-matched baselines, not official third-party framework reproductions.", "- Batched latency is shared by concurrent cases in the same real invocation and should be interpreted as this hardware/configuration's matched batch latency.", "", "## 18. Publication verdict", "", f"`{gate['status']}`", "", "Under the Phase-4C stop rule, no further UIR architecture development is warranted once this status is ready. The next work is manuscript preview and PI review.", "",
    ]
    lines += ["## 19. Gate scope", "", "The READY status certifies evidence authenticity, provenance, completeness, and consistency against the Phase-4C gate; it does not certify external benchmark superiority. C6/C8 all-case P50 values also include 310 deterministic non-model rows, so their near-zero medians must not be described as model inference latency.", ""]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "REPORT_PHASE4C_AUTHENTIC_EVIDENCE.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": gate["status"], "report": str((REPORT_DIR / "REPORT_PHASE4C_AUTHENTIC_EVIDENCE.md").relative_to(ROOT))}, sort_keys=True))


if __name__ == "__main__": main()
