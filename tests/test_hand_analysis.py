from backend.hand_analysis import HandAnalysis
from backend.hand_state import HandState
from backend.intervention_scenario import InterventionScenario
from backend.longitudinal_hand_twin import LongitudinalHandTwin


def make_twin():
    twin = LongitudinalHandTwin("twin-1", "hand-1")
    twin.add_observation(
        HandState(
            hand_id="hand-1", biological_age=70, cell_count=100, confidence=0.8,
            health_distribution={"healthy": 100}, function_distribution={"normal": 100},
        ), "2026-01-01T00:00:00+00:00",
    )
    twin.add_observation(
        HandState(
            hand_id="hand-1", biological_age=71, cell_count=100, confidence=0.9,
            health_distribution={"healthy": 90, "abnormal": 10},
            function_distribution={"normal": 90, "impaired": 10},
        ), "2027-01-01T00:00:00+00:00",
    )
    return twin


def test_analysis_runs_full_pipeline():
    scenario = InterventionScenario("hypothetical_recovery", 0.90, 0.90, 0.05, 0.03)
    analysis = HandAnalysis.from_twin(make_twin(), scenarios=(scenario,), horizon_years=5)

    assert analysis.assessment.overall_status == "observe"
    assert len(analysis.risk_signals) == 2
    assert analysis.risk_model.overall_level in {"moderate", "high"}
    assert len(analysis.scenarios) == 1
    assert len(analysis.future_states) == 1
    assert len(analysis.comparisons) == 1
    assert analysis.future_states[0].horizon_years == 5.0
    assert analysis.decision_support.action in {"monitor", "investigate"}


def test_analysis_without_scenarios_still_produces_decision_support():
    analysis = HandAnalysis.from_twin(make_twin())

    assert analysis.scenarios == ()
    assert analysis.future_states == ()
    assert analysis.comparisons == ()
    assert analysis.decision_support.scenario_name is None
