"""Research-grade primitives for identifying persistent temporal changes."""

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ChangePointResult:
    index: int
    before_mean: float
    after_mean: float
    magnitude: float


def detect_change_points(values: Iterable[float], min_segment_size: int = 2, threshold: float = 1.0) -> list[ChangePointResult]:
    values = list(values)
    if min_segment_size < 1 or threshold < 0:
        raise ValueError("invalid parameters")
    results: list[ChangePointResult] = []
    for i in range(min_segment_size, len(values) - min_segment_size + 1):
        before = values[i - min_segment_size:i]
        after = values[i:i + min_segment_size]
        before_mean = sum(before) / len(before)
        after_mean = sum(after) / len(after)
        magnitude = abs(after_mean - before_mean)
        if magnitude >= threshold:
            results.append(ChangePointResult(i, before_mean, after_mean, magnitude))
    return results
