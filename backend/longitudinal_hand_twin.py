"""Longitudinal history for traceable hand-state observations."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from .hand_state import HandState


@dataclass(frozen=True)
class HandObservation:
    """One immutable hand-state observation at a point in time."""

    observed_at: str
    state: HandState


@dataclass
class LongitudinalHandTwin:
    """Stores hand observations over time without replacing prior states."""

    twin_id: str
    hand_id: str
    observations: list[HandObservation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_observation(self, state: HandState, observed_at: str | None = None) -> HandObservation:
        """Append a hand state to the timeline and keep earlier observations intact."""
        if state.hand_id != self.hand_id:
            raise ValueError("hand state belongs to a different hand")
        timestamp = observed_at or datetime.now(timezone.utc).isoformat()
        observation = HandObservation(observed_at=timestamp, state=state)
        self.observations.append(observation)
        self.observations.sort(key=lambda item: item.observed_at)
        return observation

    def extend(self, observations: Iterable[HandObservation]) -> None:
        """Append validated observations to the timeline."""
        for observation in observations:
            self.add_observation(observation.state, observation.observed_at)

    @property
    def latest(self) -> HandObservation | None:
        """Return the most recent observation, if one exists."""
        return self.observations[-1] if self.observations else None

    def biological_age_trend(self) -> list[tuple[str, float]]:
        """Return observations that contain a biological-age estimate."""
        return [
            (observation.observed_at, observation.state.biological_age)
            for observation in self.observations
            if observation.state.biological_age is not None
        ]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
