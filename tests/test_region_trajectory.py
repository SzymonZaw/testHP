from backend.anatomical_region_state import AnatomicalRegionState
from backend.hand_state import HandState
from backend.longitudinal_hand_twin import LongitudinalHandTwin
from backend.region_trajectory import RegionTrajectory


def make_region(region_id, age, cells, confidence, health=None, function=None):
    return AnatomicalRegionState(
        region_id=region_id,
        name=region_id,
        cell_count=cells,
        biological_age=age,
        confidence=confidence,
        health_distribution=health or {"healthy": cells},
        function_distribution=function or {"normal": cells},
    )


def make_state(age, cells, confidence, region):
    state = HandState(hand_id="hand-1", biological_age=age, cell_count=cells, confidence=confidence)
    state.anatomical_regions = {region.region_id: region}
    return state


def test_region_trajectory_tracks_one_region_across_hand_observations():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(
        make_state(70, 100, 0.8, make_region("thumb", 68, 40, 0.8)),
        "2026-01-01T00:00:00+00:00",
    )
    twin.add_observation(
        make_state(72, 95, 0.9, make_region("thumb", 71, 35, 0.9)),
        "2027-01-01T00:00:00+00:00",
    )

    trajectory = RegionTrajectory.from_twin(twin, "thumb")

    assert len(trajectory.points) == 2
    assert trajectory.age_delta == 3
    assert trajectory.cell_count_delta == -5
    assert trajectory.confidence_delta == 0.09999999999999998
    assert abs(trajectory.ageing_rate() - 3.0) < 0.01


def test_region_trajectory_ignores_observations_without_that_region():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(
        make_state(70, 100, 0.8, make_region("thumb", 68, 40, 0.8)),
        "2026-01-01T00:00:00+00:00",
    )
    twin.add_observation(
        HandState(hand_id="hand-1", biological_age=72, cell_count=95, confidence=0.9),
        "2027-01-01T00:00:00+00:00",
    )

    trajectory = RegionTrajectory.from_twin(twin, "thumb")

    assert len(trajectory.points) == 1
    assert trajectory.age_delta is None
    assert trajectory.ageing_rate() is None


def test_region_trajectory_preserves_health_and_function_snapshots():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    first = make_region("palm", 70, 10, 0.8, {"healthy": 8, "abnormal": 2}, {"normal": 9, "reduced": 1})
    second = make_region("palm", 72, 9, 0.7, {"healthy": 6, "abnormal": 3}, {"normal": 7, "reduced": 2})
    twin.add_observation(make_state(70, 10, 0.8, first), "2026-01-01T00:00:00+00:00")
    twin.add_observation(make_state(72, 9, 0.7, second), "2027-01-01T00:00:00+00:00")

    trajectory = RegionTrajectory.from_twin(twin, "palm")

    assert trajectory.points[0].health_distribution == {"healthy": 8, "abnormal": 2}
    assert trajectory.points[1].health_distribution == {"healthy": 6, "abnormal": 3}
    assert trajectory.points[0].function_distribution == {"normal": 9, "reduced": 1}
    assert trajectory.points[1].function_distribution == {"normal": 7, "reduced": 2}
