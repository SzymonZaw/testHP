from backend.intervention_scenario import InterventionScenario
from backend.scenario_comparison import ScenarioComparison


def test_comparison_tracks_projected_deltas():
    scenario = InterventionScenario(
        name="hypothetical_recovery",
        baseline_health=0.80,
        baseline_function=0.90,
        health_delta=0.08,
        function_delta=0.03,
    )
    comparison = ScenarioComparison.from_scenario(scenario)

    assert comparison.health_delta == 0.08
    assert comparison.function_delta == 0.03
    assert comparison.combined_delta == 0.055
    assert comparison.meaningful_change is True


def test_uncertainty_can_make_small_change_not_meaningful():
    scenario = InterventionScenario(
        name="small_change",
        baseline_health=0.80,
        baseline_function=0.90,
        health_delta=0.02,
        function_delta=0.01,
    )
    comparison = ScenarioComparison.from_scenario(scenario, uncertainty=0.05)

    assert comparison.meaningful_change is False


def test_uncertainty_is_bounded():
    scenario = InterventionScenario(
        name="bounded_uncertainty",
        baseline_health=0.50,
        baseline_function=0.50,
    )

    assert ScenarioComparison.from_scenario(scenario, uncertainty=-1).uncertainty == 0.0
    assert ScenarioComparison.from_scenario(scenario, uncertainty=2).uncertainty == 1.0
