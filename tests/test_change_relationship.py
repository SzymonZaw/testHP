from backend.change_relationship import ChangeRelationship
from backend.function_trajectory import FunctionTrajectory
from backend.hand_state import HandState
from backend.health_trajectory import HealthTrajectory
from backend.longitudinal_hand_twin import LongitudinalHandTwin


def make_twin(first_health, last_health, first_function, last_function):
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(
        HandState(
            hand_id="hand-1",
            cell_count=sum(first_health.values()),
            health_distribution=first_health,
            function_distribution=first_function,
        ),
        "2026-01-01T00:00:00+00:00",
    )
    twin.add_observation(
        HandState(
            hand_id="hand-1",
            cell_count=sum(last_health.values()),
            health_distribution=last_health,
            function_distribution=last_function,
        ),
        "2027-01-01T00:00:00+00:00",
    )
    return twin


def test_health_change_can_exceed_function_change():
    twin = make_twin(
        {"healthy": 92, "abnormal": 8},
        {"healthy": 80, "abnormal": 20},
        {"normal": 94, "impaired": 6},
        {"normal": 93, "impaired": 7},
    )
    relationship = ChangeRelationship.from_trajectories(
        HealthTrajectory.from_twin(twin),
        FunctionTrajectory.from_twin(twin),
    )

    assert relationship.interpretation == "health_change_exceeds_function_change"
    assert relationship.health_deltas["healthy"] == -0.12
    assert relationship.function_deltas["impaired"] == 0.01


def test_function_change_can_exceed_health_change():
    twin = make_twin(
        {"healthy": 95, "abnormal": 5},
        {"healthy": 94, "abnormal": 6},
        {"normal": 95, "impaired": 5},
        {"normal": 70, "impaired": 30},
    )
    relationship = ChangeRelationship.from_trajectories(
        HealthTrajectory.from_twin(twin),
        FunctionTrajectory.from_twin(twin),
    )

    assert relationship.interpretation == "function_change_exceeds_health_change"


def test_stable_trajectories_are_stable():
    twin = make_twin(
        {"healthy": 100},
        {"healthy": 100},
        {"normal": 100},
        {"normal": 100},
    )
    relationship = ChangeRelationship.from_trajectories(
        HealthTrajectory.from_twin(twin),
        FunctionTrajectory.from_twin(twin),
    )

    assert relationship.interpretation == "stable"
    assert relationship.health_change_magnitude == 0
    assert relationship.function_change_magnitude == 0
