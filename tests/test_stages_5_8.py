from backend.stages_5_8 import _normalize_observations, _slope


def test_normalize_observations_uses_explicit_age():
    result = _normalize_observations([
        {"timepoint": "T0", "biological_age": 44},
        {"timepoint": "T1", "biological_age": 45},
    ])
    assert [x["age"] for x in result] == [44.0, 45.0]


def test_slope_is_positive_for_increasing_trajectory():
    observations = [
        {"timepoint": "T0", "age": 44},
        {"timepoint": "T1", "age": 45},
        {"timepoint": "T2", "age": 47},
    ]
    assert _slope(observations) > 0


def test_insufficient_history_is_not_fabricated():
    assert _slope([{"timepoint": "T0", "age": 44}]) is None
