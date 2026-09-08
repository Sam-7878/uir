"""Base Interface for Threat-Specific Behavioral Judges (Work Order Mandate §12)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple
from evaluation.llm_security_v3_1.schema.oracle_case import OracleCase


class BaseJudge(ABC):
    """Abstract base class for behavioral threat evaluation."""

    @abstractmethod
    def evaluate(self, record: Dict[str, Any], oracle: OracleCase) -> Tuple[bool, bool, Dict[str, Any]]:
        """Evaluate execution record against oracle ground truth.

        Returns:
            (model_compromised: bool, e2e_attack_succeeded: bool, details: Dict[str, Any])
        """
        pass
