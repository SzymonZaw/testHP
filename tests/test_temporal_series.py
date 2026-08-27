import pytest

from backend.longitudinal_observation import LongitudinalObservation
from backend.temporal_series import build_temporal_series


def observation(t, value):
    return LongitudinalObservation(
        observation_id=f"o-{t}", subject_id="s1", hand_id="h1", timepoint_id=t,
        zone_id="c1", level="cell", metric="age", value=value,
        cell_id="c1", spatial_reference=f"frame:{t}",
    )


def test_three_timepoints_detect_consistent_increase():
    series = build_temporal_series([observation("T0", 40), observation("T1", 41), observation("T2", 43)])
    assert series.deltas == (1, 2)
    assert series.trend == "increasing"


def test_mixed_changes_are_not_called_increasing():
    series = build_temporal_series([observation("T0", 40), observation("T1", 42), observation("T2", 41)])
    assert series.trend == "changing"


def test_temporal_series_requires_multiple_points():
    with pytest.raises(ValueError, match="two"):
        build_temporal_series([observation("T0", 40)])
