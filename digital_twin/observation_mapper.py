"""Map core observations onto the digital twin spatial hierarchy."""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.observation import Observation

from .spatial import HandSpatialModel


class SpatialObservationMapper:
    """Resolve an Observation to a concrete spatial entity.

    The mapper deliberately keeps the core Observation model independent from
    the hand-specific spatial implementation. Spatial identifiers are read from
    observation metadata, while anatomical_location remains the semantic
    location supplied by the core model.
    """

    def __init__(self, spatial_model: HandSpatialModel) -> None:
        self.spatial_model = spatial_model

    def resolve(self, observation: Observation) -> Dict[str, Any]:
        """Return the spatial context associated with an observation."""
        location = observation.anatomical_location
        metadata = observation.metadata or {}

        region_id = metadata.get("region_id")
        tissue_id = metadata.get("tissue_id")
        structure_id = metadata.get("structure_id")
        cell_id = metadata.get("cell_id")

        if location is not None:
            if location.level in {"cell", "cell_population"} and not cell_id:
                cell_id = location.id if location.level == "cell" else None
            if location.level == "tissue" and not tissue_id:
                tissue_id = location.id

        if cell_id:
            cell = self.spatial_model.locate_cell(cell_id)
            if cell is None:
                raise KeyError(f"Unknown spatial cell: {cell_id}")
            tissue_id = tissue_id or cell.tissue_id
            structure_id = structure_id or cell.structure_id

        if region_id and region_id not in self.spatial_model.regions:
            raise KeyError(f"Unknown spatial region: {region_id}")

        if tissue_id:
            matches = [
                region for region in self.spatial_model.regions.values()
                if tissue_id in region.tissues
            ]
            if not matches:
                raise KeyError(f"Unknown spatial tissue: {tissue_id}")
            if region_id and matches[0].region_id != region_id:
                raise ValueError("Tissue does not belong to the supplied region")
            region_id = region_id or matches[0].region_id

        if structure_id:
            found = False
            for region in self.spatial_model.regions.values():
                for tissue in region.tissues.values():
                    if structure_id in tissue.structures:
                        found = True
                        if tissue_id and tissue.tissue_id != tissue_id:
                            raise ValueError("Structure does not belong to the supplied tissue")
                        break
                if found:
                    break
            if not found:
                raise KeyError(f"Unknown spatial structure: {structure_id}")

        return {
            "region_id": region_id,
            "tissue_id": tissue_id,
            "structure_id": structure_id,
            "cell_id": cell_id,
            "biological_level": observation.biological_level,
            "timepoint_id": observation.timepoint_id,
            "observation_id": observation.id,
        }

    def index(self, observations: list[Observation]) -> Dict[str, Dict[str, Any]]:
        """Resolve and index observations by observation id."""
        return {observation.id: self.resolve(observation) for observation in observations}
