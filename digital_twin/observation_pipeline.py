"""End-to-end observation ingestion for the hand digital twin."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from core.observation import Observation

from .observation_mapper import SpatialObservationMapper


@dataclass
class ObservationRecord:
    """An accepted observation together with its resolved spatial context."""

    observation: Observation
    spatial_context: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation.id,
            "subject_id": self.observation.subject_id,
            "timepoint_id": self.observation.timepoint_id,
            "name": self.observation.name,
            "value": self.observation.value,
            "observed_at": self.observation.observed_at.isoformat(),
            "biological_level": self.observation.biological_level,
            "modality": self.observation.modality,
            "spatial_context": self.spatial_context,
        }


@dataclass
class ObservationPipeline:
    """Store observations and resolve their spatial identity consistently."""

    mapper: SpatialObservationMapper
    records: List[ObservationRecord] = field(default_factory=list)
    _ids: set[str] = field(default_factory=set, init=False, repr=False)

    def ingest(self, observation: Observation) -> ObservationRecord:
        """Validate, spatially resolve, and retain an observation."""
        if observation.id in self._ids:
            raise ValueError(f"Observation already ingested: {observation.id}")
        context = self.mapper.resolve(observation)
        record = ObservationRecord(observation=observation, spatial_context=context)
        self.records.append(record)
        self._ids.add(observation.id)
        return record

    def ingest_many(self, observations: List[Observation]) -> List[ObservationRecord]:
        return [self.ingest(observation) for observation in observations]

    def for_cell(self, cell_id: str) -> List[ObservationRecord]:
        return [record for record in self.records if record.spatial_context.get("cell_id") == cell_id]

    def for_timepoint(self, timepoint_id: str) -> List[ObservationRecord]:
        return [record for record in self.records if record.observation.timepoint_id == timepoint_id]

    def to_dict(self) -> Dict[str, Any]:
        return {"records": [record.to_dict() for record in self.records]}

    def ingest_into_twin(self, twin: Any, observation: Observation, timepoint_name: str | None = None) -> ObservationRecord:
        """Validate spatial identity, retain the observation, then update the twin.

        The existing aggregate updater remains backward compatible. Biological
        state is updated only when the observation explicitly carries a
        ``metadata['twin_update']`` payload.
        """
        record = self.ingest(observation)
        payload = observation.metadata.get("twin_update") if observation.metadata else None
        if payload:
            twin.update(payload, timepoint=timepoint_name or observation.timepoint_id)
        return record
