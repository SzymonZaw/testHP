import pytest

from backend.biological_state import (
    BiologicalAgeEstimate,
    BiologicalStateAssessment,
    InterpretationEvidence,
)
from backend.data_foundation import Provenance, Uncertainty


def _evidence() -> InterpretationEvidence:
    return InterpretationEvidence(
        evidence_id="e1",
        source_object_ids=("cell:c1", "image:slide1"),
        kind="morphology",
        value={"nucleus_area": 12.4},
        confidence=0.91,
    )


def test_interpretation_keeps_evidence_and_provenance_separate():
    evidence = _evidence()
    assessment = BiologicalStateAssessment(
        assessment_id="assessment:c1",
        subject_id="s1",
        hand_id="h1",
        timepoint_id="t1",
        target_object_id="cell:c1",
        state="indeterminate",
        confidence=0.62,
        evidence=(evidence,),
        uncertainty=Uncertainty(kind="probability", score=0.38),
        provenance=Provenance(source_object_ids=("cell:c1",), method="cell-state-model", method_version="0.1"),
        assessed_at="2026-08-27T00:00:00+00:00",
    )
    data = assessment.to_dict()
    assert data["state"] == "indeterminate"
    assert data["evidence"][0]["source_object_ids"] == ("cell:c1", "image:slide1")
    assert data["provenance"]["method"] == "cell-state-model"


def test_assessment_requires_evidence():
    with pytest.raises(ValueError, match="requires evidence"):
        BiologicalStateAssessment(
            "a", "s", "h", "t", "cell:c1", "normal", 0.9, (),
            Uncertainty(), Provenance(), "2026-08-27T00:00:00+00:00"
        ).validate()


def test_biological_age_is_an_estimate_with_explicit_uncertainty():
    estimate = BiologicalAgeEstimate(
        estimate_id="age:c1:t1",
        subject_id="s1",
        hand_id="h1",
        timepoint_id="t1",
        target_object_id="cell:c1",
        estimated_age_years=72.0,
        uncertainty=Uncertainty(kind="interval", interval=(65.0, 80.0)),
        evidence=(_evidence(),),
        provenance=Provenance(source_object_ids=("cell:c1",), method="biological-age-model", method_version="0.1"),
        assessed_at="2026-08-27T00:00:00+00:00",
    )
    assert estimate.to_dict()["uncertainty"]["interval"] == (65.0, 80.0)
