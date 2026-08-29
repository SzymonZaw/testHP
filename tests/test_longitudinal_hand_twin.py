from backend.hand_state import HandState
from backend.longitudinal_hand_twin import HandObservation, LongitudinalHandTwin


def state(hand_id, age):
    return HandState(hand_id=hand_id, biological_age=age, cell_count=1)


def test_twin_keeps_historical_observations():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    first = twin.add_observation(state("hand-1", 70), "2026-01-01T00:00:00+00:00")
    second = twin.add_observation(state("hand-1", 72), "2027-01-01T00:00:00+00:00")

    assert twin.latest is second
    assert len(twin.observations) == 2
    assert twin.observations[0] is first
    assert twin.biological_age_trend() == [
        ("2026-01-01T00:00:00+00:00", 70),
        ("2027-01-01T00:00:00+00:00", 72),
    ]


def test_twin_orders_observations_by_timestamp():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(state("hand-1", 72), "2027-01-01T00:00:00+00:00")
    twin.add_observation(state("hand-1", 70), "2026-01-01T00:00:00+00:00")

    assert [item.state.biological_age for item in twin.observations] == [70, 72]


def test_twin_rejects_state_from_another_hand():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    try:
        twin.add_observation(state("hand-2", 70), "2026-01-01T00:00:00+00:00")
    except ValueError as exc:
        assert "different hand" in str(exc)
    else:
        raise AssertionError("states from another hand must be rejected")


def test_twin_supports_observations_without_biological_age():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(state("hand-1", None), "2026-01-01T00:00:00+00:00")

    assert twin.latest is not None
    assert twin.biological_age_trend() == []


def test_hand_observation_is_explicit_value_object():
    observation = HandObservation(
        "2026-01-01T00:00:00+00:00",
        state("hand-1", 70),
    )

    assert observation.state.hand_id == "hand-1"
