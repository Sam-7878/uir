"""Phase UIR-4F: Automated Publication Table Generator (Final).

Reads ONLY Phase 4F final aggregate CSVs (never manual numbers) and generates:
  docs/work_reports/uir_phase4f/generated_tables_final.md
  docs/work_reports/uir_phase4f/generated_tables_final.tex

Tables:
  Table 1: Internal Safety & Security (Accepted Unsupported, Adversarial ASR N=50, FAR, Policy Bypass)
  Table 2: Internal Utility (Complete Accuracy, Supported Coverage, Safe Partial, No Answer, Precision, Recall)
  Table 3: Constrained Decoding Comparison (C3 vs D1 N=600 vs C8)
  Table 4: FinQA Cross-Model Evaluation (Raw Parse, Contract, Safe Exec, Acc, Raw vs Accepted Unsupported)
  Table 5: HaluEval Cross-Model Evaluation (Raw Semantic Acc, Contract, Accepted E2E, Raw Unsup, Accepted Unsup, Safe Rejection)
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from evaluation.uir_phase4f.common import DOCS_DIR, RESULTS_DIR, read_csv


def pct(val: Any, digits: int = 2) -> str:
    try:
        return f"{float(val)*100:.{digits}f}"
    except (ValueError, TypeError):
        return "N/A"


def ms(val: Any) -> str:
    try:
        v = float(val)
        if v >= 10000:
            return f"{v/1000:.1f}s"
        return f"{v:.1f}"
    except (ValueError, TypeError):
        return "N/A"


PIPELINE_MD = {
    "C0_DIRECT_SLM": "C0 Direct SLM",
    "C1_NAIVE_RAG": "C1 Naive RAG",
    "C2_RAG_EXISTENCE_CHECK": "C2 RAG + Entity Exist",
    "C3_JSON_SCHEMA_STRUCTURED": "C3 JSON-Schema Prompted / Post-Hoc",
    "C4_TOOL_CALLING_AGENT": "C4 Tool-Calling Agent",
    "C5_GUARDRAIL_STYLE": "C5 Guardrail Pipeline",
    "C6_CORRECTIVE_RETRIEVAL": "C6 Corrective RAG (CRAG)",
    "C7_GRAPH_STRUCTURED_RAG": "C7 GraphRAG",
    "C8_FINAL_UIR_B6": "**C8 Final UIR (Proposed)**",
    "D1_EXTERNAL_CONSTRAINED_DECODING": "D1 Grammar-Constrained Decoding",
}

PIPELINE_TEX = {
    "C0_DIRECT_SLM": "C0 Direct SLM",
    "C1_NAIVE_RAG": "C1 Naive RAG",
    "C2_RAG_EXISTENCE_CHECK": "C2 RAG + Exist",
    "C3_JSON_SCHEMA_STRUCTURED": "C3 JSON-Schema (Prompted)",
    "C4_TOOL_CALLING_AGENT": "C4 Tool Agent",
    "C5_GUARDRAIL_STYLE": "C5 Guardrail",
    "C6_CORRECTIVE_RETRIEVAL": "C6 CRAG",
    "C7_GRAPH_STRUCTURED_RAG": "C7 GraphRAG",
    "C8_FINAL_UIR_B6": r"\textbf{C8 Final UIR (Proposed)}",
    "D1_EXTERNAL_CONSTRAINED_DECODING": "D1 Constr. Decoding",
}


def generate_table1_md(security: list[dict[str, Any]], internal: list[dict[str, Any]]) -> str:
    lines = [
        "## Table 1: Internal Safety and Security ($N=600$ Total, $N_{\\text{attack}}=50$ Adversarial)\n",
        "| Pipeline | Accepted Unsupported Claims (%) ↓ | Wilson 95% CI | Adversarial ASR ($N=50$) (%) ↓ | Invalid Entity FAR (%) ↓ | Policy Bypass (%) ↓ |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    by_pipe = {r["pipeline"]: r for r in internal}
    for r in security:
        p = r["pipeline"]
        name = PIPELINE_MD.get(p, p)
        int_r = by_pipe.get(p, {})
        unsup = pct(int_r.get("accepted_unsupported_claim_rate", 0))
        w_lo = pct(int_r.get("unsupported_wilson_low", 0))
        w_hi = pct(int_r.get("unsupported_wilson_high", 0))
        asr = pct(r.get("adversarial_attack_success_rate", 0))
        far = pct(r.get("invalid_entity_far", 0))
        bypass = pct(r.get("policy_bypass_rate", 0))
        bold = "**" if "C8" in p else ""
        lines.append(f"| {name} | {bold}{unsup}{bold} | [{w_lo}, {w_hi}] | {bold}{asr}{bold} | {bold}{far}{bold} | {bold}{bypass}{bold} |")
    return "\n".join(lines) + "\n"


def generate_table2_md(internal: list[dict[str, Any]]) -> str:
    lines = [
        "## Table 2: Internal Utility ($N=418$ COMMIT-Eligible Requests)\n",
        "| Pipeline | Complete Accuracy (%) ↑ | Supported Coverage (%) ↑ | Safe Partial (%) | No Answer (%) | Conditional Precision (%) | Macro Recall (%) | Mean Latency (ms) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in internal:
        p = r["pipeline"]
        name = PIPELINE_MD.get(p, p)
        comp = pct(r.get("complete_claim_set_accuracy", 0))
        supp = pct(r.get("supported_answer_coverage", 0))
        part = pct(r.get("safe_partial_answer_rate", 0))
        noans = pct(r.get("no_verified_answer_rate", 0))
        prec = pct(r.get("conditional_claim_precision", 0))
        rec = pct(r.get("macro_claim_recall", 0))
        lat = r.get("mean_latency_ms", "N/A")
        bold = "**" if "C8" in p else ""
        lines.append(f"| {name} | {bold}{comp}{bold} | {bold}{supp}{bold} | {part} | {noans} | {prec} | {rec} | {bold}{lat}{bold} |")
    return "\n".join(lines) + "\n"


def generate_table3_md(constrained: list[dict[str, Any]]) -> str:
    lines = [
        "## Table 3: Grammar-Constrained Decoding Comparison (C3 vs D1 $N=600$ vs C8)\n",
        "| Baseline | Enforcement Mechanism | Schema Validity (%) | Raw Unsup. Gen. (%) ↓ | Accepted Unsup. (%) ↓ | Complete Accuracy (%) ↑ | Supported Coverage (%) ↑ | Mean Lat. (ms) |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in constrained:
        b = r.get("baseline", "")
        label = PIPELINE_MD.get(b, r.get("label", b))
        mech = r.get("enforcement_mechanism", "")
        schema = pct(r.get("schema_validity_rate", 0))
        raw_u = pct(r.get("raw_unsupported_generation_rate", 0))
        acc_u = pct(r.get("accepted_unsupported_claim_rate", 0))
        comp = pct(r.get("complete_claim_set_accuracy", 0))
        supp = pct(r.get("supported_answer_coverage", 0))
        lat = r.get("mean_latency_ms", "N/A")
        bold = "**" if "C8" in b else ""
        lines.append(f"| {label} | {mech} | {bold}{schema}{bold} | {raw_u} | {bold}{acc_u}{bold} | {bold}{comp}{bold} | {bold}{supp}{bold} | {lat} |")
    return "\n".join(lines) + "\n"


def generate_table4_md(finqa: list[dict[str, Any]]) -> str:
    lines = [
        "## Table 4: FinQA Cross-Model Evaluation (Genuine $N=200$ Each)\n",
        "| Model | Pipeline | $N$ | Raw Parse (%) | Contract Valid (%) | Safe Exec (%) | Official Accuracy (%) ↑ | Raw Unsup. Gen. (%) ↓ | Accepted Unsup. (%) ↓ | P50 Lat. |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in finqa:
        model_name = "Phi-3.5-mini" if "Phi" in r.get("model", "") else "Qwen2.5-7B"
        pipe = PIPELINE_MD.get(r.get("pipeline", ""), r.get("pipeline", ""))
        n = r.get("test_cases", 200)
        parse = pct(r.get("raw_expression_parse_rate", 0))
        contract = pct(r.get("contract_validity_rate", 0))
        safe = pct(r.get("safe_execution_rate", 0))
        acc = pct(r.get("official_execution_accuracy", 0))
        raw_u = pct(r.get("raw_unsupported_generation_rate", 0))
        acc_u = pct(r.get("accepted_unsupported_claim_rate", 0))
        lat = ms(r.get("p50_latency_ms", 0))
        bold = "**" if "C8" in r.get("pipeline", "") else ""
        lines.append(f"| {model_name} | {pipe} | {n} | {parse} | {contract} | {safe} | {bold}{acc}{bold} | {raw_u} | {bold}{acc_u}{bold} | {lat} |")
    return "\n".join(lines) + "\n"


def generate_table5_md(halu: list[dict[str, Any]]) -> str:
    lines = [
        "## Table 5: HaluEval Cross-Model Evaluation (Genuine $N=200$ Each)\n",
        "| Model | Pipeline | $N$ | Raw Semantic Acc. (%) | Contract Valid (%) | Accepted E2E Acc. (%) ↑ | Raw Unsup. Gen. (%) ↓ | Accepted Unsup. (%) ↓ | Safe Rejection (%) | P50 Lat. |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in halu:
        model_name = "Phi-3.5-mini" if "Phi" in r.get("model", "") else "Qwen2.5-7B"
        pipe = PIPELINE_MD.get(r.get("pipeline", ""), r.get("pipeline", ""))
        n = r.get("test_cases", 200)
        sem = pct(r.get("raw_semantic_accuracy", 0))
        contract = pct(r.get("contract_validity_rate", 0))
        e2e = pct(r.get("accepted_e2e_accuracy", 0))
        raw_u = pct(r.get("raw_unsupported_generation_rate", 0))
        acc_u = pct(r.get("accepted_unsupported_claim_rate", 0))
        rej = pct(r.get("safe_rejection_rate", 0))
        lat = ms(r.get("p50_latency_ms", 0))
        bold = "**" if "C8" in r.get("pipeline", "") else ""
        lines.append(f"| {model_name} | {pipe} | {n} | {sem} | {contract} | {bold}{e2e}{bold} | {raw_u} | {bold}{acc_u}{bold} | {rej} | {lat} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    print("[4F] Generating final publication tables...")
    internal = read_csv(RESULTS_DIR / "internal_final.csv")
    security = read_csv(RESULTS_DIR / "security_final.csv")
    constrained = read_csv(RESULTS_DIR / "constrained_baseline_final.csv")
    finqa = read_csv(RESULTS_DIR / "finqa_external_final.csv")
    halu = read_csv(RESULTS_DIR / "halueval_external_final.csv")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    md_out = DOCS_DIR / "generated_tables_final.md"
    tex_out = DOCS_DIR / "generated_tables_final.tex"

    # Assemble Markdown
    md_content = [
        "# Phase UIR-4F Final Generated Publication Tables\n",
        "_Auto-generated from frozen Phase 4F aggregate CSVs. Manual editing strictly prohibited._\n",
        "---\n",
        generate_table1_md(security, internal),
        "---\n",
        generate_table2_md(internal),
        "---\n",
        generate_table3_md(constrained) if constrained else "## Table 3\n_Pending D1 completion._\n",
        "---\n",
        generate_table4_md(finqa),
        "---\n",
        generate_table5_md(halu),
    ]
    md_out.write_text("\n".join(md_content), encoding="utf-8")
    print(f"[4F] Written Markdown tables: {md_out}")

    # Assemble LaTeX tables
    tex_content = r"""% Phase UIR-4F Final Generated Publication Tables (LaTeX)
% Auto-generated from Phase 4F aggregate CSVs.

\begin{table}[t]
\caption{Internal Safety and Security ($N=600$ Total, $N_{\text{attack}}=50$ Adversarial)}
\label{tab:phase4f_safety}
\centering
\scalebox{0.82}{
\begin{tabular}{lcccc}
\toprule
\textbf{Pipeline} & \textbf{Accepted Unsup. (\%)} $\downarrow$ & \textbf{Adv. ASR ($N=50$)} $\downarrow$ & \textbf{Entity FAR (\%)} $\downarrow$ & \textbf{Policy Bypass (\%)} $\downarrow$ \\
\midrule
"""
    by_pipe = {r["pipeline"]: r for r in internal}
    for r in security:
        p = r["pipeline"]
        name = PIPELINE_TEX.get(p, p)
        int_r = by_pipe.get(p, {})
        unsup = pct(int_r.get("accepted_unsupported_claim_rate", 0))
        asr = pct(r.get("adversarial_attack_success_rate", 0))
        far = pct(r.get("invalid_entity_far", 0))
        bypass = pct(r.get("policy_bypass_rate", 0))
        tex_content += f"{name} & {unsup} & {asr} & {far} & {bypass} \\\\\n"
    tex_content += r"""\bottomrule
\end{tabular}
}
\end{table}

\begin{table}[t]
\caption{Internal Utility ($N=418$ COMMIT-Eligible Requests)}
\label{tab:phase4f_utility}
\centering
\scalebox{0.80}{
\begin{tabular}{lcccccc}
\toprule
\textbf{Pipeline} & \textbf{Complete Acc. (\%)} $\uparrow$ & \textbf{Supported Cov. (\%)} $\uparrow$ & \textbf{Safe Partial (\%)} & \textbf{No Ans. (\%)} & \textbf{Prec. (\%)} & \textbf{Recall (\%)} \\
\midrule
"""
    for r in internal:
        p = r["pipeline"]
        name = PIPELINE_TEX.get(p, p)
        comp = pct(r.get("complete_claim_set_accuracy", 0))
        supp = pct(r.get("supported_answer_coverage", 0))
        part = pct(r.get("safe_partial_answer_rate", 0))
        noans = pct(r.get("no_verified_answer_rate", 0))
        prec = pct(r.get("conditional_claim_precision", 0))
        rec = pct(r.get("macro_claim_recall", 0))
        tex_content += f"{name} & {comp} & {supp} & {part} & {noans} & {prec} & {rec} \\\\\n"
    tex_content += r"""\bottomrule
\end{tabular}
}
\end{table}
"""
    tex_out.write_text(tex_content, encoding="utf-8")
    print(f"[4F] Written LaTeX tables: {tex_out}")


if __name__ == "__main__":
    main()
