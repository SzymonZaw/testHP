"""Aggregate whole-body signals into a transparent health state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from organs.propagation import OrganSignal
from .organism_model import OrganismState


@dataclass(frozen=True)
class HealthState:
    timepoint_id: str
    organ_signal_scores: Mapping[str, float]
    systemic_score: float
    anomaly_count: int
    flags: tuple[str, ...]


class HealthStateAggregator:
    """Summarize observed signals without diagnosing or prescribing treatment."""

    def aggregate(
        self,
        state: OrganismState,
        signals: Iterable[OrganSignal] = (),
    ) -> HealthState:
        scores: dict[str, float] = {}
        for signal in signals:
            scores[signal.organ] = max(scores.get(signal.organ, 0.0), signal.score)
        systemic = max(scores.values(), default=0.0)
        flags = tuple(state.anomaly_signals)
        return HealthState(
            timepoint_id=state.timepoint_id,
            organ_signal_scores=dict(scores),
            systemic_score=systemic,
            anomaly_count=len(flags),
            flags=flags,
        )
