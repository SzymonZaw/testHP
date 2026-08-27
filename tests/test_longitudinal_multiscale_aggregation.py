from backend.longitudinal_multiscale import aggregate_cell_trends


def test_cell_trends_roll_up_to_tissue_and_anatomy():
    trends = [
        {"zone": "c1", "metric": "biological_age_years", "delta": 2.0, "status": "observed_change"},
        {"zone": "c2", "metric": "biological_age_years", "delta": 0.0, "status": "stable_observation"},
        {"zone": "c3", "metric": "biological_age_years", "delta": -1.0, "status": "observed_change"},
    ]
    result = aggregate_cell_trends(
        trends,
        cell_to_tissue={"c1": "t1", "c2": "t1", "c3": "t2"},
        tissue_to_anatomy={"t1": "skin", "t2": "skin"},
    )
    assert result == [
        {"zone_id": "skin", "level": "anatomy", "metric": "biological_age_years", "cell_count": 3, "changed_cells": 2, "mean_delta": 1 / 3, "status": "attention"},
        {"zone_id": "t1", "level": "tissue", "metric": "biological_age_years", "cell_count": 2, "changed_cells": 1, "mean_delta": 1.0, "status": "attention"},
        {"zone_id": "t2", "level": "tissue", "metric": "biological_age_years", "cell_count": 1, "changed_cells": 1, "mean_delta": -1.0, "status": "attention"},
    ]


def test_unknown_or_unmapped_cells_are_not_invented_into_a_zone():
    result = aggregate_cell_trends(
        [{"zone": "missing", "metric": "stress_score", "delta": 1.0, "status": "observed_change"}],
        cell_to_tissue={},
        tissue_to_anatomy={},
    )
    assert result == []
