import os

import pytest

from backend.anatomy_foundation import AnatomicalStructure, CellObject, Geometry, TissueRegion
from backend.biological_state import (
    BiologicalAgeEstimate,
    BiologicalStateAssessment,
    InterpretationEvidence,
)
from backend.data_foundation import Provenance, SpatialReference, Uncertainty
from backend.multiscale_registry import (
    register_biological_age,
    register_biological_state,
    register_cell,
    register_tissue,
)

pytestmark = pytest.mark.integration


def _provenance() -> Provenance:
    return Provenance(
        method="integration-test",
        method_version="1",
        source_object_ids=("dataset-e2e",),
    )


def test_multiscale_chain_persists_to_postgresql():
    if not os.getenv("TESTHP_DATABASE_URL"):
        pytest.skip("TESTHP_DATABASE_URL is required for PostgreSQL integration tests")

    subject_id = "e2e_multiscale_subject"
    hand_id = "e2e_multiscale_hand"
    timepoint_id = "T0"
    frame = "hand-frame:e2e:T0"
    # A registered reference must carry an explicit transform.
    sr = SpatialReference(frame, "registered", transform={"type": "identity", "version": "1"})
    provenance = _provenance()

    anatomy = AnatomicalStructure(
        structure_id="anatomy-e2e-palm",
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        anatomical_identity="skin",
        geometry=Geometry("geom-e2e", "volume", frame, payload={"type": "test"}),
        source_data_ids=("dataset-e2e",),
        spatial_reference=sr,
        provenance=provenance,
    )
    tissue = TissueRegion(
        tissue_id="tissue-e2e-001",
        anatomical_structure_id=anatomy.structure_id,
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        tissue_type="epidermis",
        geometry=Geometry("tissue-geom-e2e", "segmentation", frame),
        source_data_ids=("dataset-e2e",),
        spatial_reference=sr,
        provenance=provenance,
    )
    cell = CellObject(
        cell_id="cell-e2e-001",
        tissue_id=tissue.tissue_id,
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        position={"x": 1.0, "y": 2.0, "z": 3.0},
        cell_type="keratinocyte",
        morphology={"area": 12.5},
        size={"diameter": 4.0},
        nucleus={"area": 3.0},
        neighbors=(),
        source_data_ids=("dataset-e2e",),
        spatial_reference=sr,
        provenance=provenance,
    )

    evidence = InterpretationEvidence(
        evidence_id="evidence-e2e-001",
        source_object_ids=("dataset-e2e",),
        kind="morphology",
        value={"area": 12.5},
        confidence=0.91,
        provenance=provenance,
    )
    assessment = BiologicalStateAssessment(
        assessment_id="assessment-e2e-001",
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        target_object_id=cell.cell_id,
        state="normal",
        confidence=0.91,
        evidence=(evidence,),
        uncertainty=Uncertainty(kind="test", score=0.09),
        provenance=provenance,
        assessed_at="2026-08-27T00:00:00+00:00",
        model_id="test-model",
        model_version="1",
    )
    age = BiologicalAgeEstimate(
        estimate_id="age-e2e-001",
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        target_object_id=cell.cell_id,
        estimated_age_years=42.0,
        uncertainty=Uncertainty(kind="test", interval=(39.5, 44.5)),
        evidence=(evidence,),
        provenance=provenance,
        assessed_at="2026-08-27T00:00:00+00:00",
        model_id="test-age-model",
        model_version="1",
    )

    from backend.database import connect, ensure_schema

    ensure_schema()
    # The multiscale tables reference the subject and hand, so seed their
    # canonical parents exactly as the real ingestion layer would.
    with connect() as conn:
        conn.execute(
            "INSERT INTO subjects (subject_id) VALUES (%s) ON CONFLICT (subject_id) DO NOTHING",
            (subject_id,),
        )
        conn.execute(
            "INSERT INTO hands (hand_id, subject_id, laterality) VALUES (%s,%s,%s) ON CONFLICT (hand_id) DO NOTHING",
            (hand_id, subject_id, "right"),
        )
        conn.commit()

    register_tissue(tissue)
    register_cell(cell)
    register_biological_state(assessment)
    register_biological_age(age)

    with connect() as conn:
        tissue_row = conn.execute(
            "SELECT tissue_id, anatomical_structure_id FROM tissue_regions WHERE tissue_id=%s",
            (tissue.tissue_id,),
        ).fetchone()
        cell_row = conn.execute(
            "SELECT cell_id, tissue_id FROM cells WHERE cell_id=%s",
            (cell.cell_id,),
        ).fetchone()
        state_row = conn.execute(
            "SELECT target_object_id, state FROM biological_state_assessments WHERE assessment_id=%s",
            (assessment.assessment_id,),
        ).fetchone()
        age_row = conn.execute(
            "SELECT target_object_id, estimated_age_years FROM biological_age_estimates WHERE estimate_id=%s",
            (age.estimate_id,),
        ).fetchone()

    assert tissue_row["anatomical_structure_id"] == anatomy.structure_id
    assert cell_row["tissue_id"] == tissue.tissue_id
    assert state_row["target_object_id"] == cell.cell_id
    assert state_row["state"] == "normal"
    assert age_row["target_object_id"] == cell.cell_id
    assert age_row["estimated_age_years"] == 42.0
