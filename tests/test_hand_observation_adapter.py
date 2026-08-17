from backend.hand_observation_adapter import evidence_to_artifacts, evidence_to_measurements, evidence_to_observations
from backend.multiscale_pipeline import EvidenceRecord


def _records():
    return [
        EvidenceRecord(
            subject_id="SUBJECT-001",
            source_id="data/raw/hand/own_cohort/T0/front.jpg",
            modality="hand",
            biological_level="macroscopic",
            region_id="hand.skin_regions",
            result_type="observation",
            metric="image_width",
            value=1920,
            unit="px",
            provenance={"timepoint": "T0"},
        ),
        EvidenceRecord(
            subject_id="SUBJECT-001",
            source_id="data/raw/hand/own_cohort/T0/front.jpg",
            modality="hand",
            biological_level="surface",
            region_id="hand.skin_regions",
            result_type="observation",
            metric="mean_brightness",
            value=0.42,
            unit="0-1",
            provenance={"timepoint": "T0"},
        ),
    ]


def test_hand_evidence_maps_to_domain_objects():
    records = _records()
    artifacts = evidence_to_artifacts(records, "T0")
    measurements = evidence_to_measurements(records, "T0")
    observations = evidence_to_observations(records, "T0")

    assert len(artifacts) == 1
    assert len(measurements) == 2
    assert len(observations) == 2
    assert artifacts[0].subject_id == "SUBJECT-001"
    assert measurements[0].timepoint_id == "T0"
    assert observations[0].anatomical_location.id == "hand.skin_regions"
