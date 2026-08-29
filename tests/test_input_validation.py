from core.input_validation import (
    EvidenceStatus,
    ModalityStatus,
    artifact_id,
    validate_user_input_package,
)


def package(*inputs):
    return {
        "subject": {"subject_id": "subject-1"},
        "acquisition": {
            "timepoint_id": "T0",
            "acquisition_time": "2026-08-29T10:00:00Z",
            "anatomical_site": "hand",
            "laterality": "right",
        },
        "inputs": list(inputs),
    }


def image_input():
    return {
        "input_id": "img-1",
        "kind": "hand_images",
        "uri": "uploads/hand/front.jpg",
        "format": "jpg",
        "provenance": {"source_type": "user"},
    }


def test_valid_package_reports_available_and_missing_without_inference():
    report = validate_user_input_package(package(image_input()))

    assert report.valid is True
    assert report.evidence_status == EvidenceStatus.OBSERVED
    assert report.modalities["hand_images"].status == ModalityStatus.AVAILABLE
    assert report.modalities["genomics"].status == ModalityStatus.MISSING
    assert report.modalities["tissue_wsi"].status == ModalityStatus.MISSING
    assert "genomics" in report.missing_modalities
    assert "hand_images" in report.available_modalities


def test_invalid_input_is_never_marked_available():
    bad = image_input()
    bad["provenance"] = {}
    report = validate_user_input_package(package(bad))

    assert report.valid is False
    assert report.modalities["hand_images"].status == ModalityStatus.INVALID
    assert report.evidence_status == EvidenceStatus.UNAVAILABLE
    assert report.modalities["hand_images"].input_ids == ()


def test_ground_truth_is_distinguished_from_observation():
    gt = {
        "input_id": "gt-1",
        "kind": "ground_truth",
        "uri": "labels/pathology.json",
        "format": "json",
        "provenance": {"source_type": "clinical", "source_id": "pathology-report-1"},
    }
    report = validate_user_input_package(package(image_input(), gt))

    assert report.valid is True
    assert report.evidence_status == EvidenceStatus.GROUND_TRUTH
    assert report.modalities["ground_truth"].status == ModalityStatus.AVAILABLE


def test_validator_does_not_open_declared_uri():
    item = image_input()
    item["uri"] = "this/file/does/not/exist.jpg"
    report = validate_user_input_package(package(item))

    assert report.valid is True
    assert report.modalities["hand_images"].status == ModalityStatus.AVAILABLE


def test_artifact_id_is_deterministic():
    assert artifact_id("uploads/hand/front.jpg") == "artifact:uploads/hand/front.jpg"
