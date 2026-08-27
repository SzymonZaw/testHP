import pytest

from backend.biological_state import BiologicalAgeEstimate, BiologicalStateAssessment, InterpretationEvidence
from backend.data_foundation import Provenance, Uncertainty
from backend.longitudinal_cells import CellTimepointRecord, build_cell_trajectory, trajectory_summary


def _evidence(tp: str) -> InterpretationEvidence:
    return InterpretationEvidence(
        evidence_id=f"ev-{tp}",
        source_object_ids=(f"obs-{tp}",),
        kind="morphology",
        value={"area": 10},
        confidence=0.9,
        provenance=Provenance(source_object_ids=(f"obs-{tp}",), method="test"),
    )


def _assessment(tp: str, state: str = "normal") -> BiologicalStateAssessment:
    return BiologicalStateAssessment(
        assessment_id=f"assessment-{tp}", subject_id="s1", hand_id="h1", timepoint_id=tp,
        target_object_id="cell-1", state=state, confidence=0.9,
        evidence=(_evidence(tp),), uncertainty=Uncertainty(kind="test", score=0.1),
        provenance=Provenance(source_object_ids=(f"obs-{tp}",)), assessed_at="2026-01-01T00:00:00+00:00",
        model_id="test-model", model_version="1",
    )


def _age(tp: str, years: float) -> BiologicalAgeEstimate:
    return BiologicalAgeEstimate(
        estimate_id=f"age-{tp}", subject_id="s1", hand_id="h1", timepoint_id=tp,
        target_object_id="cell-1", estimated_age_years=years,
        uncertainty=Uncertainty(kind="test", interval=(years - 1, years + 1)),
        evidence=(_evidence(tp),), provenance=Provenance(source_object_ids=(f"obs-{tp}",)),
        assessed_at="2026-01-01T00:00:00+00:00", model_id="age-model", model_version="1",
    )


def _record(tp: str, state: str = "normal", age: float | None = None) -> CellTimepointRecord:
    return CellTimepointRecord("cell-1", "s1", "h1", tp, _assessment(tp, state), _age(tp, age) if age is not None else None)


def test_build_cell_trajectory_orders_points_and_tracks_change():
    trajectory = build_cell_trajectory([_record("T2", "atypical", 43), _record("T0", "normal", 40), _record("T1", "normal", 41)])
    assert [point.timepoint_id for point in trajectory.points] == ["T0", "T1", "T2"]
    assert trajectory.state_sequence == ("normal", "normal", "atypical")
    assert trajectory.biological_age_delta == 3


def test_trajectory_rejects_mixed_identity_and_duplicate_timepoints():
    with pytest.raises(ValueError, match="same subject/hand"):
        build_cell_trajectory([_record("T0"), CellTimepointRecord("cell-2", "s1", "h1", "T1")])
    with pytest.raises(ValueError, match="duplicate timepoints"):
        build_cell_trajectory([_record("T0"), _record("T0")])


def test_assessment_and_age_must_target_same_cell_and_context():
    bad = BiologicalStateAssessment(
        assessment_id="a", subject_id="s1", hand_id="h1", timepoint_id="T0", target_object_id="other",
        state="normal", confidence=0.9, evidence=(_evidence("T0"),),
        uncertainty=Uncertainty(kind="test"), provenance=Provenance(source_object_ids=("obs-T0",)),
        assessed_at="2026-01-01T00:00:00+00:00",
    )
    with pytest.raises(ValueError, match="assessment target"):
        CellTimepointRecord("cell-1", "s1", "h1", "T0", assessment=bad).validate()


def test_summary_is_explicitly_non_clinical():
    summary = trajectory_summary(build_cell_trajectory([_record("T0", age=40), _record("T1", "atypical", 42)]))
    assert summary["biological_age_delta_years"] == 2
    assert summary["interpretation"] == "longitudinal_observed_assessments_only"
