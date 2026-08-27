"""Spatial hierarchy for the digital twin."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


@dataclass
class SpatialPoint:
    """A point in the twin coordinate system."""

    x: float
    y: float
    z: float
    coordinate_system: str = "hand"


@dataclass
class CellLocation:
    """Spatial identity of one cell."""

    cell_id: str
    position: SpatialPoint
    tissue_id: Optional[str] = None
    structure_id: Optional[str] = None
    cell_type: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StructureRegion:
    """A structure inside a tissue region."""

    structure_id: str
    name: str
    region_id: Optional[str] = None
    structure_type: Optional[str] = None
    bounds_min: Optional[SpatialPoint] = None
    bounds_max: Optional[SpatialPoint] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TissueRegion:
    """A spatially localized tissue region."""

    tissue_id: str
    tissue_type: str = "skin"
    name: Optional[str] = None
    region_id: Optional[str] = None
    bounds_min: Optional[SpatialPoint] = None
    bounds_max: Optional[SpatialPoint] = None
    structures: Dict[str, StructureRegion] = field(default_factory=dict)
    cells: Dict[str, CellLocation] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_structure(self, structure: StructureRegion) -> None:
        self.structures[structure.structure_id] = structure

    def add_cell(self, cell: CellLocation) -> None:
        self.cells[cell.cell_id] = cell


@dataclass
class HandRegion:
    """A named anatomical region of the hand."""

    region_id: str
    name: str
    side: Optional[str] = None
    bounds_min: Optional[SpatialPoint] = None
    bounds_max: Optional[SpatialPoint] = None
    tissues: Dict[str, TissueRegion] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_tissue(self, tissue: TissueRegion) -> None:
        self.tissues[tissue.tissue_id] = tissue


@dataclass
class HandSpatialModel:
    """Hand -> region -> tissue -> structure -> cell hierarchy."""

    coordinate_system: str = "hand"
    regions: Dict[str, HandRegion] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_region(self, region: HandRegion) -> None:
        self.regions[region.region_id] = region
        self._touch()

    def add_tissue(self, region_id: str, tissue: TissueRegion) -> None:
        self._region(region_id).add_tissue(tissue)
        self._touch()

    def add_structure(self, region_id: str, tissue_id: str, structure: StructureRegion) -> None:
        self._tissue(region_id, tissue_id).add_structure(structure)
        self._touch()

    def add_cell(self, region_id: str, tissue_id: str, cell: CellLocation) -> None:
        self._tissue(region_id, tissue_id).add_cell(cell)
        self._touch()

    def locate_cell(self, cell_id: str) -> Optional[CellLocation]:
        for region in self.regions.values():
            for tissue in region.tissues.values():
                if cell_id in tissue.cells:
                    return tissue.cells[cell_id]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def _region(self, region_id: str) -> HandRegion:
        if region_id not in self.regions:
            raise KeyError(f"Unknown hand region: {region_id}")
        return self.regions[region_id]

    def _tissue(self, region_id: str, tissue_id: str) -> TissueRegion:
        region = self._region(region_id)
        if tissue_id not in region.tissues:
            raise KeyError(f"Unknown tissue '{tissue_id}' in region '{region_id}'")
        return region.tissues[tissue_id]

    def _touch(self) -> None:
        self.updated_at = datetime.utcnow().isoformat()
