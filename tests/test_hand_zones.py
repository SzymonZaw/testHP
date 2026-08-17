from backend.hand_zones import assign_feature_to_zone, zone_layout


def test_zone_layout_is_deterministic():
    zones = zone_layout(900, 600)
    assert len(zones) == 9
    assert zones[0]["zone_id"] == "hand-zone-01"
    assert zones[-1]["zone_id"] == "hand-zone-09"
    assert zones[4]["bbox"] == {"x": 300, "y": 200, "width": 300, "height": 200}


def test_feature_maps_to_zone():
    assert assign_feature_to_zone(100, 100, 900, 600) == "hand-zone-01"
    assert assign_feature_to_zone(450, 300, 900, 600) == "hand-zone-05"
    assert assign_feature_to_zone(899, 599, 900, 600) == "hand-zone-09"
    assert assign_feature_to_zone(-1, 10, 900, 600) is None
