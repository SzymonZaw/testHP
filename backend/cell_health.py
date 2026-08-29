from __future__ import annotations

"""Evidence-based cell health assessment primitives.

The module deliberately returns state and uncertainty, not a medical
recommendation. A model may populate the measurements/signals supplied here.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

HealthState = Literal["healthy", "altered", "stressed", "senescent", "pathological", "unknown"]


@dataclass(frozen=True)
class CellHealthAssessment:
    assessment_id: str
    cell_id: str
    state: HealthState
    score: float | None
    confidence: float | None
    signals: dict[str, Any] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    model_id: str | None = None
    model_version: str | None = None
    limitations: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.assessment_id or not self.cell_id:
            raise ValueError("cell health identity is required")
        for name, value in (("score", self.score), ("confidence", self.confidence)):
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.state == "healthy" and self.confidence is None:
            raise ValueError("healthy classification requires explicit confidence")


def build_health_assessment(**kwargs: Any) -> CellHealthAssessment:
    result = CellHealthAssessment(**kwargs)
    result.validate()
    return result
