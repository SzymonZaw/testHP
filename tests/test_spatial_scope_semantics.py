from core.spatial_scope import (
    build_parent_map,
    canonical_parent_id,
    scope_ids,
    split_spatial_scope,
)


def test_direct_hand_regions_are_siblings():
    assert canonical_parent_id("hand/palm") == "hand"
    assert canonical_parent_id("hand/thumb") == "hand"
    assert canonical_parent_id("hand/little") == "hand"

    parents = build_parent_map(
        [
            {"spatial_id": "hand/palm"},
            {"spatial_id": "hand/thumb"},
            {"spatial_id": "hand/little"},
        ]
    )
    assert scope_ids("hand/palm", parents, include_descendants=True) == {"hand/palm"}


def test_recursive_scope_includes_only_descendants():
    items = [
        {"id": "direct", "spatial_id": "hand/palm"},
        {"id": "child", "spatial_id": "hand/palm/thenar"},
        {"id": "grandchild", "spatial_id": "hand/palm/thenar/field-b"},
        {"id": "sibling", "spatial_id": "hand/thumb"},
        {"id": "ancestor", "spatial_id": "hand"},
    ]

    direct, descendants = split_spatial_scope(
        items,
        "hand/palm",
        include_descendants=True,
    )

    assert [item["id"] for item in direct] == ["direct"]
    assert {item["id"] for item in descendants} == {"child", "grandchild"}


def test_biological_level_is_a_filter_not_spatial_identity():
    items = [
        {"id": "cell-palm", "spatial_id": "hand/palm", "biological_level": "cellular"},
        {"id": "cell-thumb", "spatial_id": "hand/thumb", "biological_level": "cellular"},
        {"id": "tissue-field", "spatial_id": "hand/palm/thenar/field-a", "biological_level": "tissue"},
    ]

    direct, descendants = split_spatial_scope(
        items,
        "hand/palm",
        include_descendants=True,
    )

    scoped = direct + descendants
    assert {item["id"] for item in scoped} == {"cell-palm", "tissue-field"}
    assert sum(item["biological_level"] == "cellular" for item in scoped) == 1
    assert sum(item["biological_level"] == "tissue" for item in scoped) == 1


def test_include_descendants_false_is_exact_match_only():
    items = [
        {"id": "direct", "spatial_id": "hand/palm"},
        {"id": "child", "spatial_id": "hand/palm/thenar"},
    ]

    direct, descendants = split_spatial_scope(
        items,
        "hand/palm",
        include_descendants=False,
    )

    assert [item["id"] for item in direct] == ["direct"]
    assert descendants == []
