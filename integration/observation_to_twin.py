"""Unified research pipeline from observations to a digital twin snapshot."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from organism.digital_twin import DigitalBiologicalTwin, TwinSnapshot


@dataclass(frozen=True)
class Observation:
    """A raw biological observation with basic provenance and quality."""

    feature: str
    value: float
    quality_score: float = 1.0
    modality: str = "unknown"


class ObservationToTwinPipeline:
    """Connect quality-filtered observations to the digital-twin history."""

    def __init__(self, twin: DigitalBiologicalTwin, minimum_quality: float = 0.5) -> None:
        if not 0 <= minimum_quality <= 1:
            raise ValueError("minimum_quality must be between 0 and 1")
        self.twin = twin
        self.minimum_quality = minimum_quality

    def build_snapshot(
        self,
        timepoint_id: str,
        observations: Iterable[Observation],
        captured_at: datetime,
    ) -> TwinSnapshot:
        accepted: dict[str, Any] = {}
        provenance: list[str] = []
        for item in observations:
            if item.quality_score < self.minimum_quality:
                continue
            accepted[item.feature] = item.value
            provenance.append(item.modality)
        return TwinSnapshot(
            timepoint_id,
            captured_at,
            accepted,
            tuple(dict.fromkeys(provenance)),
        )

    def ingest(
        self,
        timepoint_id: str,
        observations: Iterable[Observation],
        captured_at: datetime,
    ) -> TwinSnapshot:
        """Build and persist one validated snapshot in the twin history."""
        snapshot = self.build_snapshot(timepoint_id, observations, captured_at)
        self.twin.add_snapshot(snapshot)
        return snapshot
