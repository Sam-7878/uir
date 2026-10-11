"""Holistic Security and Benign Utility Evaluator for HETE V3.2."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from .base_judge import BaseJudge
from .benign_utility_oracle_v3_2 import BenignUtilityOracleV32
from .direct_jailbreak_judge import DirectJailbreakJudge
from .excessive_agency_judge import ExcessiveAgencyJudge
from .indirect_injection_judge import IndirectInjectionJudge
from .nonexistent_entity_judge import NonexistentEntityJudge
from .poisoning_judge import PoisoningJudge
from .resource_exhaustion_judge import ResourceExhaustionJudge
from .sensitive_exfiltration_judge import SensitiveExfiltrationJudge
from ..schema.oracle_case import OracleCase


class SecurityEvaluatorV32:
    """Evaluates full test records against ground-truth OracleCases."""

    def __init__(self):
        self.benign_oracle = BenignUtilityOracleV32()
        self.judges: Dict[str, BaseJudge] = {
            "direct_system_prompt_extraction": DirectJailbreakJudge(),
            "direct_prompt_injection": DirectJailbreakJudge(),
            "indirect_prompt_injection": IndirectInjectionJudge(),
            "jailbreak_policy_override": DirectJailbreakJudge(),
            "indirect_instruction_injection": IndirectInjectionJudge(),
            "poisoned_retrieval_evidence": PoisoningJudge(),
            "sensitive_data_exfiltration": SensitiveExfiltrationJudge(),
            "excessive_agency_tool_escalation": ExcessiveAgencyJudge(),
            "nonexistent_entity": NonexistentEntityJudge(),
            "gaslighting_false_premise": DirectJailbreakJudge(),
            "context_firewall_cross_tenant": DirectJailbreakJudge(),
            "resource_exhaustion": ResourceExhaustionJudge(),
        }

    def evaluate_case(self, record: Dict[str, Any], oracle: OracleCase) -> Dict[str, Any]:
        """Evaluates a single execution record."""
        if not oracle.is_attack:
            score = self.benign_oracle.evaluate(record, oracle)
            return {
                "case_id": oracle.case_id,
                "is_attack": False,
                "attack_class": "valid_benign",
                "benign_success": score.complete_task_success,
                "complete_task_success": score.complete_task_success,
                "safe_partial_success": score.safe_partial_success,
                "contract_validity": score.contract_validity,
                "entity_match": score.entity_match,
                "numeric_match": score.numeric_match,
                "citation_accuracy": score.citation_accuracy,
                "false_rejection": score.false_rejection,
                "model_compromised": False,
                "e2e_attack_succeeded": False,
                "details": {
                    "extracted_entity": score.extracted_entity,
                    "extracted_values": score.extracted_values,
                    "rejection_reason": score.rejection_reason,
                },
            }

        judge = self.judges.get(oracle.attack_class, DirectJailbreakJudge())
        mcr, e2e, details = judge.evaluate(record, oracle)

        return {
            "case_id": oracle.case_id,
            "is_attack": True,
            "attack_class": oracle.attack_class,
            "benign_success": False,
            "model_compromised": mcr,
            "e2e_attack_succeeded": e2e,
            "details": details,
        }
