import pytest

from backend.biological_state import InterpretationEvidence
from backend.cell_analysis import CellAnalysisInput, build_cell_age_estimate, build_cell_state_assessment
from backend.data_foundation import Provenance, SpatialReference, Uncertainty
from backend.evidence_attachment import EvidenceAttachment


def make_input():
    provenance = Provenance(source_object_ids=("slide-1",), method="test")
    attachment = EvidenceAttachment(
        attachment_id="att-1",
        evidence_id="ev-1",
        source_asset_id="slide-1",
        subject_id="s1",
        hand_id="h1",
        timepoint_id="T0",
        spatial_node_id="cell-1",
        spatial_level="cell",
        modality="histology",
        spatial_reference=SpatialReference(
            "hand-frame:T0", "registered", transform={"type": "identity", "version": "1"}
        ),
        provenance=provenance,
    )
    evidence = InterpretationEvidence(
        evidence_id="ev-1",
        source_object_ids=("slide-1",),
        kind="morphology",
        value={"nucleus_area": 3.0},
        confidence=0.9,
        provenance=provenance,
    )
    return CellAnalysisInput("cell-1", attachment, evidence), provenance


def test_analysis_rejects_evidence_for_another_cell():
    analysis, _ = make_input()
    with pytest.raises(ValueError, match="must target the supplied cell"):
        CellAnalysisInput("cell-2", analysis.attachment, analysis.evidence).validate()


def test_state_and_age_share_explicit_cell_evidence():
    analysis, provenance = make_input()
    uncertainty = Uncertainty(kind="test", score=0.1)
    state = build_cell_state_assessment(
        analysis,
        assessment_id="state-1",
        state="normal",
        confidence=0.9,
        assessed_at="2026-08-27T00:00:00+00:00",
        provenance=provenance,
        uncertainty=uncertainty,
        model_id="cell-state-test",
        model_version="1",
    )
    age = build_cell_age_estimate(
        analysis,
        estimate_id="age-1",
        estimated_age_years=42.0,
        uncertainty=Uncertainty(kind="interval", interval=(39.0, 45.0)),
        assessed_at="2026-08-27T00:00:00+00:00",
        provenance=provenance,
        model_id="cell-age-test",
        model_version="1",
    )
    assert state.target_object_id == age.target_object_id == "cell-1"
    assert state.evidence[0].evidence_id == age.evidence[0].evidence_id == "ev-1"
