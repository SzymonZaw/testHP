from backend.hand_vision import analyze_own_cohort, observations_from_analysis


def test_empty_own_cohort_is_safe(tmp_path):
    result = analyze_own_cohort(tmp_path)
    assert result["files_found"] == 0
    assert result["files_analyzed"] == 0
    assert result["files_failed"] == 0
    assert result["results"] == []


def test_observations_from_analysis_stays_observed():
    analysis = {
        "results": [{
            "source_file": "1.jpg",
            "image": {"width": 600, "height": 450, "mean_brightness": 120.0, "contrast": 30.0},
            "hand_count": 1,
            "hands": [{
                "laterality": "right",
                "handedness_confidence": 0.98,
                "bbox": {"area_ratio": 0.2},
                "landmarks": [{"index": i, "x": 0.1, "y": 0.1, "z": 0.0} for i in range(21)],
                "zones": {"index": {"centroid_x": 0.4, "centroid_y": 0.3, "centerline_length_3d_norm": 0.2}},
            }],
        }],
    }
    observations = observations_from_analysis(analysis, "subject-1", "session-1", "T0")
    assert observations
    assert all(item["evidence_level"] == "observed" for item in observations)
    assert any(item["zone"] == "index" and item["metric"] == "centroid_x" for item in observations)
    assert not any(item.get("interpretation") for item in observations)
