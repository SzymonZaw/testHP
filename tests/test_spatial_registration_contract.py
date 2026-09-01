import pytest

from backend.spatial_registration_contract import (
    RegistrationAssessment,
    RegistrationStatus,
    SpatialTransform,
)


def test_candidate_registration_can_exist_without_transform():
    assessment = RegistrationAssessment(
        source_id="human-skin-spatial-census",
        source_region="elbow",
        target_region="hand",
        status=RegistrationStatus.CANDIDATE,
        anatomical_match=False,
        limitations=("No verified hand registration transform.",),
    )
    assert assessment.to_dict()["transform"] is None


def test_verified_registration_requires_evidence_and_transform():
    transform = SpatialTransform(
        transform_id="t-001",
        source_frame="sample_local",
        target_frame="nih_hand_template",
        matrix=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        method="validated_affine",
        status=RegistrationStatus.VERIFIED,
        evidence_ids=("registration-landmarks-001",),
    )
    assessment = RegistrationAssessment(
        source_id="human-skin-spatial-census",
        source_region="palm",
        target_region="palm",
        status=RegistrationStatus.VERIFIED,
        transform=transform,
        anatomical_match=True,
        limitations=(),
    )
    assert assessment.to_dict()["status"] == "verified"


def test_verified_registration_without_evidence_is_rejected():
    transform = SpatialTransform(
        transform_id="t-002",
        source_frame="sample_local",
        target_frame="nih_hand_template",
        matrix=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        method="validated_affine",
        status=RegistrationStatus.VERIFIED,
    )
    with pytest.raises(ValueError, match="evidence_ids"):
        transform.validate()
