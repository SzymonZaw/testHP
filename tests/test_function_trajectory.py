from backend.function_trajectory import FunctionTrajectory
from backend.hand_state import HandState
from backend.longitudinal_hand_twin import LongitudinalHandTwin


def make_state(function):
    return HandState(hand_id="hand-1", cell_count=sum(function.values()), function_distribution=function)


def test_function_trajectory_tracks_fraction_changes():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(make_state({"normal": 94, "impaired": 6}), "2026-01-01T00:00:00+00:00")
    twin.add_observation(make_state({"normal": 84, "impaired": 16}), "2028-01-01T00:00:00+00:00")

    trajectory = FunctionTrajectory.from_twin(twin)

    assert trajectory.latest is not None
    assert trajectory.latest.function_fractions["normal"] == 0.84
    assert trajectory.fraction_delta("normal") == -0.10
    assert trajectory.fraction_delta("impaired") == 0.10


def test_missing_function_state_counts_as_zero():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(make_state({"normal": 10}), "2026-01-01T00:00:00+00:00")
    twin.add_observation(make_state({"normal": 9, "impaired": 1}), "2027-01-01T00:00:00+00:00")

    trajectory = FunctionTrajectory.from_twin(twin)

    assert trajectory.fraction_delta("impaired") == 0.1


def test_empty_trajectory_has_no_latest_point():
    trajectory = FunctionTrajectory(())

    assert trajectory.latest is None
    assert trajectory.first is None
    assert trajectory.fraction_delta("normal") is None
