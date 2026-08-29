from backend.intervention_scenario import InterventionScenario


def test_scenario_projects_expected_deltas():
    scenario = InterventionScenario(
        name="hypothetical_recovery",
        baseline_health=0.80,
        baseline_function=0.90,
        health_delta=0.08,
        function_delta=0.03,
    )

    assert scenario.projected_health == 0.88
    assert scenario.projected_function == 0.93
    assert scenario.expected_delta == {"health": 0.08, "function": 0.03}


def test_projection_is_clamped_to_valid_range():
    scenario = InterventionScenario(
        name="bounded",
        baseline_health=0.95,
        baseline_function=0.05,
        health_delta=0.20,
        function_delta=-0.20,
    )

    assert scenario.projected_health == 1.0
    assert scenario.projected_function == 0.0


def test_zero_delta_preserves_baseline():
    scenario = InterventionScenario(
        name="baseline",
        baseline_health=0.75,
        baseline_function=0.85,
    )

    assert scenario.projected_health == 0.75
    assert scenario.projected_function == 0.85
    assert scenario.expected_delta == {"health": 0.0, "function": 0.0}
