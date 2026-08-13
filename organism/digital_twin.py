"""Persistent Digital Biological Twin foundation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class TwinSnapshot:
    """Immutable snapshot of modeled biological state at a timepoint."""

    timepoint_id: str
    captured_at: datetime
    state: Any
    provenance: tuple[str, ...] = ()
    uncertainty: Optional[Any] = None


@dataclass
class DigitalBiologicalTwin:
    """Longitudinal computational representation of one subject.

    Research data model only; it is not a clinical or predictive twin.
    """

    subject_id: str
    snapshots: list[TwinSnapshot] = field(default_factory=list)

    def add_snapshot(self, snapshot: TwinSnapshot) -> None:
        if snapshot.timepoint_id in {item.timepoint_id for item in self.snapshots}:
            raise ValueError(f"Snapshot already exists: {snapshot.timepoint_id}")
        self.snapshots.append(snapshot)
        self.snapshots.sort(key=lambda item: item.captured_at)

    def latest(self) -> Optional[TwinSnapshot]:
        return self.snapshots[-1] if self.snapshots else None

    def history(self) -> tuple[TwinSnapshot, ...]:
        return tuple(self.snapshots)

    def snapshot_at(self, timepoint_id: str) -> TwinSnapshot:
        for snapshot in self.snapshots:
            if snapshot.timepoint_id == timepoint_id:
                return snapshot
        raise KeyError(timepoint_id)

    def provenance(self) -> tuple[str, ...]:
        values: list[str] = []
        for snapshot in self.snapshots:
            values.extend(snapshot.provenance)
        return tuple(dict.fromkeys(values))
