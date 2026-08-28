"""Normalize external observations into digital-twin structures."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .anatomical_location import AnatomicalLocation
from .cell_profile import CellProfile, build_cell_profile
from .hand_observation import HandObservation


@dataclass
class ObservationIngestionResult:
    cells: List[CellProfile] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


class ObservationIngestion:
    """Single entry point for microscopy, imaging, lab and manual inputs."""

    def ingest_cells(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        source: str,
    ) -> ObservationIngestionResult:
        result = ObservationIngestionResult(provenance={"source": source})

        for record in records:
            cell_id = record.get("cell_id")
            if not cell_id:
                result.warnings.append("missing cell_id")
                continue

            location = None
            if any(k in record for k in ("hand_side", "region_id", "tissue_id")):
                location = AnatomicalLocation(
                    hand_side=record.get("hand_side"),
                    region_id=record.get("region_id"),
                    tissue_id=record.get("tissue_id"),
                    confidence=float(record.get("location_confidence", 0.0)),
                )

            profile = build_cell_profile(
                cell_id=str(cell_id),
                biological_age=record.get("biological_age"),
                health_markers=record.get("health_markers"),
                function_score=record.get("function_score"),
                confidence=float(record.get("confidence", 0.0)),
                tissue_id=record.get("tissue_id"),
                cell_type=record.get("cell_type"),
                observed_at=record.get("observed_at"),
                location=location,
                metadata={"source": source},
            )
            result.cells.append(profile)

        return result

    def build_observation(
        self,
        *,
        observation_id: str,
        observed_at: str,
        hand_id: str,
        cells: Iterable[CellProfile],
        provenance: Optional[Dict[str, Any]] = None,
        confidence: float = 0.0,
    ) -> HandObservation:
        cell_map = {cell.cell_id: cell for cell in cells}
        return HandObservation(
            observation_id=observation_id,
            observed_at=observed_at,
            hand_id=hand_id,
            cells=cell_map,
            provenance=provenance or {},
            confidence=confidence,
        )
