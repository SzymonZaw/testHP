from core.user_input_contract import contract_as_dict, validate_input_manifest


def test_contract_has_images_as_minimum_required_input():
    contract = contract_as_dict()
    assert "hand_images" in contract["required"]
    assert "single_cell_rna" in contract["optional"]
    assert contract["rules"]["absence_of_optional_data_is_not_a_negative_biological_finding"] is True


def test_manifest_requires_hand_image():
    issues = validate_input_manifest({"artifacts": [{"kind": "mp4", "path": "hand/motion.mp4"}]})
    assert any(issue.field == "hand_images" for issue in issues)


def test_valid_minimum_manifest():
    issues = validate_input_manifest({"artifacts": [{"kind": "jpg", "path": "hand/front.jpg"}]})
    assert issues == []


def test_artifact_requires_kind_and_path():
    issues = validate_input_manifest({"artifacts": [{"kind": "jpg"}, {"path": "hand/front.jpg"}]})
    assert len(issues) == 2
