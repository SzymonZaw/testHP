from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LongitudinalObservation:
    observation_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    zone_id: str
    level: str
    metric: str
    value: float
    spatial_reference: str | None = None
    cell_id: str | None = None
    tissue_id: str | None = None

    def validate(self) -> None:
        if not self.observation_id:
            raise ValueError("observation_id is required")
        if not self.subject_id or not self.hand_id or not self.timepoint_id:
            raise ValueError("subject, hand and timepoint are required")
        if not self.zone_id or not self.metric:
            raise ValueError("zone_id and metric are required")
        if self.level not in {"cell", "tissue", "anatomy"}:
            raise ValueError("level must be cell, tissue or anatomy")
        if self.level == "cell" and not self.cell_id:
            raise ValueError("cell observations require cell_id")
        if self.level == "tissue" and not self.tissue_id:
            raise ValueError("tissue observations require tissue_id")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "observation_id": self.observation_id,
            "subject_id": self.subject_id,
            "hand_id": self.hand_id,
            "timepoint_id": self.timepoint_id,
            "zone_id": self.zone_id,
            "level": self.level,
            "metric": self.metric,
            "value": self.value,
            "spatial_reference": self.spatial_reference,
            "cell_id": self.cell_id,
            "tissue_id": self.tissue_id,
        }
