from core.spatial_scope import build_parent_map, split_spatial_scope


def test_top_level_hand_regions_are_siblings():
    items = [
        {"spatial_id": "hand/palm"},
        {"spatial_id": "hand/thumb"},
        {"spatial_id": "hand/palm/thenar-eminence"},
        {"spatial_id": "hand/thumb/field-a"},
    ]
    direct, descendants = split_spatial_scope(items, "hand/palm", include_descendants=True)
    assert [item["spatial_id"] for item in direct] == ["hand/palm"]
    assert [item["spatial_id"] for item in descendants] == ["hand/palm/thenar-eminence"]


def test_same_biological_level_does_not_cross_spatial_nodes():
    items = [
        {"spatial_id": "hand/palm/field-a", "biological_level": "cellular"},
        {"spatial_id": "hand/palm/field-b", "biological_level": "cellular"},
        {"spatial_id": "hand/thumb/field-a", "biological_level": "cellular"},
    ]
    direct, descendants = split_spatial_scope(items, "hand/palm/field-a", include_descendants=True)
    assert [item["spatial_id"] for item in direct] == ["hand/palm/field-a"]
    assert descendants == []


def test_recursive_scope_follows_parent_chain():
    items = [
        {"spatial_id": "hand/palm"},
        {"spatial_id": "hand/palm/thenar-eminence"},
        {"spatial_id": "hand/palm/thenar-eminence/field-b"},
        {"spatial_id": "hand/palm/thenar-eminence/field-b/cell-3"},
    ]
    parents = build_parent_map(items)
    assert parents["hand/palm"] == "hand"
    assert parents["hand/palm/thenar-eminence"] == "hand/palm"
    assert parents["hand/palm/thenar-eminence/field-b"] == "hand/palm/thenar-eminence"
    direct, descendants = split_spatial_scope(items, "hand/palm", include_descendants=True)
    assert len(direct) == 1
    assert {item["spatial_id"] for item in descendants} == {
        "hand/palm/thenar-eminence",
        "hand/palm/thenar-eminence/field-b",
        "hand/palm/thenar-eminence/field-b/cell-3",
    }


def test_include_descendants_false_keeps_only_selected_node():
    items = [
        {"spatial_id": "hand/palm"},
        {"spatial_id": "hand/palm/field-a"},
        {"spatial_id": "hand/palm/field-a/cell-1"},
    ]
    direct, descendants = split_spatial_scope(items, "hand/palm", include_descendants=False)
    assert [item["spatial_id"] for item in direct] == ["hand/palm"]
    assert descendants == []


def test_siblings_are_never_descendants_of_each_other():
    items = [
        {"spatial_id": "hand/palm/field-a", "biological_level": "cellular"},
        {"spatial_id": "hand/palm/field-b", "biological_level": "cellular"},
        {"spatial_id": "hand/palm/field-a/cell-1", "biological_level": "cellular"},
    ]
    direct, descendants = split_spatial_scope(items, "hand/palm/field-b", include_descendants=True)
    assert [item["spatial_id"] for item in direct] == ["hand/palm/field-b"]
    assert descendants == []


def test_parent_map_materializes_missing_intermediate_nodes():
    parents = build_parent_map([{"spatial_id": "hand/palm/thenar-eminence/field-b/cell-3"}])
    assert parents["hand/palm/thenar-eminence/field-b/cell-3"] == "hand/palm/thenar-eminence/field-b"
    assert parents["hand/palm/thenar-eminence/field-b"] == "hand/palm/thenar-eminence"
    assert parents["hand/palm/thenar-eminence"] == "hand/palm"
    assert parents["hand/palm"] == "hand"
