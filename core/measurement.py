"""Raw or directly derived quantitative measurements."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .anatomy import AnatomicalLocation
from .biomarker import Biomarker
from .uncertainty import Uncertainty


@dataclass
class Measurement:
    id: str
    subject_id: str
    timepoint_id: str
    modality: str
    biomarker: Biomarker
    value: Any
    measured_at: datetime
    anatomical_location: Optional[AnatomicalLocation] = None
    unit: Optional[str] = None
    uncertainty: Optional[Uncertainty] = None
    source: Optional[str] = None
    model_version: Optional[str] = None
    processing_version: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.subject_id.strip() or not self.timepoint_id.strip():
            raise ValueError("Measurement ids and subject_id cannot be empty")
        if not self.modality.strip():
            raise ValueError("Measurement modality cannot be empty")
