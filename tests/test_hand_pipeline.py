from __future__ import annotations

from backend.hand_pipeline import build_measurements, longitudinal_changes, quality_report, zone_map


def _analysis():
    return {
        "results": [{
            "source_file": "own_cohort/1.jpg",
            "image": {"width": 600, "height": 450, "mean_brightness": 150.0, "contrast": 35.0},
            "hand_count": 1,
            "hands": [{
                "laterality": "right",
                "handedness_confidence": 0.97,
                "bbox": {"area_ratio": 0.21},
                "landmarks": [{"index": i, "x": 0.1, "y": 0.2, "z": 0.0} for i in range(21)],
                "zones": {
                    "index": {"centroid_x": 0.4, "centroid_y": 0.3, "span_x": 0.1, "span_y": 0.2, "centerline_length_3d_norm": 0.2},
                    "palm": {"centroid_x": 0.5, "centroid_y": 0.5},
                },
            }],
        }]
    }


def test_stage21_creates_core_measurements():
    measurements = build_measurements(_analysis(), "subject-1", "T0")
    assert measurements
    assert all(item.subject_id == "subject-1" for item in measurements)
    assert all(item.modality == "hand" for item in measurements)
    assert any(item.biomarker.name == "centroid_x" for item in measurements)


def test_stage22_quality_is_transparent():
    measurements = build_measurements(_analysis(), "subject-1", "T0")
    quality = quality_report(measurements)
    assert len(quality) == len(measurements)
    assert all("score" in item and "flags" in item for item in quality)
    assert all(0.0 <= item["score"] <= 1.0 for item in quality)


def test_stage23_has_stable_zones():
    measurements = build_measurements(_analysis(), "subject-1", "T0")
    zones = zone_map(measurements)
    assert set(zones) == {"wrist", "palm", "thumb", "index", "middle", "ring", "little"}
    assert zones["index"]["measurements"]
    assert zones["palm"]["measurements"]


def test_stage24_compares_only_same_zone_and_metric():
    baseline = build_measurements(_analysis(), "subject-1", "T0")
    current = build_measurements(_analysis(), "subject-1", "T1")
    current[0].value = float(current[0].value) + 10
    changes = longitudinal_changes(baseline, current)
    assert changes
    assert all(item["result_type"] == "observed_change" for item in changes)
    assert all(item["interpretation"] == "not established" for item in changes)
