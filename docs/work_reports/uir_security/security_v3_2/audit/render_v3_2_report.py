#!/usr/bin/env python3
"""Synchronize the final report from the authoritative closure documentation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
RESULTS = REPO / "results/llm_security_v3_2_closure"
SOURCE = RESULTS / "documentation/HETE_UIR_V3_2_FINAL_SCIENTIFIC_VALIDITY_REPORT.md"
TARGET = REPO / "docs/security_v3_2/HETE_UIR_V3_2_FINAL_SCIENTIFIC_VALIDITY_REPORT.md"


def main() -> int:
    baseline = json.loads((RESULTS / "baseline_comparison.json").read_text())
    models = json.loads((RESULTS / "multi_model_results.json").read_text())
    ablations = json.loads((RESULTS / "ablation_results.json").read_text())
    adaptive = json.loads((RESULTS / "adaptive_attack_results.json").read_text())
    text = SOURCE.read_text(encoding="utf-8")
    required = (
        f"| HETE | {baseline['HETE']['mcr']['count']}/{baseline['HETE']['mcr']['denominator']}",
        f"| qwen2.5:7b | {models['qwen2.5:7b']['attack_cases']} | {models['qwen2.5:7b']['benign_cases']}",
        f"| phi3.5:latest | {models['phi3.5:latest']['attack_cases']} | {models['phi3.5:latest']['benign_cases']}",
        f"| no_input_guard | {ablations['no_input_guard']['attack_cases']}",
        f"Adaptive execution: {sum(v['seeds'] for v in adaptive.values())} seeds; {sum(v['queries'] for v in adaptive.values())} actual queries.",
        "human_validation=false",
        "Actual AgentDojo was not imported or executed.",
    )
    missing = [claim for claim in required if claim not in text]
    if missing:
        raise ValueError(f"authoritative report does not match frozen JSON: {missing}")
    shutil.copyfile(SOURCE, TARGET)
    print(f"synchronized {TARGET.relative_to(REPO)} from authoritative closure documentation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
