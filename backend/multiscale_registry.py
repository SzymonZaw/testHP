from __future__ import annotations

"""Persistence boundary for the multiscale digital-twin chain."""

from dataclasses import asdict
from typing import Any

from psycopg.types.json import Json

from .anatomy_foundation import CellObject, TissueRegion
from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment
from .database import connect, ensure_schema


def _json(value: Any) -> Json:
    """Wrap Python JSON-compatible values for psycopg JSON/JSONB columns."""
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    return Json(value)


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


def _json_value(value: Any) -> Any:
    """Convert dataclasses recursively to plain JSON-compatible structures."""
    return asdict(value) if hasattr(value, "__dataclass_fields__") else value
