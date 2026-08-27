from datetime import datetime, timedelta

from digital_twin.biological_age_model import estimate_biological_age
from digital_twin.aging_deviation import build_aging_deviation
from digital_twin.temporal_aging_deviation import analyze_temporal_aging_deviation
from digital_twin.temporal_aging_map import build_temporal_aging_map


def test_biological_age_estimate_aggregates_markers():
    estimate = estimate_biological_age(50, [52, 56, 54], confidence=0.8)
    assert estimate.biological_age == 54
    assert estimate.age_acceleration == 4
    assert estimate.confidence == 0.8
    assert estimate.uncertainty == 0.2
    assert estimate.marker_count == 3


def test_biological_age_empty_markers_stays_unknown():
    estimate = estimate_biological_age(50, [], confidence=0.9)
    assert estimate.biological_age is None
    assert estimate.age_acceleration is None
    assert estimate.marker_count == 0


def test_aging_deviation_classification_respects_confidence():
    item = build_aging_deviation("region", "thumb", 50, 61, 0.9)
    assert item.deviation == 11
    assert item.severity == "significant"

    uncertain = build_aging_deviation("region", "index", 50, 61, 0.4)
    assert uncertain.severity == "insufficient"


def test_temporal_deviation_detects_increasing_persistent_signal():
    base = datetime(2026, 1, 1)
    points = [
        {"observed_at": base.isoformat(), "deviation": 6, "confidence": 0.8},
        {"observed_at": (base + timedelta(days=30)).isoformat(), "deviation": 9, "confidence": 0.9},
    ]
    result = analyze_temporal_aging_deviation("thumb", points)
    assert result.direction == "increasing"
    assert result.persistence == "persistent"
    assert result.change == 3
    assert result.confidence == 0.85


def test_temporal_map_ranks_and_filters_nodes():
    base = datetime(2026, 1, 1)
    nodes = [
        {"identifier": "thumb", "points": [
            {"observed_at": base.isoformat(), "deviation": 6, "confidence": 0.9},
            {"observed_at": (base + timedelta(days=30)).isoformat(), "deviation": 10, "confidence": 0.9},
        ]},
        {"identifier": "index", "points": []},
    ]
    result = build_temporal_aging_map(nodes)
    assert result["ranked"][0]["identifier"] == "thumb"
    assert result["persistent"][0]["identifier"] == "thumb"
    assert result["increasing"][0]["identifier"] == "thumb"
    assert result["items"][1]["persistence"] == "insufficient"
