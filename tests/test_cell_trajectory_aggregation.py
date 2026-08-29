from backend.cell_trajectory_aggregation import aggregate_cell_trajectories
from backend.cell_evidence import CellEvidence
from backend.longitudinal_cells import CellTrajectory, CellTrajectoryPoint


def _trajectory(cell_id: str, *ages: float | None) -> CellTrajectory:
    return CellTrajectory(
        cell_id=cell_id,
        subject_id="s1",
        hand_id="h1",
        points=tuple(
            CellTrajectoryPoint(
                timepoint_id=f"T{i}",
                state="normal",
                state_confidence=0.9,
                biological_age_years=age,
                age_interval=None,
            )
            for i, age in enumerate(ages)
        ),
    )


def test_cell_trajectories_roll_up_to_hand_tissue_and_anatomy_with_provenance():
    result = aggregate_cell_trajectories(
        [_trajectory("c1", 40.0, 42.0), _trajectory("c2", 41.0, 41.0)],
        cell_to_tissue={"c1": "t1", "c2": "t1"},
        tissue_to_anatomy={"t1": "skin"},
    )

    assert [item.to_dict() for item in result] == [
        {
            "zone_id": "h1", "level": "hand", "metric": "biological_age_years",
            "cell_count": 2, "changed_cells": 1, "mean_delta": 1.0,
            "status": "attention", "source_cell_ids": ("c1", "c2"),
            "confidence": 0.9, "uncertainty_interval": None, "evidence_ids": (),
        },
        {
            "zone_id": "skin", "level": "anatomy", "metric": "biological_age_years",
            "cell_count": 2, "changed_cells": 1, "mean_delta": 1.0,
            "status": "attention", "source_cell_ids": ("c1", "c2"),
            "confidence": 0.9, "uncertainty_interval": None, "evidence_ids": (),
        },
        {
            "zone_id": "t1", "level": "tissue", "metric": "biological_age_years",
            "cell_count": 2, "changed_cells": 1, "mean_delta": 1.0,
            "status": "attention", "source_cell_ids": ("c1", "c2"),
            "confidence": 0.9, "uncertainty_interval": None, "evidence_ids": (),
        },
    ]


def test_aggregation_preserves_uncertainty_and_observation_provenance():
    trajectory = CellTrajectory(
        cell_id="c1", subject_id="s1", hand_id="h1",
        points=(
            CellTrajectoryPoint("T1", "normal", 0.95, 40.0, (38.0, 42.0), "obs-1", 0.93,
                                (CellEvidence("microscopy", "marker", value=0.8, observation_id="obs-1"),)),
            CellTrajectoryPoint("T2", "normal", 0.8, 41.0, (39.0, 43.0), "obs-2", 0.91,
                                (CellEvidence("microscopy", "marker", value=0.7, observation_id="obs-2"),)),
        ),
    )
    result = aggregate_cell_trajectories([trajectory], cell_to_tissue={"c1": "t1"}, tissue_to_anatomy={"t1": "skin"})

    assert all(item.confidence == 0.8 for item in result)
    assert all(item.uncertainty_interval == (38.0, 43.0) for item in result)
    assert all(item.evidence_ids == ("obs-1", "obs-2") for item in result)


def test_missing_age_observation_is_not_treated_as_zero_change():
    result = aggregate_cell_trajectories(
        [_trajectory("c1", None, None)],
        cell_to_tissue={"c1": "t1"},
        tissue_to_anatomy={"t1": "skin"},
    )
    assert all(item.mean_delta is None for item in result)
    assert all(item.changed_cells == 0 for item in result)
    assert all(item.status == "insufficient_observation" for item in result)


def test_missing_hierarchy_mapping_fails_closed():
    try:
        aggregate_cell_trajectories([_trajectory("c1", 40.0, 42.0)], cell_to_tissue={}, tissue_to_anatomy={})
    except ValueError as exc:
        assert "missing tissue mapping" in str(exc)
    else:
        raise AssertionError("unmapped cell must not be invented into a tissue")
