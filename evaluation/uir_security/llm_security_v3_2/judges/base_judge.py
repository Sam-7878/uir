"""Base behavioral judge interface for HETE V3.2."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from ..schema.oracle_case import OracleCase


class BaseJudge(ABC):
    @abstractmethod
    def evaluate(self, record: Dict[str, Any], oracle: OracleCase) -> Tuple[bool, bool, Dict[str, Any]]:
        """Evaluates execution record against oracle ground truth.

        Returns:
            Tuple of (model_compromised_mcr, e2e_attack_succeeded, details_dict)
        """
        pass
