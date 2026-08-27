import pytest

from decision.longitudinal_summary import summarize_trajectories


def test_builds_multiscale_trajectory_and_relative_change():
    result = summarize_trajectories("s1", [
        {"zone": "palm", "metric": "cell_age", "timepoint": "T0", "value": 40},
        {"zone": "palm", "metric": "cell_age", "timepoint": "T1", "value": 42},
        {"zone": "palm", "metric": "cell_age", "timepoint": "T2", "value": 44},
    ])
    assert len(result) == 1
    assert result[0].values == (40.0, 42.0, 44.0)
    assert result[0].delta == 4.0
    assert result[0].relative_delta == pytest.approx(0.1)
    assert result[0].direction == "increased"
    assert result[0].status == "observed_change"


def test_single_timepoint_is_not_interpreted_as_stable():
    result = summarize_trajectories("s1", [
        {"zone": "palm", "metric": "cell_age", "timepoint": "T0", "value": 40},
    ])
    assert result[0].direction == "not_available"
    assert result[0].status == "insufficient_timepoints"


def test_duplicate_measurements_are_rejected():
    with pytest.raises(ValueError):
        summarize_trajectories("s1", [
            {"zone": "palm", "metric": "density", "timepoint": "T0", "value": 1},
            {"zone": "palm", "metric": "density", "timepoint": "T0", "value": 2},
        ])


def test_non_numeric_values_are_ignored():
    result = summarize_trajectories("s1", [
        {"zone": "palm", "metric": "density", "timepoint": "T0", "value": "unknown"},
        {"zone": "palm", "metric": "density", "timepoint": "T1", "value": 2},
    ])
    assert result[0].status == "insufficient_timepoints"
