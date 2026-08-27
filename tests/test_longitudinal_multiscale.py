from backend.longitudinal import compare_observations


def test_cell_biological_age_trend_across_timepoints():
    observations = [
        {"subject_id": "s1", "zone": "cell:c1", "metric": "biological_age_years", "timepoint": "T0", "value": 41.0},
        {"subject_id": "s1", "zone": "cell:c1", "metric": "biological_age_years", "timepoint": "T1", "value": 42.5},
        {"subject_id": "s1", "zone": "cell:c1", "metric": "biological_age_years", "timepoint": "T2", "value": 44.0},
    ]
    result = compare_observations("s1", observations)
    assert result == [{
        "subject_id": "s1", "zone": "cell:c1", "metric": "biological_age_years",
        "timepoints": ["T0", "T1", "T2"], "values": [41.0, 42.5, 44.0],
        "delta": 3.0, "status": "observed_change",
    }]


def test_missing_timepoints_are_not_called_stable():
    result = compare_observations("s1", [{
        "subject_id": "s1", "zone": "cell:c1", "metric": "biological_age_years", "timepoint": "T0", "value": 41.0,
    }])
    assert result[0]["status"] == "insufficient_timepoints"
    assert result[0]["delta"] is None


def test_cell_state_can_be_tracked_as_numeric_score_without_boolean_coercion():
    observations = [
        {"subject_id": "s1", "zone": "cell:c1", "metric": "stress_score", "timepoint": "T0", "value": 0.1},
        {"subject_id": "s1", "zone": "cell:c1", "metric": "stress_score", "timepoint": "T1", "value": 0.4},
    ]
    result = compare_observations("s1", observations)
    assert result[0]["delta"] == 0.3
    assert result[0]["status"] == "observed_change"
