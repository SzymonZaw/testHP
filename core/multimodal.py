"""Common interface for heterogeneous biological observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .measurement import Measurement
from .observation import Observation

Record = Measurement | Observation


@dataclass(frozen=True)
class ObservationBatch:
    subject_id: str
    timepoint_id: str
    records: tuple[Record, ...]

    @property
    def modalities(self) -> tuple[str, ...]:
        names = set()
        for record in self.records:
            if isinstance(record, Measurement):
                names.add(record.modality)
            else:
                modality = record.metadata.get("modality")
                if modality:
                    names.add(str(modality))
        return tuple(sorted(names))


@dataclass
class MultimodalObservationLayer:
    """Collect records from different modalities without altering provenance."""

    _records: list[Record] = field(default_factory=list)

    def add(self, record: Record) -> None:
        if not isinstance(record, (Measurement, Observation)):
            raise TypeError("record must be a Measurement or Observation")
        self._records.append(record)

    def add_many(self, records: Iterable[Record]) -> None:
        for record in records:
            self.add(record)

    def for_timepoint(self, subject_id: str, timepoint_id: str) -> ObservationBatch:
        records = tuple(
            record for record in self._records
            if record.subject_id == subject_id and record.timepoint_id == timepoint_id
        )
        return ObservationBatch(subject_id, timepoint_id, records)

    def for_modality(self, modality: str) -> tuple[Record, ...]:
        if not modality.strip():
            raise ValueError("modality cannot be empty")
        return tuple(
            record for record in self._records
            if (isinstance(record, Measurement) and record.modality == modality)
            or (isinstance(record, Observation) and record.metadata.get("modality") == modality)
        )

    @property
    def modalities(self) -> tuple[str, ...]:
        names = set()
        for record in self._records:
            if isinstance(record, Measurement):
                names.add(record.modality)
            else:
                modality = record.metadata.get("modality")
                if modality:
                    names.add(str(modality))
        return tuple(sorted(names))
