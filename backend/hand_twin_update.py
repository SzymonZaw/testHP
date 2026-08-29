"""Canonical update flow for the longitudinal hand digital twin."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .hand_state import HandState
from .longitudinal_hand_twin import HandObservation, LongitudinalHandTwin


@dataclass(frozen=True)
class TwinUpdateResult:
    """Auditable result of adding one validated hand observation."""

    observation: HandObservation
    observation_count: int
    latest_biological_age: float | None
    health_trajectory: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation": {
                "observed_at": self.observation.observed_at,
                "state": self.observation.state.to_dict(),
            },
            "observation_count": self.observation_count,
            "latest_biological_age": self.latest_biological_age,
            "health_trajectory": self.health_trajectory.to_dict(),
        }


def update_hand_twin(
    twin: LongitudinalHandTwin,
    state: HandState,
    *,
    observed_at: str | None = None,
) -> TwinUpdateResult:
    """Add a hand observation and rebuild derived longitudinal health state.

    The function deliberately does not infer treatment, diagnosis, or
    rejuvenation actions. It only updates the observational twin and derives
    traceable longitudinal summaries.
    """
    observation = twin.add_observation(state, observed_at)
    trajectory = twin.health_trajectory()
    return TwinUpdateResult(
        observation=observation,
        observation_count=len(twin.observations),
        latest_biological_age=twin.latest_state.biological_age if twin.latest_state else None,
        health_trajectory=trajectory,
    )
