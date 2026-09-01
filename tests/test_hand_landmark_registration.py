import pytest

from backend.hand_landmark_registration import (
    LandmarkPair,
    assess_landmark_registration,
    promote_verified,
)
from backend.spatial_registration_contract import RegistrationStatus


SOURCE = "human-skin-spatial-census"


def pairs():
    return [
        LandmarkPair("A", (0.0, 0.0), (10.0, 20.0), "img-a"),
        LandmarkPair("B", (10.0, 0.0), (30.0, 20.0), "img-b"),
        LandmarkPair("C", (0.0, 10.0), (10.0, 40.0), "img-c"),
        LandmarkPair("D", (10.0, 10.0), (30.0, 40.0), "img-d"),
    ]


def test_landmarks_produce_candidate_transform():
    assessment = assess_landmark_registration(SOURCE, "sample-1", "hand", pairs())
    assert assessment.status is RegistrationStatus.CANDIDATE
    assert assessment.transform is not None
    assert assessment.transform.status is RegistrationStatus.CANDIDATE
    assert assessment.transform.source_frame == "sample_local"
    assert assessment.transform.target_frame == "canonical_hand_2d"
    assert assessment.limitations == ("landmark_rms_error=0.0000",)


def test_too_few_landmarks_remain_unregistered():
    assessment = assess_landmark_registration(SOURCE, "sample-1", "hand", pairs()[:2])
    assert assessment.status is RegistrationStatus.UNREGISTERED
    assert assessment.transform is None


def test_collinear_landmarks_remain_unregistered():
    collinear = [
        LandmarkPair("A", (0.0, 0.0), (0.0, 0.0)),
        LandmarkPair("B", (1.0, 1.0), (1.0, 2.0)),
        LandmarkPair("C", (2.0, 2.0), (2.0, 4.0)),
    ]
    assessment = assess_landmark_registration(SOURCE, "sample-1", "hand", collinear)
    assert assessment.status is RegistrationStatus.UNREGISTERED
    assert "collinear" in assessment.limitations[0]


def test_candidate_cannot_be_promoted_without_anatomical_match():
    assessment = assess_landmark_registration(SOURCE, "sample-1", "hand", pairs())
    with pytest.raises(ValueError, match="anatomical_match"):
        promote_verified(assessment, evidence_ids=["manual-review-1"])


def test_candidate_can_be_verified_only_with_explicit_evidence():
    assessment = assess_landmark_registration(
        SOURCE, "sample-1", "hand", pairs(), anatomical_match=True
    )
    with pytest.raises(ValueError, match="evidence_ids"):
        promote_verified(assessment, evidence_ids=[])

    verified = promote_verified(assessment, evidence_ids=["manual-review-1", "manual-review-1"])
    assert verified.status is RegistrationStatus.VERIFIED
    assert verified.transform is not None
    assert verified.transform.status is RegistrationStatus.VERIFIED
    assert verified.transform.evidence_ids == ("manual-review-1",)
