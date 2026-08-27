from __future__ import annotations

"""Persistence boundary for the multiscale digital-twin chain."""

from dataclasses import asdict, dataclass, field
from typing import Any

from psycopg.types.json import Json

from .anatomy_foundation import (
    AnatomicalStructure, CellObject, CellStateAssessment, HandCoordinateSystem,
    HistologyRegion, Registration, TissueRegion,
)
from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment
from .database import connect, ensure_schema


def _json(value: Any) -> Json:
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    return Json(value)


def _json_value(value: Any) -> Any:
    return asdict(value) if hasattr(value, "__dataclass_fields__") else value


@dataclass(frozen=True)
class ModalityAcquisition:
    acquisition_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    modality: str
    source_data_ids: list[str]
    frame_id: str


@dataclass
class MultiscaleRegistry:
    coordinate_systems: dict[str, HandCoordinateSystem] = field(default_factory=dict)
    registrations: dict[str, Registration] = field(default_factory=dict)
    acquisitions: dict[str, ModalityAcquisition] = field(default_factory=dict)
    anatomy: dict[str, AnatomicalStructure] = field(default_factory=dict)
    tissues: dict[str, TissueRegion] = field(default_factory=dict)
    histology: dict[str, HistologyRegion] = field(default_factory=dict)
    cells: dict[str, CellObject] = field(default_factory=dict)
    cell_state_assessments: dict[str, CellStateAssessment] = field(default_factory=dict)

    def add_coordinate_system(self, value: HandCoordinateSystem) -> None:
        self.coordinate_systems[value.frame_id] = value

    def add_registration(self, value: Registration) -> None:
        if value.target_frame not in self.coordinate_systems:
            raise ValueError("registration target frame must already exist")
        self.registrations[value.registration_id] = value

    def add_acquisition(self, value: ModalityAcquisition) -> None:
        self.acquisitions[value.acquisition_id] = value

    def add_anatomy(self, value: AnatomicalStructure) -> None:
        value.validate()
        self.anatomy[value.structure_id] = value

    @staticmethod
    def _same_context(left: Any, right: Any) -> bool:
        return (
            left.subject_id,
            left.hand_id,
            left.timepoint_id,
        ) == (
            right.subject_id,
            right.hand_id,
            right.timepoint_id,
        )

    def add_tissue(self, value: TissueRegion) -> None:
        value.validate()
        parent = self.anatomy.get(value.anatomical_structure_id)
        if parent is None:
            raise ValueError("tissue requires an existing anatomical structure")
        if not self._same_context(value, parent):
            raise ValueError("tissue and anatomical structure must share subject/hand/timepoint")
        self.tissues[value.tissue_id] = value

    def add_histology(self, value: HistologyRegion) -> None:
        value.validate()
        parent = self.tissues.get(value.tissue_id)
        if parent is None:
            raise ValueError("histology requires an existing tissue")
        if not self._same_context(value, parent):
            raise ValueError("histology and tissue must share subject/hand/timepoint")
        self.histology[value.histology_id] = value

    def add_cell(self, value: CellObject) -> None:
        value.validate()
        parent = self.tissues.get(value.tissue_id)
        if parent is None:
            raise ValueError("cell requires an existing tissue")
        if not self._same_context(value, parent):
            raise ValueError("cell and tissue must share subject/hand/timepoint")
        self.cells[value.cell_id] = value

    def add_cell_state_assessment(self, value: CellStateAssessment) -> None:
        value.validate()
        if value.cell_id not in self.cells:
            raise ValueError("cell state assessment requires an existing cell")
        self.cell_state_assessments[value.assessment_id] = value

    def validate_integrity(self) -> None:
        """Validate the complete in-memory macro→tissue→cell chain.

        This is intentionally structural: it checks identity, parent links and
        context continuity, but never infers health, disease or treatment.
        """
        for tissue in self.tissues.values():
            parent = self.anatomy.get(tissue.anatomical_structure_id)
            if parent is None:
                raise ValueError(f"tissue {tissue.tissue_id} has no anatomical parent")
            if not self._same_context(tissue, parent):
                raise ValueError(f"tissue {tissue.tissue_id} has mismatched subject/hand/timepoint")

        for histology in self.histology.values():
            parent = self.tissues.get(histology.tissue_id)
            if parent is None:
                raise ValueError(f"histology {histology.histology_id} has no tissue parent")
            if not self._same_context(histology, parent):
                raise ValueError(f"histology {histology.histology_id} has mismatched subject/hand/timepoint")

        for cell in self.cells.values():
            parent = self.tissues.get(cell.tissue_id)
            if parent is None:
                raise ValueError(f"cell {cell.cell_id} has no tissue parent")
            if not self._same_context(cell, parent):
                raise ValueError(f"cell {cell.cell_id} has mismatched subject/hand/timepoint")

        for assessment in self.cell_state_assessments.values():
            if assessment.cell_id not in self.cells:
                raise ValueError(f"cell state assessment {assessment.assessment_id} has no cell parent")

    def snapshot(self) -> dict[str, list[dict[str, Any]]]:
        self.validate_integrity()
        return {
            name: [asdict(x) for x in values.values()]
            for name, values in (
                ("coordinate_systems", self.coordinate_systems),
                ("registrations", self.registrations),
                ("acquisitions", self.acquisitions),
                ("anatomy", self.anatomy),
                ("tissues", self.tissues),
                ("histology", self.histology),
                ("cells", self.cells),
                ("cell_state_assessments", self.cell_state_assessments),
            )
        }


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
             _json(tissue.geometry), _json(list(tissue.source_data_ids)),
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
             _json(list(cell.neighbors)), _json(list(cell.source_data_ids)),
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
             assessment.confidence, _json([_json_value(x) for x in assessment.evidence]),
             _json(assessment.uncertainty), _json(assessment.provenance),
             assessment.assessed_at, assessment.model_id, assessment.model_version,
             _json(assessment.metadata)),
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
             _json([_json_value(x) for x in estimate.evidence]),
             _json(estimate.provenance), estimate.assessed_at,
             estimate.model_id, estimate.model_version, _json(estimate.metadata)),
        )
        conn.commit()
    return estimate
