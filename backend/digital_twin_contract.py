from __future__ import annotations

"""Single canonical Digital Twin aggregate and validation boundary."""

from dataclasses import dataclass, field
from typing import Any

from .anatomy_foundation import MultiscaleHierarchy


@dataclass(frozen=True)
class DigitalTwin:
    twin_id: str
    subject_id: str
    hand_id: str
    timepoints: tuple[str, ...] = ()
    hierarchy: MultiscaleHierarchy | None = None
    evidence_ids: tuple[str, ...] = ()
    contract_version: str = "1"
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.twin_id or not self.subject_id or not self.hand_id:
            raise ValueError("DigitalTwin requires twin_id, subject_id and hand_id")
        if self.hierarchy is not None:
            if self.hierarchy.hand_id != self.hand_id:
                raise ValueError("DigitalTwin hierarchy belongs to another hand")
            self.hierarchy.validate()
        if len(set(self.timepoints)) != len(self.timepoints):
            raise ValueError("DigitalTwin timepoints must be unique")

    def snapshot(self, timepoint_id: str | None = None) -> dict[str, Any]:
        self.validate()
        if timepoint_id is not None and timepoint_id not in self.timepoints:
            raise ValueError("unknown timepoint")
        return {
            "twin_id": self.twin_id,
            "subject_id": self.subject_id,
            "hand_id": self.hand_id,
            "timepoint_id": timepoint_id,
            "contract_version": self.contract_version,
            "evidence_ids": self.evidence_ids,
        }
