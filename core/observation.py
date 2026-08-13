"""Interpretations produced from one or more measurements."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from .anatomy import AnatomicalLocation
from .uncertainty import Uncertainty


@dataclass
class Observation:
    id: str
    subject_id: str
    timepoint_id: str
    name: str
    value: Any
    observed_at: datetime
    anatomical_location: Optional[AnatomicalLocation] = None
    uncertainty: Optional[Uncertainty] = None
    source_measurement_ids: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.subject_id.strip() or not self.timepoint_id.strip():
            raise ValueError("Observation ids and subject_id cannot be empty")
        if not self.name.strip():
            raise ValueError("Observation name cannot be empty")
