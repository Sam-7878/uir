#!/usr/bin/env python3
"""Compatibility entry point for Phase-2 statistical procedures."""
from paired_statistics import mcnemar_exact, paired_bootstrap_delta, percentile

__all__ = ["mcnemar_exact", "paired_bootstrap_delta", "percentile"]
