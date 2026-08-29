from backend.future_state import FutureState
from backend.intervention_scenario import InterventionScenario


def test_future_state_projects_scenario():
    scenario = InterventionScenario(
        name="hypothetical_recovery",
        baseline_health=0.80,
        baseline_function=0.90,
        health_delta=0.08,
        function_delta=0.03,
    )
    state = FutureState.from_scenario(scenario, horizon_years=5, uncertainty=0.05)

    assert state.scenario_name == "hypothetical_recovery"
    assert state.horizon_years == 5.0
    assert state.projected_health == 0.88
    assert state.projected_function == 0.93
    assert state.uncertainty == 0.05
    assert state.evidence["baseline_health"] == 0.80


def test_future_state_normalizes_invalid_horizon():
    scenario = InterventionScenario(
        name="baseline",
        baseline_health=0.70,
        baseline_function=0.80,
    )

    state = FutureState.from_scenario(scenario, horizon_years=-3)

    assert state.horizon_years == 0.0
