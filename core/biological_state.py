"""Aggregated biological state for one subject and timepoint."""

from dataclasses import dataclass, field
from typing import Dict, List

from .observation import Observation


@dataclass
class BiologicalState:
    subject_id: str
    timepoint_id: str
    observations: List[Observation] = field(default_factory=list)
    dimensions: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)

    def add_observation(self, observation: Observation) -> None:
        if observation.subject_id != self.subject_id:
            raise ValueError("Observation belongs to a different subject")
        if observation.timepoint_id != self.timepoint_id:
            raise ValueError("Observation belongs to a different timepoint")
        self.observations.append(observation)

    def set_dimension(self, name: str, value: float) -> None:
        if not name.strip():
            raise ValueError("Dimension name cannot be empty")
        self.dimensions[name] = float(value)

    def get_dimension(self, name: str) -> float | None:
        return self.dimensions.get(name)
