"""Canonical raw observation model for Digital Twin inputs."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Observation:
    """A raw biological measurement with traceability and quality metadata."""

    observation_id: str
    subject_id: str
    cell_id: str
    sample_id: str
    observed_at: datetime
    modality: str
    feature: str
    value: Any
    unit: Optional[str] = None
    spatial_location: Optional[Dict[str, Any]] = None
    provenance: Optional[str] = None
    quality: Optional[float] = None
    uncertainty: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["observed_at"] = self.observed_at.isoformat()
        return result

    def validate(self) -> None:
        if not self.observation_id or not self.subject_id or not self.cell_id or not self.sample_id:
            raise ValueError("observation identifiers must be non-empty")
        if not self.modality or not self.feature:
            raise ValueError("modality and feature must be non-empty")
        for name, value in (("quality", self.quality), ("uncertainty", self.uncertainty)):
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
