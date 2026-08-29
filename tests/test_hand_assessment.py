from backend.change_relationship import ChangeRelationship
from backend.function_trajectory import FunctionTrajectory
from backend.hand_assessment import HandAssessment
from backend.hand_trajectory import HandTrajectory
from backend.hand_state import HandState
from backend.health_trajectory import HealthTrajectory
from backend.longitudinal_hand_twin import LongitudinalHandTwin
from backend.region_trajectory import RegionTrajectory


def make_twin():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(
        HandState(
            hand_id="hand-1",
            biological_age=70,
            cell_count=100,
            health_distribution={"healthy": 95, "abnormal": 5},
            function_distribution={"normal": 95, "impaired": 5},
        ),
        "2026-01-01T00:00:00+00:00",
    )
    twin.add_observation(
        HandState(
            hand_id="hand-1",
            biological_age=72,
            cell_count=98,
            health_distribution={"healthy": 90, "abnormal": 10},
            function_distribution={"normal": 90, "impaired": 10},
        ),
        "2027-01-01T00:00:00+00:00",
    )
    return twin


def build_assessment(twin, regions=()):
    health = HealthTrajectory.from_twin(twin)
    function = FunctionTrajectory.from_twin(twin)
    relationship = ChangeRelationship.from_trajectories(health, function)
    return HandAssessment.from_trajectories(
        HandTrajectory.from_twin(twin), health, function, relationship, regions
    )


def test_assessment_reports_observation_when_signals_change():
    assessment = build_assessment(make_twin())

    assert assessment.overall_status == "observe"
    assert assessment.health_signal == "changing"
    assert assessment.function_signal == "changing"
    assert assessment.ageing_signal == "accelerated_change"


def test_assessment_reports_insufficient_data():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    assessment = build_assessment(twin)

    assert assessment.overall_status == "insufficient_data"
    assert assessment.ageing_signal == "insufficient_data"
    assert assessment.health_signal == "insufficient_data"
    assert assessment.function_signal == "insufficient_data"


def test_assessment_reports_stable_state():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    state = HandState(
        hand_id="hand-1",
        biological_age=70,
        cell_count=100,
        health_distribution={"healthy": 100},
        function_distribution={"normal": 100},
    )
    twin.add_observation(state, "2026-01-01T00:00:00+00:00")
    twin.add_observation(state, "2027-01-01T00:00:00+00:00")

    assessment = build_assessment(twin)

    assert assessment.overall_status == "stable"
    assert assessment.health_signal == "stable"
    assert assessment.function_signal == "stable"


def test_assessment_identifies_changed_regions():
    twin = make_twin()
    region = RegionTrajectory(
        region_id="thumb",
        points=(),
    )

    assessment = build_assessment(twin, (region,))

    assert assessment.affected_regions == ()
    assert assessment.evidence["region_count"] == 1
