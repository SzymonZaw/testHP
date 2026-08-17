"""Physical or digital evidence supplied to the observation pipeline."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Artifact:
    """A source object such as an image, video, table, slide, or text file.

    Artifacts are deliberately modality-neutral. A biological observation can
    therefore be backed by images, video, microscopy, molecular tables, or
    other non-image evidence without changing the domain model.
    """

    id: str
    subject_id: str
    timepoint_id: str
    modality: str
    uri: str
    media_type: Optional[str] = None
    anatomical_location_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (("id", self.id), ("subject_id", self.subject_id), ("timepoint_id", self.timepoint_id), ("modality", self.modality), ("uri", self.uri)):
            if not value.strip():
                raise ValueError(f"Artifact {name} cannot be empty")
