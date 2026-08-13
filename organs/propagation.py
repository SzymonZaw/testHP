"""Propagate organ-level signals through declared dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .organ_model import OrganSystemModel


@dataclass(frozen=True)
class OrganSignal:
    organ: str
    score: float
    source: str
    path: tuple[str, ...]


class OrganSignalPropagator:
    """Propagate a bounded signal through dependency edges.

    This is an explainable systems model, not a physiological causal model.
    """

    def __init__(self, system: OrganSystemModel, decay: float = 0.5) -> None:
        if not 0 < decay <= 1:
            raise ValueError("decay must be in (0, 1]")
        self.system = system
        self.decay = float(decay)

    def propagate(self, source_scores: Mapping[str, float], max_depth: int = 3) -> tuple[OrganSignal, ...]:
        if max_depth < 0:
            raise ValueError("max_depth cannot be negative")
        result: list[OrganSignal] = []
        for source, score in source_scores.items():
            if source not in self.system.organs:
                raise KeyError(source)
            self._walk(source, float(score), (source,), 0, max_depth, result)
        return tuple(result)

    def _walk(
        self,
        organ: str,
        score: float,
        path: tuple[str, ...],
        depth: int,
        max_depth: int,
        result: list[OrganSignal],
    ) -> None:
        result.append(OrganSignal(organ, score, path[0], path))
        if depth >= max_depth:
            return
        for target, weight in self.system.organs[organ].dependencies.items():
            if target in path:
                continue
            self._walk(
                target,
                score * weight * self.decay,
                path + (target,),
                depth + 1,
                max_depth,
                result,
            )
