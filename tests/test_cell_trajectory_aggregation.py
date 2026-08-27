from backend.biological_state import BiologicalAgeEstimate, Provenance, Uncertainty
from backend.longitudinal_cells import CellTimepointRecord, build_cell_trajectory
from backend.cell_trajectory_aggregation import aggregate_cell_trajectories


def age(cell, subject, hand, timepoint, years):
    return BiologicalAgeEstimate(
        f"age:{cell}:{timepoint}", subject, hand, timepoint, cell, years,
        Uncertainty(kind="test", interval=(years - 1, years + 1)),
        (f"source:{timepoint}",), Provenance(), "2026-08-27T00:00:00+00:00", "test", "1",
    )


def trajectory(cell, values):
    return build_cell_trajectory([
        CellTimepointRecord(cell, "s1", "h1", tp, biological_age=age(cell, "s1", "h1", tp, years))
        for tp, years in values
    ])


def test_trajectories_roll_up_to_tissue_and_anatomy():
    result = aggregate_cell_trajectories(
        [trajectory("c1", [("T0", 40), ("T1", 42)]), trajectory("c2", [("T0", 50), ("T1", 50)]), trajectory("c3", [("T0", 60), ("T1", 59)])],
        cell_to_tissue={"c1": "t1", "c2": "t1", "c3": "t2"},
        tissue_to_anatomy={"t1": "skin", "t2": "skin"},
    )
    assert result[0].to_dict() == {
        "zone_id": "skin", "level": "anatomy", "metric": "biological_age_years",
        "cell_count": 3, "changed_cells": 2, "mean_delta": 1 / 3,
        "status": "attention", "source_cell_ids": ("c1", "c2", "c3"),
    }
    assert result[1].zone_id == "t1"
    assert result[1].mean_delta == 1.0
    assert result[2].zone_id == "t2"
    assert result[2].mean_delta == -1.0


def test_missing_mapping_is_rejected():
    try:
        aggregate_cell_trajectories([trajectory("c1", [("T0", 40), ("T1", 41)])], cell_to_tissue={}, tissue_to_anatomy={})
    except ValueError as exc:
        assert "missing tissue mapping" in str(exc)
    else:
        raise AssertionError("expected missing mapping to be rejected")
