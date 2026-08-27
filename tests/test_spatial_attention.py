from backend.spatial_attention import build_spatial_attention_map


def test_spatial_attention_map_uses_observed_cell_positions():
    result = build_spatial_attention_map(
        [{"zone_id": "t1", "level": "tissue", "metric": "age", "score": 0.8, "status": "high_attention"}],
        cell_positions={
            "c1": {"x": 10, "y": 20, "z": 30},
            "c2": {"x": 14, "y": 22, "z": 32},
        },
        zone_cells={"t1": ("c1", "c2")},
    )
    assert result[0]["centroid"] == (12.0, 21.0, 31.0)
    assert result[0]["source_cell_ids"] == ("c1", "c2")
    assert result[0]["score"] == 0.8


def test_spatial_map_omits_zones_without_observed_cells():
    result = build_spatial_attention_map(
        [{"zone_id": "missing", "level": "tissue", "metric": "age", "score": 1.0}],
        cell_positions={}, zone_cells={"missing": ("unknown",)},
    )
    assert result == []
