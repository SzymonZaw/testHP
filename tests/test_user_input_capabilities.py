from core.input_validation import ModalityStatus, validate_user_input_package
from core.user_capabilities import build_user_analysis_plan


def package(*inputs):
    return {
        "schema_version": "user_input_v1",
        "subject": {"subject_id": "user-test"},
        "acquisition": {
            "timepoint_id": "T0",
            "acquisition_time": "2026-08-29T10:30:00Z",
            "laterality": "right",
        },
        "inputs": list(inputs),
    }


def item(kind, input_id="i1"):
    return {
        "input_id": input_id,
        "kind": kind,
        "uri": f"upload://{input_id}",
        "format": "application/octet-stream",
        "provenance": {"source_type": "user"},
    }


def test_hand_image_is_enough_for_hand_structure_only():
    report = validate_user_input_package(package(item("hand_images")))
    assert report.valid
    assert report.modalities["hand_images"].status == ModalityStatus.AVAILABLE
    plan = build_user_analysis_plan(report)
    assert "hand_structure" in plan["available_analyses"]
    assert "genomic_state" in plan["unavailable_analyses"]


def test_missing_modalities_are_not_negative_findings():
    report = validate_user_input_package(package(item("hand_images")))
    plan = build_user_analysis_plan(report)
    assert "genomics" in plan["unavailable_analyses"]
    assert any("not interpreted as negative" in x for x in plan["limitations"])


def test_wsi_enables_tissue_research_but_not_validated_age_clock():
    report = validate_user_input_package(package(item("tissue_wsi")))
    plan = build_user_analysis_plan(report)
    assert "tissue_morphology" in plan["available_analyses"]
    assert "biological_age_research" in plan["available_analyses"]
    assert any("validated biological-age clock" in x for x in plan["limitations"])
