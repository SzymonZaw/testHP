"""Process new observations without discarding biological history."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from ..core.observation import Observation


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
    """Store an observation, infer its cell when possible, and preserve prior history."""
    if observation.subject_id != twin.subject_id:
        raise ValueError("Observation subject_id must match the DigitalTwin subject_id")

    previous = twin.observations.get(observation.id)
    is_revision = previous is not None
    if previous is not None:
        observation.version = previous.version + 1
        observation.created_at = previous.created_at
        observation.updated_at = datetime.utcnow()

    evidence = twin.add_observation(observation, confidence=confidence)
    cell_id = getattr(observation, "cell_id", None)
    inference = None
    trend = None
    if cell_id:
        inference = twin.infer_cell(cell_id, observed_at=observation.observed_at)
        trend = twin.cell_inference_trend(cell_id)

    return ObservationProcessResult(
        observation_id=observation.id,
        cell_id=cell_id,
        inference=inference,
        trend=trend,
        is_revision=is_revision,
        version=observation.version,
    )
