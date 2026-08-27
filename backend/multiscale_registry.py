from __future__ import annotations

"""Phase B runtime registry for multimodal acquisition and multiscale links."""

from dataclasses import asdict, dataclass, field
from typing import Any

from .anatomy_foundation import AnatomicalStructure, CellObject, HandCoordinateSystem, HistologyRegion, Registration, TissueRegion
from .data_foundation import Acquisition, DataObject, SpatialReference


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

    def add_canonical_acquisition(self, acquisition: Acquisition, data_object: DataObject, hand_id: str) -> ModalityAcquisition:
        if acquisition.subject_id != data_object.subject_id or acquisition.timepoint_id != data_object.timepoint_id:
            raise ValueError("acquisition and data object identity do not match")
        value = ModalityAcquisition(acquisition.acquisition_id, acquisition.subject_id, hand_id, acquisition.timepoint_id, acquisition.modality, [data_object.data_id])
        self.add_acquisition(value)
        return value

    def add_registration(self, value: Registration) -> None:
        value.validate()
        if value.target_frame not in self.coordinate_systems:
            raise ValueError("registration target frame is not registered in the hand coordinate system registry")
        self.registrations[value.registration_id] = value

    def register_data_object(self, data_object: DataObject, registration_id: str) -> DataObject:
        registration = self.registrations.get(registration_id)
        if registration is None:
            raise ValueError("unknown registration")
        if data_object.data_id not in registration.provenance.source_object_ids and data_object.data_id not in data_object.derived_from:
            raise ValueError("registration does not reference this data object")
        spatial = SpatialReference(
            frame_id=registration.target_frame,
            registration_status="registered",
            anatomical_target=data_object.spatial_reference.anatomical_target,
            transform=registration.transform,
            registration_quality=registration.quality.score,
        )
        return DataObject(
            data_id=data_object.data_id, data_type=data_object.data_type, subject_id=data_object.subject_id,
            timepoint_id=data_object.timepoint_id, acquisition_id=data_object.acquisition_id,
            source_class=data_object.source_class, modality=data_object.modality, status=data_object.status,
            quality=data_object.quality, uncertainty=data_object.uncertainty, provenance=data_object.provenance,
            spatial_reference=spatial, derived_from=data_object.derived_from, created_at=data_object.created_at,
            metadata=data_object.metadata,
        )

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
        if not any((x.subject_id, x.hand_id, x.timepoint_id) == (subject_id, hand_id, timepoint_id) for x in self.coordinate_systems.values()):
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
