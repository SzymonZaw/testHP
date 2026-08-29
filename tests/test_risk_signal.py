from backend.change_relationship import ChangeRelationship
from backend.function_trajectory import FunctionTrajectory
from backend.hand_assessment import HandAssessment
from backend.hand_state import HandState
from backend.hand_trajectory import HandTrajectory
from backend.health_trajectory import HealthTrajectory
from backend.longitudinal_hand_twin import LongitudinalHandTwin


def make_assessment(health_last, function_last):
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(
        HandState(
            hand_id="hand-1",
            biological_age=70,
            cell_count=100,
            confidence=0.8,
            health_distribution={"healthy": 100},
            function_distribution={"normal": 100},
        ),
        "2026-01-01T00:00:00+00:00",
    )
    twin.add_observation(
        HandState(
            hand_id="hand-1",
            biological_age=71,
            cell_count=100,
            confidence=0.9,
            health_distribution=health_last,
            function_distribution=function_last,
        ),
        "2027-01-01T00:00:00+00:00",
    )
    health = HealthTrajectory.from_twin(twin)
    function = FunctionTrajectory.from_twin(twin)
    relationship = ChangeRelationship.from_trajectories(health, function)
    return HandAssessment.from_trajectories(
        HandTrajectory.from_twin(twin), health, function, relationship
    )


def test_health_change_creates_signal():
    from backend.risk_signal import RiskSignal

    assessment = make_assessment({"healthy": 80, "abnormal": 20}, {"normal": 100})
    signals = RiskSignal.from_assessment(assessment)

    assert len(signals) == 1
    assert signals[0].signal_type == "health_change"
    assert signals[0].severity == "high"
    assert signals[0].region is None


def test_function_change_creates_signal():
    from backend.risk_signal import RiskSignal

    assessment = make_assessment({"healthy": 100}, {"normal": 80, "impaired": 20})
    signals = RiskSignal.from_assessment(assessment)

    assert len(signals) == 1
    assert signals[0].signal_type == "function_change"


def test_stable_assessment_creates_no_signals():
    from backend.risk_signal import RiskSignal

    assessment = make_assessment({"healthy": 100}, {"normal": 100})
    signals = RiskSignal.from_assessment(assessment)

    assert signals == ()
