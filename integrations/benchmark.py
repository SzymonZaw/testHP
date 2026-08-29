from __future__ import annotations

"""Model-agnostic benchmarking primitives for testHP.

The benchmark layer never declares a clinical diagnosis. It compares model
outputs against supplied ground truth/reference metrics and returns ranked
candidates together with uncertainty and provenance-friendly metadata.
"""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class BenchmarkResult:
    model_id: str
    task: str
    metrics: Mapping[str, float]
    primary_score: float
    sample_count: int = 0
    notes: str = ""


@dataclass(frozen=True)
class RankedModel:
    model_id: str
    primary_score: float
    rank: int
    metrics: Mapping[str, float]


def rank_models(
    results: list[BenchmarkResult],
    *,
    higher_is_better: bool = True,
) -> list[RankedModel]:
    """Rank benchmark results without coupling testHP to a model vendor."""
    ordered = sorted(
        results,
        key=lambda item: item.primary_score,
        reverse=higher_is_better,
    )
    return [
        RankedModel(
            model_id=item.model_id,
            primary_score=item.primary_score,
            rank=index,
            metrics=item.metrics,
        )
        for index, item in enumerate(ordered, start=1)
    ]


def select_best(
    results: list[BenchmarkResult],
    *,
    higher_is_better: bool = True,
) -> RankedModel | None:
    """Return the top benchmark candidate, or None for an empty benchmark."""
    ranked = rank_models(results, higher_is_better=higher_is_better)
    return ranked[0] if ranked else None
