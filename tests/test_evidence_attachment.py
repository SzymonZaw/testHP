import pytest

from backend.data_foundation import Provenance, Quality, SpatialReference
from backend.evidence_attachment import EvidenceAttachment


def make_attachment(**overrides):
    values = dict(
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
            "hand-frame:T0",
            "registered",
            anatomical_target="hand/palm",
            transform={"type": "identity", "version": "1"},
        ),
        provenance=Provenance(source_object_ids=("slide-1",), method="test"),
        quality=Quality(status="acceptable", score=0.95),
    )
    values.update(overrides)
    return EvidenceAttachment(**values)


def test_attachment_requires_registered_reference():
    attachment = make_attachment(
        spatial_reference=SpatialReference("hand-frame:T0", "unregistered")
    )
    with pytest.raises(ValueError, match="registered spatial reference"):
        attachment.validate()


def test_attachment_serializes_complete_spatial_context():
    payload = make_attachment().to_dict()
    assert payload["spatial_node_id"] == "cell-1"
    assert payload["spatial_level"] == "cell"
    assert payload["timepoint_id"] == "T0"
    assert payload["spatial_reference"]["registration_status"] == "registered"
    assert payload["provenance"]["source_object_ids"] == ("slide-1",)


def test_candidate_attachment_can_be_unregistered():
    attachment = make_attachment(
        status="candidate",
        spatial_reference=SpatialReference("hand-frame:T0", "unregistered"),
    )
    attachment.validate()
