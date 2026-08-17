"""Evidence and provenance links for multimodal biological analysis."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Evidence:
    """A traceable piece of support for an observation or derived result."""

    id: str
    subject_id: str
    observation_id: str
    artifact_ids: list[str] = field(default_factory=list)
    measurement_ids: list[str] = field(default_factory=list)
    evidence_type: str = "source"
    interpretation_boundary: str = "observation_only"
    provenance: Dict[str, Any] = field(default_factory=dict)
    confidence: Optional[float] = None

    def __post_init__(self) -> None:
        for name, value in (("id", self.id), ("subject_id", self.subject_id), ("observation_id", self.observation_id)):
            if not value.strip():
                raise ValueError(f"Evidence {name} cannot be empty")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Evidence confidence must be between 0 and 1")
