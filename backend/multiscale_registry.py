from __future__ import annotations

"""Persistence boundary and in-memory compatibility registry for the multiscale twin."""

from dataclasses import asdict, dataclass, field
from typing import Any

from .anatomy_foundation import (
    AnatomicalStructure,
    CellObject,
    HandCoordinateSystem,
    HistologyRegion,
    Registration,
    TissueRegion,
    validate_multiscale_chain,
)
from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment
from .database import connect, ensure_schema


@dataclass(frozen=True)
class ModalityAcquisition:
    acquisition_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    modality: str
    source_data_ids: list[str]
    source_frame: str
    metadata: dict[str, Any] = field(default_factory=dict)


class MultiscaleRegistry:
    """Lightweight Phase-B registry retained for domain-level tests and callers."""

    def __init__(self) -> None:
        self.coordinate_systems: dict[str, HandCoordinateSystem] = {}
        self.registrations: dict[str, Registration] = {}
        self.acquisitions: dict[str, ModalityAcquisition] = {}
        self.anatomy: dict[str, AnatomicalStructure] = {}
        self.tissues: dict[str, TissueRegion] = {}
        self.histology: dict[str, HistologyRegion] = {}
        self.cells: dict[str, CellObject] = {}

    def add_coordinate_system(self, value: HandCoordinateSystem) -> None:
        self.coordinate_systems[value.frame_id] = value

    def add_registration(self, value: Registration) -> None:
        value.validate()
        if value.target_frame not in self.coordinate_systems:
            raise ValueError("registration target frame must be a registered hand coordinate system")
        self.registrations[value.registration_id] = value

    def add_acquisition(self, value: ModalityAcquisition) -> None:
        self.acquisitions[value.acquisition_id] = value

    def add_anatomy(self, value: AnatomicalStructure) -> None:
        value.validate()
        frame = self.coordinate_systems.get(value.spatial_reference.frame_id)
        if frame is None:
            raise ValueError("anatomical structure requires an existing coordinate system")
        self.anatomy[value.structure_id] = value

    def add_tissue(self, value: TissueRegion) -> None:
        value.validate()
        parent = self.anatomy.get(value.anatomical_structure_id)
        if parent is None:
            raise ValueError("tissue requires an existing anatomical structure")
        validate_multiscale_chain(parent, value)
        self.tissues[value.tissue_id] = value

    def add_histology(self, value: HistologyRegion) -> None:
        if value.tissue_id not in self.tissues:
            raise ValueError("histology requires an existing tissue")
        self.histology[value.histology_id] = value

    def add_cell(self, value: CellObject) -> None:
        value.validate()
        tissue = self.tissues.get(value.tissue_id)
        if tissue is None:
            raise ValueError("cell requires an existing tissue")
        if (value.subject_id, value.hand_id, value.timepoint_id) != (tissue.subject_id, tissue.hand_id, tissue.timepoint_id):
            raise ValueError("cell and tissue belong to different subject/hand/timepoint")
        self.cells[value.cell_id] = value

    def snapshot(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "coordinate_systems": [asdict(v) for v in self.coordinate_systems.values()],
            "registrations": [asdict(v) for v in self.registrations.values()],
            "acquisitions": [asdict(v) for v in self.acquisitions.values()],
            "anatomy": [asdict(v) for v in self.anatomy.values()],
            "tissues": [asdict(v) for v in self.tissues.values()],
            "histology": [asdict(v) for v in self.histology.values()],
            "cells": [asdict(v) for v in self.cells.values()],
        }


def _json(value: Any) -> Any:
    return asdict(value) if hasattr(value, "__dataclass_fields__") else value


def register_tissue(tissue: TissueRegion) -> TissueRegion:
    tissue.validate()
    ensure_schema()
    with connect() as conn:
        conn.execute(
            """INSERT INTO tissue_regions
               (tissue_id, anatomical_structure_id, subject_id, hand_id,
                timepoint_id, tissue_type, geometry, source_data_ids,
                spatial_reference, confidence, provenance)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (tissue_id) DO UPDATE SET
                 anatomical_structure_id=EXCLUDED.anatomical_structure_id,
                 tissue_type=EXCLUDED.tissue_type, geometry=EXCLUDED.geometry,
                 source_data_ids=EXCLUDED.source_data_ids,
                 spatial_reference=EXCLUDED.spatial_reference,
                 confidence=EXCLUDED.confidence, provenance=EXCLUDED.provenance""",
            (tissue.tissue_id, tissue.anatomical_structure_id, tissue.subject_id,
             tissue.hand_id, tissue.timepoint_id, tissue.tissue_type,
             _json(tissue.geometry), list(tissue.source_data_ids),
             _json(tissue.spatial_reference), tissue.confidence,
             _json(tissue.provenance)),
        )
        conn.commit()
    return tissue


def register_cell(cell: CellObject) -> CellObject:
    cell.validate()
    ensure_schema()
    with connect() as conn:
        conn.execute(
            """INSERT INTO cells
               (cell_id, tissue_id, subject_id, hand_id, timepoint_id,
                position, cell_type, morphology, size, nucleus, neighbors,
                source_data_ids, spatial_reference, confidence, provenance)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (cell_id) DO UPDATE SET tissue_id=EXCLUDED.tissue_id,
                 position=EXCLUDED.position, cell_type=EXCLUDED.cell_type,
                 morphology=EXCLUDED.morphology, size=EXCLUDED.size,
                 nucleus=EXCLUDED.nucleus, neighbors=EXCLUDED.neighbors,
                 source_data_ids=EXCLUDED.source_data_ids,
                 spatial_reference=EXCLUDED.spatial_reference,
                 confidence=EXCLUDED.confidence, provenance=EXCLUDED.provenance""",
            (cell.cell_id, cell.tissue_id, cell.subject_id, cell.hand_id,
             cell.timepoint_id, _json(cell.position), cell.cell_type,
             _json(cell.morphology), _json(cell.size), _json(cell.nucleus),
             list(cell.neighbors), list(cell.source_data_ids),
             _json(cell.spatial_reference), cell.confidence,
             _json(cell.provenance)),
        )
        conn.commit()
    return cell


def register_biological_state(assessment: BiologicalStateAssessment) -> BiologicalStateAssessment:
    assessment.validate()
    ensure_schema()
    with connect() as conn:
        conn.execute(
            """INSERT INTO biological_state_assessments
               (assessment_id, subject_id, hand_id, timepoint_id, target_object_id,
                state, confidence, evidence, uncertainty, provenance, assessed_at,
                model_id, model_version, metadata)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (assessment_id) DO UPDATE SET state=EXCLUDED.state,
                 confidence=EXCLUDED.confidence, evidence=EXCLUDED.evidence,
                 uncertainty=EXCLUDED.uncertainty, provenance=EXCLUDED.provenance,
                 assessed_at=EXCLUDED.assessed_at, model_id=EXCLUDED.model_id,
                 model_version=EXCLUDED.model_version, metadata=EXCLUDED.metadata""",
            (assessment.assessment_id, assessment.subject_id, assessment.hand_id,
             assessment.timepoint_id, assessment.target_object_id, assessment.state,
             assessment.confidence, [_json(x) for x in assessment.evidence],
             _json(assessment.uncertainty), _json(assessment.provenance),
             assessment.assessed_at, assessment.model_id, assessment.model_version,
             assessment.metadata),
        )
        conn.commit()
    return assessment


def register_biological_age(estimate: BiologicalAgeEstimate) -> BiologicalAgeEstimate:
    estimate.validate()
    ensure_schema()
    with connect() as conn:
        conn.execute(
            """INSERT INTO biological_age_estimates
               (estimate_id, subject_id, hand_id, timepoint_id, target_object_id,
                estimated_age_years, uncertainty, evidence, provenance, assessed_at,
                model_id, model_version, metadata)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (estimate_id) DO UPDATE SET
                 estimated_age_years=EXCLUDED.estimated_age_years,
                 uncertainty=EXCLUDED.uncertainty, evidence=EXCLUDED.evidence,
                 provenance=EXCLUDED.provenance, assessed_at=EXCLUDED.assessed_at,
                 model_id=EXCLUDED.model_id, model_version=EXCLUDED.model_version,
                 metadata=EXCLUDED.metadata""",
            (estimate.estimate_id, estimate.subject_id, estimate.hand_id,
             estimate.timepoint_id, estimate.target_object_id,
             estimate.estimated_age_years, _json(estimate.uncertainty),
             [_json(x) for x in estimate.evidence], _json(estimate.provenance),
             estimate.assessed_at, estimate.model_id, estimate.model_version,
             estimate.metadata),
        )
        conn.commit()
    return estimate
