import pytest

from backend.biological_state_estimate import BiologicalStateEstimate


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
