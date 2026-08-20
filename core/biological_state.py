"""Canonical biological state model for one subject, timepoint and scope."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping

from .observation import Observation


BIOLOGICAL_STATE_DIMENSIONS = (
    "biological_age",
    "structural_functional_state",
    "damage",
    "pathology",
)


@dataclass
class BiologicalState:
    """Single source of truth for the research interpretation layer.

    The model stores observations and derived evidence metadata, while keeping
    interpretation values separate. Missing evidence is represented explicitly
    and never converted into a positive biological conclusion.
    """

    subject_id: str
    timepoint_id: str
    observations: List[Observation] = field(default_factory=list)
    dimensions: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    evidence_count: int = 0
    availability: str = "insufficient_evidence"
    confidence: float | None = None
    interpretations: Mapping[str, Any] = field(default_factory=dict)

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

    def interpretation(self, name: str) -> Any | None:
        return self.interpretations.get(name)
