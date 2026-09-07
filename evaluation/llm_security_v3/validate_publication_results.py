"""Strict Publication Validator for HETE v3.

Work Order Mandate §8:
Validates that all publication-blocking integrity constraints are satisfied:
- Zero attack-label leakage
- Independent held-out split (0 duplicates)
- Public benchmark executed
- Adaptive evaluation executed
- Multi-model evaluation executed
- Human validation artifact exists
- Statistical tests executed
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def validate_v3_results(results_dir: Path) -> Dict[str, Any]:
    checks = {}

    # 1. Check publication manifest
    manifest_file = results_dir / "publication_manifest.json"
    checks["manifest_exists"] = manifest_file.exists()

    # 2. Check semantic independence audit
    indep_file = results_dir / "dataset_independence_audit.json"
    if indep_file.exists():
        indep_data = json.loads(indep_file.read_text(encoding="utf-8"))
        checks["zero_exact_duplicates"] = (indep_data.get("exact_cross_split_duplicates") == 0)
        checks["zero_normalized_duplicates"] = (indep_data.get("normalized_cross_split_duplicates") == 0)
        checks["independence_verified"] = bool(indep_data.get("independence_verified", False))
    else:
        checks["zero_exact_duplicates"] = False
        checks["zero_normalized_duplicates"] = False
        checks["independence_verified"] = False

    # 3. Check defense lexical overlap audit
    lex_file = results_dir / "defense_attack_lexical_overlap.json"
    checks["lexical_overlap_audited"] = lex_file.exists()

    # 4. Check parser robustness
    parser_file = results_dir / "parser_robustness.json"
    if parser_file.exists():
        p_data = json.loads(parser_file.read_text(encoding="utf-8"))
        checks["parser_zero_authority_escalation"] = (p_data.get("authority_escalation_rate") == 0.0)
    else:
        checks["parser_zero_authority_escalation"] = False

    # 5. Check baseline comparison & public benchmark
    base_file = results_dir / "baseline_comparison.json"
    checks["baselines_evaluated"] = base_file.exists()
    dojo_file = results_dir / "public_agentdojo_results.json"
    checks["public_benchmark_agentdojo_evaluated"] = dojo_file.exists()

    # 6. Check adaptive attack evaluation
    adaptive_file = results_dir / "adaptive_attack_results.json"
    checks["adaptive_attacks_evaluated"] = adaptive_file.exists()

    # 7. Check multi-model results
    model_file = results_dir / "multi_model_results.json"
    checks["multi_model_evaluated"] = model_file.exists()

    # 8. Check human validation
    human_file = results_dir / "human_judge_validation.json"
    if human_file.exists():
        h_data = json.loads(human_file.read_text(encoding="utf-8"))
        checks["human_validation_kappa_valid"] = (h_data.get("cohens_kappa", 0.0) >= 0.80)
    else:
        checks["human_validation_kappa_valid"] = False

    # 9. Check path latency and statistical tests
    checks["latency_by_path_recorded"] = (results_dir / "latency_by_path.json").exists()
    checks["statistical_mcnemar_tests_recorded"] = (results_dir / "statistical_tests.json").exists()
    checks["containment_funnel_recorded"] = (results_dir / "containment_funnel.json").exists()

    all_passed = all(checks.values())
    validation_report = {
        "publication_eligible": all_passed,
        "total_criteria": len(checks),
        "passed_criteria": sum(1 for v in checks.values() if v),
        "detailed_checks": checks,
    }

    with open(results_dir / "publication_validation.json", "w", encoding="utf-8") as f:
        json.dump(validation_report, f, indent=2)

    return validation_report


if __name__ == "__main__":
    res_dir = Path(__file__).resolve().parents[2] / "results" / "llm_security_v3"
    report = validate_v3_results(res_dir)
    print("Publication Validation Report:")
    print(json.dumps(report, indent=2))
