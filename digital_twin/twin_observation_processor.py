"""Process new observations without discarding biological history."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .observation import Observation


@dataclass(frozen=True)
class ObservationProcessResult:
    observation_id: str
    cell_id: Optional[str]
    inference: Any
    trend: Any
    is_revision: bool
    version: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "cell_id": self.cell_id,
            "inference": self.inference.to_dict() if hasattr(self.inference, "to_dict") else self.inference,
            "trend": self.trend.to_dict() if hasattr(self.trend, "to_dict") else self.trend,
            "is_revision": self.is_revision,
            "version": self.version,
        }


def process_observation(twin: Any, observation: Observation, confidence: Optional[float] = None) -> ObservationProcessResult:
    """Store an observation and preserve replaced observations as immutable revisions."""
    if observation.subject_id != twin.subject_id:
        raise ValueError("Observation subject_id must match the DigitalTwin subject_id")
    observation.validate()

    previous = twin.observations.get(observation.observation_id)
    history = twin.metadata.setdefault("observation_revisions", {}).setdefault(observation.observation_id, [])
    version = len(history) + 1
    if previous is not None:
        history.append(previous.to_dict())

    twin.add_observation(observation, confidence=confidence)
    inference = twin.infer_cell(observation.cell_id, observed_at=observation.observed_at)
    trend = twin.cell_inference_trend(observation.cell_id)

    return ObservationProcessResult(
        observation_id=observation.observation_id,
        cell_id=observation.cell_id,
        inference=inference,
        trend=trend,
        is_revision=previous is not None,
        version=version,
    )
