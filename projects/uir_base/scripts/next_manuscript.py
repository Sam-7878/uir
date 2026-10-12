"""Generate a source-linked provisional research draft, never author approval."""
import argparse
import json
from pathlib import Path
import re
from projects.uir_base.scripts import revision_audit as a
from projects.uir_base.scripts.next_release import DEFAULT, csv_rows


def escape(value):
    return str(value).replace("\\", "\\textbackslash{}").replace("_", "\\_").replace("%", "\\%").replace("&", "\\&").replace("#", "\\#")


def build(destination):
    if destination.exists():
        raise FileExistsError("Use a fresh draft version; original manuscript is immutable")
    historical = DEFAULT / "historical_reanalysis"
    paths = [DEFAULT / "release_manifest.json", historical / "internal_utility_recomputed.csv", historical / "halueval_recomputed.csv",
             DEFAULT / "fresh_matched/matched_summary.csv", DEFAULT / "fresh_matched_offline_replay/verification.json",
             DEFAULT / "benchmark_adapter/adapter_verification.json", DEFAULT / "ai_review_v2/calibration_accuracy.csv",
             DEFAULT / "ai_review_v2/holdout_accuracy.csv", DEFAULT / "finqa_holdout_v2/summary.csv",
             DEFAULT / "finqa_holdout_v2/posthoc_diagnostic_summary.json"]
    if any(not p.is_file() for p in paths):
        raise FileNotFoundError("Required completed result missing; do not render invented or pending metrics")
    source = {str(p.relative_to(a.ROOT)): a.digest(p) for p in paths}
    destination.mkdir(parents=True)
    a.write_json(destination / "draft_result_manifest.json", {"source_sha256": source, "status": "PROVISIONAL_NOT_MANUSCRIPT_READY",
        "claim_scope": "restricted CNL/policy conformance + reproducible output evaluation", "author_confirmations": "PENDING",
        "target": "Electronics / Generative AI, Large Language Models and Their Applications",
        "original_W08": "NOT_SATISFIED", "human_validation": False, "generator_sha256": a.digest(__file__)})
    table = []
    for row in csv_rows(historical / "internal_utility_recomputed.csv"):
        name = row["pipeline"].split("_")[0]
        table.append(f"{escape(name)} & {row['full']}/{row['N_eligible']} & {row['partial']}/{row['N_eligible']} & {int(row['full'])+int(row['partial'])}/{row['N_eligible']} & {row['unsupported_accepted_cases']}/{row['N_all']}" + r" \\")
    halu = [f"{escape(r['model'])} {r['pipeline']} & {r['n_raw_correct']}/{r['N']} & {r['n_contract_valid']}/{r['N']} & {r['n_e2e_correct']}/{r['N']}" + r" \\" for r in csv_rows(historical / "halueval_recomputed.csv")]
    fresh = [f"{escape(r['pipeline'].replace('DETERMINISTIC_TRUSTED_FIXTURE','Template').replace('SLM_',''))} & {r['full']}/{r['N_eligible']} & {r['unsupported_accepted_cases']}/{r['N_all']}" + r" \\" for r in csv_rows(DEFAULT / "fresh_matched/matched_summary.csv")]
    external = [f"{escape(r['model'])} {r['condition'].split('_')[0]} & {r['N_correct']}/{r['N']} & {r['N_finished']}/{r['N']} & {r['N_missing']}/{r['N']}" + r" \\" for r in csv_rows(DEFAULT / "finqa_holdout_v2/summary.csv")]
    tables = {"internal": "\n".join(table), "halueval": "\n".join(halu), "fresh": "\n".join(fresh), "external": "\n".join(external)}
    a.write_json(destination / "generated_table_inputs.json", tables)
    abstract = ("Probabilistic generation and executable authority require different validation criteria. We study a typed policy-and-evidence contract shared by restricted Korean and English frontends, separating model candidates from authorized structured output. The study is AI-only: constructed benchmarks, trusted-slot historical execution and supplementary model review do not establish human semantic accuracy. A raw-capture reanalysis distinguishes exact claim support, answer completeness, format validity, missing task labels and unassessed prose. A trusted-slot deterministic control outperforms the historical generative pipeline in complete answers while matching supported-answer coverage. A local GPU output-layer experiment exposes a five-required-field syntax constraint versus seven-field exact validation mismatch; its negative results are not attributed to general model ability. A prospective FinQA experiment compares Phi-3.5 and Qwen3-1.7B with separately frozen non-thinking decoding and explicit program execution. Restricted-language and in-memory policy-action conformance, source-family-aware historical uncertainty and independently replayable evidence support a bounded systems contribution. They do not establish universal factual truth, superior model reasoning, host-compromise resistance or general natural-language understanding. The draft retains negative findings and unresolved scientific and author-confirmation gates.")
    (destination / "abstract_wordcount.txt").write_text(str(len(abstract.split())) + "\n")
    text = r"""\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage[margin=25mm]{geometry}
\usepackage{amsmath,booktabs,longtable}
\usepackage[hidelinks]{hyperref}
\title{Typed Policy-and-Evidence Contracts for Local Language-Model Workflows: A Bounded Systems Evaluation}
\author{Author confirmation pending}
\date{Provisional research draft, not for submission}
\begin{document}
\maketitle
\noindent\textbf{Status: BLOCKED, not manuscript-ready.} Original paper source is preserved.
This is a separate research draft, not a completed MDPI template conversion.
\begin{abstract}
ABSTRACT
\end{abstract}
\paragraph{Keywords} typed execution contract; evidence binding; controlled natural language; local inference; reproducible evaluation.
\section{Introduction}
Language-model generation is not an authorization boundary. A well-formed output may use an incorrect entity, period, unit or provenance. Controlled languages, declarative policy and structured decoding already address parts of this problem. AgentSpec supplies customizable action enforcement and CaMeL separates trusted control from untrusted data. We investigate a narrower composition: shared typed request semantics, policy/evidence snapshot identity, deterministic claim binding and explicit answer states. ``Universal'' refers only to supported frontend sharing; it does not denote free-language understanding or domain-independent truth.
\section{Methods and study scope}
The study follows an explicitly approved AI-only amendment. Original W08, requiring actual independent human evaluation, remains NOT\_SATISFIED. Constructed fixtures are not human semantic gold. Historical trusted-slot execution, raw-only restricted CNL conformance, counterfactual replay, fresh GGUF inference and synthetic AI review are separate evidence kinds. C5--C7 are mechanism-matched implementations, not official external framework reproductions.

A contract binds entity, attribute, period, policy snapshot and evidence snapshot. Raw-only parsing accepts a declared bilingual CNL with explicit NOT/AND/OR precedence and Boolean/decimal operands. Unsupported text yields clarification, never silently dropped conditions. A digest covers canonical NFC-normalized RFC8785 bytes; audit metadata and language do not enter semantic identity. User predicates are distinct from default system provenance constraints. Under trusted authority inputs, stale snapshots quarantine, denied actions do not execute, approval is rechecked, and read-only does not authorize writes.

For required evaluator claim set $R$, runtime catalogue $K$ and accepted emitted set $E$, structured unsupported claims are $E\setminus K$; complete answers require $E=R$, policy admissibility and nonempty $R$. This is registry-relative support, not independently established objective fact truth. Native prose is separately unassessed. Evaluation gold is excluded from runtime payloads, with an explicit CPython file-open boundary test; this is not an OS sandbox proof against inherited descriptors or native code.

Historical utility has 418 eligible cases among 600 requests. Source-row hashes are not independent families. Hash-matched original lineage, documented language pairs, templates and source-document evidence yield 238 recorded eligible families. Paired cluster bootstrap retains all rows within each sampled family. Existing 18 exact McNemar tests retain their Holm family and case-independence limitation. Historical batch-shared latency is not request-level tail latency. Fresh sequential logs separate load-inclusive first requests, warm calls, rejection and measured CPU stages, each with one repetition.
\section{Results}
\subsection{Historical structured-claim reanalysis}
\begin{center}\begin{tabular}{lrrrr}\toprule
Condition & Complete & Partial & Coverage & Unsupported\\\midrule
INTERNAL_TABLE
\bottomrule\end{tabular}\end{center}
The last column is unsupported structured-claim cases among all requests, not whole-output hallucination. The trusted-slot deterministic control completes 272/418 versus C8's 224/418 complete plus 48 partial; both cover 272. There are 48 deterministic-only complete cases and no C8-only complete cases. This does not support a necessary SLM renderer. All original C5 candidate records are linked; its counterfactual projection is not fresh inference or a zero-generation-cost model.

D1 changes from the legacy scorer's 206 complete and 125 unsupported cases to 74 complete and 326 unsupported cases under seven-field exact support. The source responses are unchanged. Schema validity alone cannot establish those exact bindings. Historical literal task labels, missing labels, contract validity and accepted correctness are independently replayed:
\begin{center}\begin{tabular}{lrrr}\toprule
HaluEval model/condition & Literal correct & Contract valid & End-to-end correct\\\midrule
HALU_TABLE
\bottomrule\end{tabular}\end{center}
\subsection{New local output-layer development condition}
\begin{center}\begin{tabular}{lrr}\toprule
Condition & Complete & Unsupported\\\midrule
FRESH_TABLE
\bottomrule\end{tabular}\end{center}
Phi's Q4\_0 artifact made 272 actual calls among 600 requests: 251 stopped and 21 exhausted the fixed generation limit. The inherited syntax schema requires five fields but the scorer binds seven. Period omission occurs in 249 candidate cases and unit omission in 118 (nonexclusive). The loss and abstention must therefore not be generalized to model capability or interpreted as an unbiased causal contribution estimate. Exact-key projection rejects unsupported candidates rather than establishing usefulness.
\subsection{Prospective external task evaluation}
\begin{center}\begin{tabular}{lrrr}\toprule
Model/condition & End-to-end correct & Finished & Adapter MISSING state\\\midrule
EXTERNAL_TABLE
\bottomrule\end{tabular}\end{center}
The new generator comparison is Phi-3.5 (approximately 3.8B, Q4\_0) versus user-selected Qwen3-1.7B (Q4\_K\_M), non-thinking with equal visible generation limits. It is not parameter-, tokenizer- or quantization-matched, or a replacement for historical Qwen2.5-7B evidence. All 200 indices per condition are disjoint from historical development, but 71 documents and 180 companies overlap. The custom source-number program contract is not the official evaluator: seven executable-intersection parity fixtures agree, while unsupported operations and intentional rejection are disclosed. 172/200 gold programs are executable with the full source; this evaluation-only expressibility is not runtime retrieval coverage. Unsupported claim rates are NOT\_MEASURED for these task-answer conditions.

These are strict adapter-defined task endpoints, not isolated reasoning accuracy. Post-hoc diagnostics identify DIAGNOSTIC_MARKERS requests with an answer marker somewhere in the response but no value extracted by the frozen end-anchored parser. Trailing prose and percentage-versus-benchmark-unit ambiguity confound model attribution. JSON program strings do not themselves enforce arithmetic DSL syntax: most rejected candidates describe a calculation in prose. No primary score is changed by this diagnostic; future adapter improvement requires development data and a new prospective protocol with unused holdout data.
\subsection{Supplementary conformance and policy effects}
New AI review uses 16 synthetic calibration and 16 lexical-shift holdout cases, each independently requested from two model families. All 64 responses are schema-valid but all cases remain unresolved on at least one dimension; agreement is not accuracy or human validation. Missing candidates, request ambiguity, reviewer epistemic uncertainty and evidence availability are distinct labels. No two-model majority adjudicates ties.

Ten in-memory action opportunities per tool-capable condition include six prohibited and four allowed actions. Enforcement executes none of the prohibited actions and falsely denies none of the allowed ones; the unguarded control executes six prohibited actions, while refuse-only denies four allowed actions. No-tools has zero execution opportunities and is not evidence of attack blocking. These are synthetic finite-policy effects, not a deployed-agent prompt-injection success rate. Five hundred legacy mutations and 1,500 gate classifications are reconstructed from seeded source, not recovered original raw mutation captures or generated-output robustness tests.
\section{Discussion and limitations}
The observations favor deterministic rendering where trusted slots already supply the answer. A typed contract may aid inspectable authority and failure handling, but an input/representation-layer causal comparison remains incomplete. Neither zero-event structured support nor synthetic action conformance proves unassessed prose factuality, correct underlying registries, or security under host/registry compromise. Recorded families cannot cover unknown dependencies. The new external tasks measure answer correctness and bounded program execution, not universal hallucination elimination. Poor supplementary reviewer calibration is retained rather than tuned away. The manuscript and submission gates remain blocked pending remaining comparisons, complete release/PDF review, journal-template checks and actual author/institution declarations.
\section{Conclusions}
A bounded executable policy/evidence interface can separate candidate text from granted authority. Reproducible evidence and honest rejection states are the supported systems result; universal semantics, superior generative utility and independent human truth validation are not established.
\section*{Declarations pending actual confirmation}
Authorship, contributions, funding, conflicts, ethics/IRB applicability, AI-use disclosure, availability rights and publication access identifiers remain PENDING\_AUTHOR\_CONFIRMATION. No default ``Not applicable'' declaration is inserted. Code and raw-evidence archives are local verification candidates, not a claimed public deposit. Original papers and model weights are excluded from the code/evidence archive.
\begin{thebibliography}{9}
\bibitem{camel} E. Debenedetti et al., Defeating Prompt Injections by Design, arXiv:2503.18813v2, 2025. \url{https://arxiv.org/abs/2503.18813v2}.
\bibitem{agentspec} H. Wang, C. M. Poskitt, and J. Sun, AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents, ICSE 2026. DOI: 10.1145/3744916.3764546.
\bibitem{cnl} T. Kuhn, A Survey and Classification of Controlled Natural Languages, Computational Linguistics 40(1), 121--170, 2014. DOI: 10.1162/COLI\_a\_00168.
\bibitem{xgrammar} Y. Dong et al., XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models, arXiv:2411.15100, 2024.
\bibitem{chopchop} S. Nagy et al., ChopChop: A Programmable Framework for Semantically Constraining the Output of Language Models, PACMPL 10, POPL, article 66, 2026. DOI: 10.1145/3776708.
\end{thebibliography}
\end{document}
"""
    diagnostics = json.loads((DEFAULT / "finqa_holdout_v2/posthoc_diagnostic_summary.json").read_text())
    for key, value in {"ABSTRACT": abstract, "INTERNAL_TABLE": tables["internal"], "HALU_TABLE": tables["halueval"], "FRESH_TABLE": tables["fresh"], "EXTERNAL_TABLE": tables["external"], "DIAGNOSTIC_MARKERS": str(diagnostics["marker_present_but_adapter_missing"])}.items():
        text = text.replace(key, value)
    (destination / "research_draft.tex").write_text(text, encoding="utf-8")
    (destination / "numeric_consistency_report.md").write_text("# Numeric linkage\n\nAll four result tables generated from hashed CSV sources in draft_result_manifest.json.\nNo submission-ready status is inferred. Narrative canonical counts still require independent PDF/source review.\n")
    print(destination / "research_draft.tex")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    build(parser.parse_args().out)
