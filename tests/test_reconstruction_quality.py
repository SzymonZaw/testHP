from backend.reconstruction_quality import validate_inputs


def test_quality_gate_requires_two_prepared_views():
    result = validate_inputs([])
    assert result["status"] == "blocked"
    assert result["minimum_views"] == 2
    assert result["prepared_count"] == 0


def test_quality_gate_requires_two_registered_directions():
    records = [
        {"asset_id": "a", "view": "front", "prepared": True, "quality": {"overall": 0.9}, "registration": {"status": "registered", "quality": 0.9}},
        {"asset_id": "b", "view": "front", "prepared": True, "quality": {"overall": 0.9}, "registration": {"status": "registered", "quality": 0.9}},
    ]
    result = validate_inputs(records)
    assert result["status"] == "blocked"
    assert any("different view directions" in error for error in result["errors"])


def test_quality_gate_ready_with_two_views_and_preserves_warning():
    records = [
        {"asset_id": "a", "filename": "front.jpg", "view": "front", "prepared": True, "quality": {"overall": 0.9}, "warnings": [], "registration": {"status": "registered", "quality": 0.9}},
        {"asset_id": "b", "filename": "side.jpg", "view": "side_left", "prepared": True, "quality": {"overall": 0.4}, "warnings": ["review exposure"], "registration": {"status": "registered", "quality": 0.8}},
    ]
    result = validate_inputs(records)
    assert result["status"] == "ready"
    assert result["registered_views"] == ["front", "side_left"]
    assert result["warnings"]
