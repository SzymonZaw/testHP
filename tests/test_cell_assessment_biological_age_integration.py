from datetime import datetime

from digital_twin.biological_age_v01 import AgeEvidence, estimate_biological_age
from digital_twin.cell_assessment import CellAssessment


def test_cell_assessment_exposes_multicomponent_biological_age():
    estimate = estimate_biological_age(
        morphology=AgeEvidence(42, .9, 2, "synthetic-morphology"),
        cellular=AgeEvidence(45, .7, 3, "synthetic-cellular"),
        functional=AgeEvidence(41, .4, 1, "synthetic-functional"),
    )
    assessment = CellAssessment("cell-0347", datetime(2026, 3, 2))
    assessment.set_biological_age_estimate(estimate)

    assert assessment.biological_age == estimate.overall_age
    assert assessment.age_confidence == estimate.confidence
    assert assessment.biological_age_estimate["status"] == "estimated"
    assert assessment.biological_age_estimate["evidence_count"] == 6
    assert assessment.to_dict()["biological_age_estimate"]["molecular"] is None


def test_cell_assessment_preserves_insufficient_evidence():
    estimate = estimate_biological_age(cellular=AgeEvidence(45, .7, 4))
    assessment = CellAssessment("cell-0001", datetime(2026, 3, 2))
    assessment.set_biological_age_estimate(estimate)

    assert assessment.biological_age is None
    assert assessment.age_confidence == .7
    assert assessment.biological_age_estimate["status"] == "insufficient_evidence"
