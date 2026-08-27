from backend.attention_map import build_attention_map


def test_attention_map_prioritises_changed_zones():
    result = build_attention_map([
        {"zone_id": "t1", "level": "tissue", "metric": "age", "cell_count": 10, "changed_cells": 9, "mean_delta": 5.0},
        {"zone_id": "t2", "level": "tissue", "metric": "age", "cell_count": 10, "changed_cells": 1, "mean_delta": 0.2},
    ])
    assert result[0]["zone_id"] == "t1"
    assert result[0]["status"] == "high_attention"
    assert 0.0 <= result[0]["score"] <= 1.0
    assert result[1]["status"] == "monitor"


def test_attention_map_does_not_make_diagnostic_claims():
    result = build_attention_map([
        {"zone_id": "skin", "level": "anatomy", "metric": "stress", "cell_count": 2, "changed_cells": 1, "mean_delta": 2.0},
    ])
    assert result[0]["status"] == "attention"
    assert "diagnosis" not in result[0]
    assert "treatment" not in result[0]
