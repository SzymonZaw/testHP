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
from .biological_age import BiologicalAgeEngine
from .canonical_cell_state import CanonicalCellState, build_canonical_cell_state
from .cell_assessment import CellAssessmentEngine
from .database import connect, ensure_schema
from .multiscale_chain import MultiscaleChain, build_multiscale_chain


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


@dataclass(frozen=True)
class CellAssessmentBundle:
    state_assessment: CellStateAssessment
    age_estimate: BiologicalAgeEstimate


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
    biological_state_assessments: dict[str, BiologicalStateAssessment] = field(default_factory=dict)
    biological_age_estimates: dict[str, BiologicalAgeEstimate] = field(default_factory=dict)

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
        return (left.subject_id, left.hand_id, left.timepoint_id) == (right.subject_id, right.hand_id, right.timepoint_id)

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

    def add_biological_state_assessment(self, value: BiologicalStateAssessment) -> None:
        value.validate()
        cell = self.cells.get(value.target_object_id)
        if cell is None:
            raise ValueError("biological state assessment requires an existing cell")
        if not self._same_context(value, cell):
            raise ValueError("biological state assessment and cell must share subject/hand/timepoint")
        self.biological_state_assessments[value.assessment_id] = value

    def add_biological_age_estimate(self, value: BiologicalAgeEstimate) -> None:
        value.validate()
        cell = self.cells.get(value.target_object_id)
        if cell is None:
            raise ValueError("biological age estimate requires an existing cell")
        if not self._same_context(value, cell):
            raise ValueError("biological age estimate and cell must share subject/hand/timepoint")
        self.biological_age_estimates[value.estimate_id] = value

    def canonical_cell_state(self, cell_id: str) -> CanonicalCellState:
        cell = self.cells.get(cell_id)
        if cell is None:
            raise KeyError(f"unknown cell: {cell_id}")
        states = [x for x in self.biological_state_assessments.values() if x.target_object_id == cell_id and self._same_context(x, cell)]
        legacy_states = [x for x in self.cell_state_assessments.values() if x.cell_id == cell_id and self._same_context(x, cell)]
        if states and legacy_states:
            raise ValueError(f"cell {cell_id} has conflicting state assessment representations")
        if len(states) > 1 or len(legacy_states) > 1:
            raise ValueError(f"cell {cell_id} has multiple state assessments")
        ages = [x for x in self.biological_age_estimates.values() if x.target_object_id == cell_id and self._same_context(x, cell)]
        if len(ages) > 1:
            raise ValueError(f"cell {cell_id} has multiple biological age estimates")
        assessment = states[0] if states else (legacy_states[0] if legacy_states else None)
        return build_canonical_cell_state(cell, state_assessment=assessment, age_estimate=ages[0] if ages else None)

    def assess_and_register_cell(self, cell_id: str, *, observations: dict[str, Any], age_observations: dict[str, Any], source_data_ids: tuple[str, ...], assessed_at: str, state_engine: CellAssessmentEngine | None = None, age_engine: BiologicalAgeEngine | None = None) -> CellAssessmentBundle:
        cell = self.cells.get(cell_id)
        if cell is None:
            raise KeyError(f"unknown cell: {cell_id}")
        if not source_data_ids:
            raise ValueError("source_data_ids are required")
        state_result = (state_engine or CellAssessmentEngine()).assess(cell, observations=observations, source_data_ids=source_data_ids, assessed_at=assessed_at)
        age_result = (age_engine or BiologicalAgeEngine()).estimate(cell, observations=age_observations, source_data_ids=source_data_ids, assessed_at=assessed_at)
        self.add_cell_state_assessment(state_result.assessment)
        self.add_biological_age_estimate(age_result.estimate)
        return CellAssessmentBundle(state_result.assessment, age_result.estimate)

    def chain_for_cell(self, cell_id: str) -> MultiscaleChain:
        cell = self.cells.get(cell_id)
        if cell is None:
            raise KeyError(f"unknown cell: {cell_id}")
        tissue = self.tissues.get(cell.tissue_id)
        if tissue is None:
            raise ValueError(f"cell {cell_id} has no tissue parent")
        anatomy = self.anatomy.get(tissue.anatomical_structure_id)
        if anatomy is None:
            raise ValueError(f"tissue {tissue.tissue_id} has no anatomical parent")
        histologies = [x for x in self.histology.values() if x.tissue_id == tissue.tissue_id and self._same_context(x, cell)]
        states = [x for x in self.biological_state_assessments.values() if x.target_object_id == cell_id and self._same_context(x, cell)]
        ages = [x for x in self.biological_age_estimates.values() if x.target_object_id == cell_id and self._same_context(x, cell)]
        if len(histologies) > 1 or len(states) > 1 or len(ages) > 1:
            raise ValueError(f"cell {cell_id} has multiple matching child records")
        return build_multiscale_chain(anatomy, tissue, histology=histologies[0] if histologies else None, cell=cell, state_assessment=states[0] if states else None, age_estimate=ages[0] if ages else None)

    def validate_integrity(self) -> None:
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
        for assessment in self.biological_state_assessments.values():
            cell = self.cells.get(assessment.target_object_id)
            if cell is None:
                raise ValueError(f"biological state assessment {assessment.assessment_id} has no cell parent")
            if not self._same_context(assessment, cell):
                raise ValueError(f"biological state assessment {assessment.assessment_id} has mismatched context")
        for estimate in self.biological_age_estimates.values():
            cell = self.cells.get(estimate.target_object_id)
            if cell is None:
                raise ValueError(f"biological age estimate {estimate.estimate_id} has no cell parent")
            if not self._same_context(estimate, cell):
                raise ValueError(f"biological age estimate {estimate.estimate_id} has mismatched context")

    def snapshot(self) -> dict[str, list[dict[str, Any]]]:
        self.validate_integrity()
        return {name: [asdict(x) for x in values.values()] for name, values in (("coordinate_systems", self.coordinate_systems), ("registrations", self.registrations), ("acquisitions", self.acquisitions), ("anatomy", self.anatomy), ("tissues", self.tissues), ("histology", self.histology), ("cells", self.cells), ("cell_state_assessments", self.cell_state_assessments), ("biological_state_assessments", self.biological_state_assessments), ("biological_age_estimates", self.biological_age_estimates))}


def register_tissue(tissue: TissueRegion) -> TissueRegion:
    tissue.validate()
    ensure_schema()
    with connect() as conn:
        conn.execute("""INSERT INTO tissue_regions (tissue_id, anatomical_structure_id, subject_id, hand_id, timepoint_id, tissue_type, geometry, source_data_ids, spatial_reference, confidence, provenance) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tissue_id) DO UPDATE SET anatomical_structure_id=EXCLUDED.anatomical_structure_id, tissue_type=EXCLUDED.tissue_type, geometry=EXCLUDED.geometry, source_data_ids=EXCLUDED.source_data_ids, spatial_reference=EXCLUDED.spatial_reference, confidence=EXCLUDED.confidence, provenance=EXCLUDED.provenance""", (tissue.tissue_id, tissue.anatomical_structure_id, tissue.subject_id, tissue.hand_id, tissue.timepoint_id, tissue.tissue_type, _json(tissue.geometry), _json(list(tissue.source_data_ids)), _json(tissue.spatial_reference), tissue.confidence, _json(tissue.provenance)))
        conn.commit()
    return tissue


def register_cell(cell: CellObject) -> CellObject:
    cell.validate()
    ensure_schema()
    with connect() as conn:
        conn.execute("""INSERT INTO cells (cell_id, tissue_id, subject_id, hand_id, timepoint_id, position, cell_type, morphology, size, nucleus, neighbors, source_data_ids, spatial_reference, confidence, provenance) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (cell_id) DO UPDATE SET tissue_id=EXCLUDED.tissue_id, position=EXCLUDED.position, cell_type=EXCLUDED.cell_type, morphology=EXCLUDED.morphology, size=EXCLUDED.size, nucleus=EXCLUDED.nucleus, neighbors=EXCLUDED.neighbors, source_data_ids=EXCLUDED.source_data_ids, spatial_reference=EXCLUDED.spatial_reference, confidence=EXCLUDED.confidence, provenance=EXCLUDED.provenance""", (cell.cell_id, cell.tissue_id, cell.subject_id, cell.hand_id, cell.timepoint_id, _json(cell.position), cell.cell_type, _json(cell.morphology), _json(cell.size), _json(cell.nucleus), _json(list(cell.neighbors)), _json(list(cell.source_data_ids)), _json(cell.spatial_reference), cell.confidence, _json(cell.provenance)))
        conn.commit()
    return cell


def register_biological_state(assessment: BiologicalStateAssessment) -> BiologicalStateAssessment:
    assessment.validate()
    ensure_schema()
    with connect() as conn:
        conn.execute("""INSERT INTO biological_state_assessments (assessment_id, subject_id, hand_id, timepoint_id, target_object_id, state, confidence, evidence, uncertainty, provenance, assessed_at, model_id, model_version, metadata) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (assessment_id) DO UPDATE SET state=EXCLUDED.state, confidence=EXCLUDED.confidence, evidence=EXCLUDED.evidence, uncertainty=EXCLUDED.uncertainty, provenance=EXCLUDED.provenance, assessed_at=EXCLUDED.assessed_at, model_id=EXCLUDED.model_id, model_version=EXCLUDED.model_version, metadata=EXCLUDED.metadata""", (assessment.assessment_id, assessment.subject_id, assessment.hand_id, assessment.timepoint_id, assessment.target_object_id, assessment.state, assessment.confidence, _json([_json_value(x) for x in assessment.evidence]), _json(assessment.uncertainty), _json(assessment.provenance), assessment.assessed_at, assessment.model_id, assessment.model_version, _json(assessment.metadata)))
        conn.commit()
    return assessment


def register_biological_age(estimate: BiologicalAgeEstimate) -> BiologicalAgeEstimate:
    estimate.validate()
    ensure_schema()
    with connect() as conn:
        conn.execute("""INSERT INTO biological_age_estimates (estimate_id, subject_id, hand_id, timepoint_id, target_object_id, estimated_age_years, uncertainty, evidence, provenance, assessed_at, model_id, model_version, metadata) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (estimate_id) DO UPDATE SET estimated_age_years=EXCLUDED.estimated_age_years, uncertainty=EXCLUDED.uncertainty, evidence=EXCLUDED.evidence, provenance=EXCLUDED.provenance, assessed_at=EXCLUDED.assessed_at, model_id=EXCLUDED.model_id, model_version=EXCLUDED.model_version, metadata=EXCLUDED.metadata""", (estimate.estimate_id, estimate.subject_id, estimate.hand_id, estimate.timepoint_id, estimate.target_object_id, estimate.estimated_age_years, _json(estimate.uncertainty), _json([_json_value(x) for x in estimate.evidence]), _json(estimate.provenance), estimate.assessed_at, estimate.model_id, estimate.model_version, _json(estimate.metadata)))
        conn.commit()
    return estimate
