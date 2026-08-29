from data_contract.user_input_validator_v1 import validate_user_package


def base_package():
    return {
        "subject": {"subject_id": "S1"},
        "acquisition": {
            "timepoint_id": "T0",
            "acquisition_time": "2026-08-29T10:00:00Z",
            "anatomical_site": "hand",
            "laterality": "right",
        },
        "inputs": [],
    }


def test_complete_hand_image_is_accepted():
    package = base_package()
    package["inputs"] = [{
        "input_id": "img1",
        "kind": "hand_images",
        "uri": "file:///hand.png",
        "format": "png",
        "laterality": "right",
        "anatomical_site": "hand",
        "acquisition_time": "2026-08-29T10:00:00Z",
        "provenance": {"source_type": "user"},
    }]
    report = validate_user_package(package)
    assert report.valid_contract
    assert report.ready_for_any_processing
    assert not report.errors


def test_incomplete_wsi_is_reported_without_fabrication():
    package = base_package()
    package["inputs"] = [{
        "input_id": "wsi1",
        "kind": "tissue_wsi",
        "uri": "file:///sample.svs",
        "format": "svs",
        "provenance": {"source_type": "research_dataset"},
    }]
    report = validate_user_package(package)
    assert report.valid_contract
    assert not report.ready_for_any_processing
    assert any(f.code == "INPUT_INCOMPLETE" and "tissue_type" in f.message for f in report.findings)


def test_unknown_modality_is_contract_error():
    package = base_package()
    package["inputs"] = [{
        "input_id": "x",
        "kind": "invented_modality",
        "uri": "file:///x",
        "format": "bin",
        "provenance": {"source_type": "user"},
    }]
    report = validate_user_package(package)
    assert not report.valid_contract
    assert any(f.code == "UNSUPPORTED_KIND" for f in report.errors)
