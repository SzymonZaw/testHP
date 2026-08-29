from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Timepoint:
    timepoint_id: str
    observed_at: str
    source_ids: tuple[str, ...] = ()
    label: str | None = None


@dataclass(frozen=True)
class TemporalChange:
    spatial_id: str
    from_timepoint: str
    to_timepoint: str
    metrics: dict[str, float] = None  # type: ignore[assignment]
    direction: str = "unknown"
    confidence: float | None = None
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.spatial_id or not self.from_timepoint or not self.to_timepoint:
            raise ValueError("temporal change requires spatial target and two timepoints")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class TemporalTwin:
    twin_id: str
    timepoints: tuple[Timepoint, ...]
    changes: tuple[TemporalChange, ...] = ()

    def validate(self) -> None:
        ids = [item.timepoint_id for item in self.timepoints]
        if len(ids) != len(set(ids)):
            raise ValueError("timepoint IDs must be unique")
        for change in self.changes:
            change.validate()
            if change.from_timepoint not in ids or change.to_timepoint not in ids:
                raise ValueError("temporal change references unknown timepoint")
