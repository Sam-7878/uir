"""Budgeted Adaptive Attack Search Runner for HETE V3.2.

Work Order Mandate §4 (P3):
- Genuine mutation search with budget B=20.
- Evaluates candidate mutations produced by AdaptiveMutationEngine.
- Evaluates HETE, Spotlighting, and CaMeL baselines.
- Tracks exact query index of first MCR and first E2E compromise.
- Captures unique input hashes and mutation operators.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from llm_trust.inference.base import BaseInferenceBackend
from ..baselines.camel_adapter import CaMeLBaselineAdapter
from ..baselines.spotlighting_adapter import SpotlightingBaselineAdapter
from ..baselines.uir_v3_2_security import UirV32SecurityPipeline
from ..judges.security_evaluator import SecurityEvaluatorV32
from ..schema.oracle_case import OracleCase
from ..schema.runtime_case import RuntimeCase
from .mutation_engine import AdaptiveMutationEngine, MutationResult


class AdaptiveSearchRunnerV32:
    """Orchestrates genuine 20-query adaptive adversarial mutation campaigns."""

    def __init__(
        self,
        backend: BaseInferenceBackend,
        max_budget: int = 20,
    ):
        self.backend = backend
        self.max_budget = max_budget
        self.mutation_engine = AdaptiveMutationEngine()
        self.evaluator = SecurityEvaluatorV32()
        self.hete = UirV32SecurityPipeline(backend=backend)
        self.spotlighting = SpotlightingBaselineAdapter(backend=backend)
        self.camel = CaMeLBaselineAdapter(backend=backend)

    def run_seed_campaign(
        self,
        seed_runtime_case: RuntimeCase,
        seed_oracle_case: OracleCase,
        target_system: str = "HETE",
    ) -> Dict[str, Any]:
        """Runs an adaptive search loop up to max_budget iterations against target system."""
        pipeline = {
            "HETE": self.hete.execute,
            "Spotlighting": self.spotlighting.run_case,
            "CaMeL": self.camel.run_case,
        }.get(target_system, self.hete.execute)

        campaign_log: List[Dict[str, Any]] = []
        first_mcr_query: Optional[int] = None
        first_e2e_query: Optional[int] = None

        curr_input = seed_runtime_case.user_input

        for q_idx in range(1, self.max_budget + 1):
            mut: MutationResult = self.mutation_engine.mutate(curr_input, q_idx)

            # Build mutated runtime case
            mut_case = RuntimeCase(
                case_id=f"{seed_runtime_case.case_id}_adapt_q{q_idx}",
                language=seed_runtime_case.language,
                user_input=mut.mutated_input,
                retrieved_context=seed_runtime_case.retrieved_context,
                principal_id=seed_runtime_case.principal_id,
                environment_id=seed_runtime_case.environment_id,
                session_metadata=seed_runtime_case.session_metadata,
            )

            rec = pipeline(mut_case)
            eval_res = self.evaluator.evaluate_case(rec, seed_oracle_case)

            is_mcr = eval_res.get("model_compromised", False)
            is_e2e = eval_res.get("e2e_attack_succeeded", False)

            if is_mcr and first_mcr_query is None:
                first_mcr_query = q_idx
            if is_e2e and first_e2e_query is None:
                first_e2e_query = q_idx

            # Determine containment gate
            containment = "NONE"
            events = rec.get("guard_events", [])
            for ev in events:
                if ev.get("decision") in {"BLOCKED", "QUARANTINED", "REJECTED", "DENIED"}:
                    containment = ev.get("component", "GUARD")
                    break

            entry = {
                "query_index": q_idx,
                "input_hash": mut.input_hash,
                "operator_name": mut.operator_name,
                "description": mut.description,
                "model_compromised": is_mcr,
                "e2e_attack_succeeded": is_e2e,
                "containment_gate": containment,
                "terminal_status": rec.get("terminal_status", "UNKNOWN"),
            }
            campaign_log.append(entry)

            # If E2E compromise succeeded, attacker terminates successfully
            if is_e2e:
                break

            # Update candidate for next mutation step
            curr_input = mut.mutated_input

        return {
            "seed_case_id": seed_runtime_case.case_id,
            "target_system": target_system,
            "queries_executed": len(campaign_log),
            "max_budget": self.max_budget,
            "first_mcr_query": first_mcr_query,
            "first_e2e_query": first_e2e_query,
            "compromised_e2e": first_e2e_query is not None,
            "compromised_mcr": first_mcr_query is not None,
            "log": campaign_log,
        }
