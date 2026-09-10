#!/usr/bin/env python3
"""Dependency-free metrics used by the deterministic UIR evaluation."""
from __future__ import annotations

import math
import statistics
from collections.abc import Iterable


def rate(successes: int, total: int) -> float:
    return successes / total if total else 0.0


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    observed = successes / total
    denominator = 1.0 + z * z / total
    centre = (observed + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(observed * (1 - observed) / total + z * z / (4 * total * total)) / denominator
    low = 0.0 if successes == 0 else max(0.0, centre - margin)
    high = 1.0 if successes == total else min(1.0, centre + margin)
    return low, high


def percentile(values: Iterable[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def describe(values: Iterable[float]) -> dict[str, float]:
    data = list(values)
    return {
        "count": len(data), "mean": statistics.fmean(data) if data else 0.0,
        "median": statistics.median(data) if data else 0.0, "p50": percentile(data, .50),
        "p95": percentile(data, .95), "p99": percentile(data, .99),
        "stddev": statistics.pstdev(data) if len(data) > 1 else 0.0,
    }


def prf(expected: set[tuple[str, str]], actual: set[tuple[str, str]]) -> tuple[float, float, float]:
    true_positive = len(expected & actual)
    precision = rate(true_positive, len(actual))
    recall = rate(true_positive, len(expected))
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1
