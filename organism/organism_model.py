"""Integrate longitudinal, organ, aging and anomaly state.

This is a software representation of observations, not a clinical digital twin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from organs.organ_model import OrganState


@dataclass(frozen=True)
class OrganismState:
    subject_id: str
    timepoint_id: str
    organs: Mapping[str, OrganState] = field(default_factory=dict)
    biomarkers: Mapping[str, float] = field(default_factory=dict)
    aging_scores: Mapping[str, float] = field(default_factory=dict)
    anomaly_signals: tuple[str, ...] = ()

    def with_anomaly(self, signal: str) -> "OrganismState":
        if not signal.strip():
            raise ValueError("signal cannot be empty")
        return OrganismState(
            subject_id=self.subject_id,
            timepoint_id=self.timepoint_id,
            organs=dict(self.organs),
            biomarkers=dict(self.biomarkers),
            aging_scores=dict(self.aging_scores),
            anomaly_signals=self.anomaly_signals + (signal,),
        )


@dataclass
class OrganismModel:
    subject_id: str
    history: list[OrganismState] = field(default_factory=list)

    def add_state(self, state: OrganismState) -> None:
        if state.subject_id != self.subject_id:
            raise ValueError("State belongs to a different subject")
        if self.history and state.timepoint_id == self.history[-1].timepoint_id:
            raise ValueError("Duplicate timepoint")
        self.history.append(state)

    @property
    def current(self) -> OrganismState | None:
        return self.history[-1] if self.history else None

    def trajectory(self) -> tuple[OrganismState, ...]:
        return tuple(self.history)

    def biomarker_change(self, name: str) -> float | None:
        if len(self.history) < 2:
            return None
        previous = self.history[-2].biomarkers.get(name)
        current = self.history[-1].biomarkers.get(name)
        if previous is None or current is None:
            return None
        return current - previous
