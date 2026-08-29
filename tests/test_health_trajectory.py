from backend.hand_state import HandState
from backend.health_trajectory import HealthTrajectory
from backend.longitudinal_hand_twin import LongitudinalHandTwin


def make_state(health):
    return HandState(hand_id="hand-1", cell_count=sum(health.values()), health_distribution=health)


def test_health_trajectory_tracks_fraction_changes():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(make_state({"healthy": 92, "abnormal": 6, "diseased": 2}), "2026-01-01T00:00:00+00:00")
    twin.add_observation(make_state({"healthy": 79, "abnormal": 14, "diseased": 7}), "2028-01-01T00:00:00+00:00")

    trajectory = HealthTrajectory.from_twin(twin)

    assert trajectory.latest is not None
    assert trajectory.latest.health_fractions["healthy"] == 0.79
    assert trajectory.fraction_delta("healthy") == -0.13
    assert trajectory.fraction_delta("diseased") == 0.05


def test_missing_health_state_counts_as_zero():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(make_state({"healthy": 10}), "2026-01-01T00:00:00+00:00")
    twin.add_observation(make_state({"healthy": 9, "diseased": 1}), "2027-01-01T00:00:00+00:00")

    trajectory = HealthTrajectory.from_twin(twin)

    assert trajectory.fraction_delta("diseased") == 0.1


def test_empty_trajectory_has_no_latest_point():
    trajectory = HealthTrajectory(())

    assert trajectory.latest is None
    assert trajectory.first is None
    assert trajectory.fraction_delta("healthy") is None
