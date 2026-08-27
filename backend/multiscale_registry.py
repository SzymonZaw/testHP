from __future__ import annotations

"""Phase B runtime registry: modality acquisition, registration and links.

The registry is intentionally storage-neutral. It provides a canonical bridge
between the existing ingestion objects and the Phase-B domain objects.
"""

from dataclasses import asdict, dataclass, field
from typing import Any

from .anatomy_foundation import AnatomicalStructure, HistologyRegion, TissueRegion, CellObject, Registration, HandCoordinateSystem


@dataclass
class ModalityAcquisition:
    acquisition_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    modality: str
    source_data_ids: list[str] = field(default_factory=list)
    source_frame: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class MultiscaleRegistry:
    coordinate_systems: dict[str, HandCoordinateSystem] = field(default_factory=dict)
    acquisitions: dict[str, ModalityAcquisition] = field(default_factory=dict)
    registrations: dict[str, Registration] = field(default_factory=dict)
    anatomy: dict[str, AnatomicalStructure] = field(default_factory=dict)
    tissues: dict[str, TissueRegion] = field(default_factory=dict)
    histology: dict[str, HistologyRegion] = field(default_factory=dict)
    cells: dict[str, CellObject] = field(default_factory=dict)

    def add_coordinate_system(self, value: HandCoordinateSystem) -> None:
        self.coordinate_systems[value.frame_id] = value

    def add_acquisition(self, value: ModalityAcquisition) -> None:
        self.acquisitions[value.acquisition_id] = value

    def add_registration(self, value: Registration) -> None:
        value.validate()
        if value.target_frame not in self.coordinate_systems:
            raise ValueError("registration target frame is not registered in the hand coordinate system registry")
        self.registrations[value.registration_id] = value

    def add_anatomy(self, value: AnatomicalStructure) -> None:
        value.validate()
        self._check_identity(value.subject_id, value.hand_id, value.timepoint_id)
        self.anatomy[value.structure_id] = value

    def add_tissue(self, value: TissueRegion) -> None:
        value.validate()
        parent = self.anatomy.get(value.anatomical_structure_id)
        if parent is None:
            raise ValueError("tissue requires an existing anatomical structure")
        if (parent.subject_id, parent.hand_id, parent.timepoint_id) != (value.subject_id, value.hand_id, value.timepoint_id):
            raise ValueError("tissue and anatomy subject/hand/timepoint do not match")
        self.tissues[value.tissue_id] = value

    def add_histology(self, value: HistologyRegion) -> None:
        if value.tissue_id not in self.tissues:
            raise ValueError("histology requires an existing tissue region")
        self.histology[value.histology_id] = value

    def add_cell(self, value: CellObject) -> None:
        value.validate()
        if value.tissue_id not in self.tissues:
            raise ValueError("cell requires an existing tissue region")
        self.cells[value.cell_id] = value

    def _check_identity(self, subject_id: str, hand_id: str, timepoint_id: str) -> None:
        for cs in self.coordinate_systems.values():
            if (cs.subject_id, cs.hand_id, cs.timepoint_id) == (subject_id, hand_id, timepoint_id):
                return
        raise ValueError("subject/hand/timepoint has no hand coordinate system")

    def snapshot(self) -> dict[str, Any]:
        return {
            "coordinate_systems": [asdict(x) for x in self.coordinate_systems.values()],
            "acquisitions": [x.to_dict() for x in self.acquisitions.values()],
            "registrations": [asdict(x) for x in self.registrations.values()],
            "anatomy": [asdict(x) for x in self.anatomy.values()],
            "tissues": [asdict(x) for x in self.tissues.values()],
            "histology": [asdict(x) for x in self.histology.values()],
            "cells": [asdict(x) for x in self.cells.values()],
        }
