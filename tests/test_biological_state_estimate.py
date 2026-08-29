import pytest

from backend.biological_hierarchy import BiologicalObservation
from backend.biological_state_estimate import BiologicalStateEstimate
from backend.biological_timeline import BiologicalTimeline
from backend.biological_trajectory import BiologicalTrajectory


def test_state_estimate_preserves_evidence_and_values():
    estimate = BiologicalStateEstimate(
        health_state="abnormal",
        biological_age=67.4,
        confidence=0.82,
        evidence_ids=("obs-101", "obs-145"),
    )

    assert estimate.health_state == "abnormal"
    assert estimate.biological_age == 67.4
    assert estimate.confidence == 0.82
    assert estimate.evidence_ids == ("obs-101", "obs-145")
    assert estimate.has_evidence


def test_state_estimate_rejects_invalid_values():
    with pytest.raises(ValueError):
        BiologicalStateEstimate(biological_age=-1)
    with pytest.raises(ValueError):
        BiologicalStateEstimate(confidence=1.1)
    with pytest.raises(ValueError):
        BiologicalStateEstimate(evidence_ids=("obs-1", "obs-1"))


def test_state_estimate_retains_trajectory_context_and_evidence():
    timeline = BiologicalTimeline((
        BiologicalObservation("obs-1", "microscopy", "2026-01-01", {"marker": 0.8}, confidence=0.9),
        BiologicalObservation("obs-2", "microscopy", "2027-01-01", {"marker": 0.6}, confidence=0.9),
    ))
    trajectory = BiologicalTrajectory.from_timeline(timeline, "marker")
    estimate = BiologicalStateEstimate.from_trajectory(
        trajectory,
        health_state="abnormal",
        biological_age=67.4,
        confidence=0.82,
        evidence_ids=("obs-1", "obs-2"),
    )

    assert estimate.trajectory_key == "marker"
    assert estimate.trajectory_direction == "decreasing"
    assert estimate.trajectory_delta == -0.2
    assert estimate.evidence_ids == ("obs-1", "obs-2")
    assert estimate.has_evidence


def test_state_estimate_without_trajectory_remains_valid():
    estimate = BiologicalStateEstimate(health_state="unknown", confidence=0.4)

    assert estimate.trajectory_key is None
    assert estimate.trajectory_delta is None
    assert not estimate.has_evidence
