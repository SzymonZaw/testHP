from research.predictive_twin import (
    CellAgeModel,
    CellHealthModel,
    CellState,
    ClinicalValidationPlan,
    LongHorizonPredictor,
    MechanisticSimulator,
    MechanisticState,
    RejuvenationPlanner,
    WholeBodyTwin,
)


def test_cell_health_is_explicitly_research_only():
    state = CellState("c1", {"morphology": 0.9, "viability": 0.8}, confidence=0.9)
    result = CellHealthModel().assess(state)
    assert result.status == "research_favorable"
    assert result.validated is False


def test_cell_age_requires_all_calibration_signals():
    model = CellAgeModel({"clock_a": 40.0, "clock_b": 20.0})
    state = CellState("c1", age_signals={"clock_a": 1.0}, confidence=0.8)
    result = model.estimate(state)
    assert result.biological_age is None
    assert result.missing_signals == ("clock_b",)


def test_mechanistic_simulation_preserves_bounds():
    initial = MechanisticState(function=0.9, damage=0.1, repair=0.8, senescence=0.05)
    result = MechanisticSimulator().step(initial, 10)
    assert all(0.0 <= x <= 1.0 for x in (result.function, result.damage, result.repair, result.senescence))


def test_long_horizon_prediction_is_marked_unvalidated():
    initial = MechanisticState(0.9, 0.1, 0.8, 0.05)
    prediction = LongHorizonPredictor(MechanisticSimulator()).predict(initial, 100)
    assert prediction.horizon_years == 100
    assert prediction.validated is False


def test_rejuvenation_planner_ranks_without_prescribing():
    ranked = RejuvenationPlanner().rank([
        {"node_id": "tissue-a", "priority": 0.4, "confidence": 0.8, "action": "monitor"},
        {"node_id": "cell-b", "priority": 0.9, "confidence": 0.7, "action": "research_candidate"},
    ])
    assert [x.node_id for x in ranked] == ["cell-b", "tissue-a"]


def test_whole_body_twin_supports_hierarchy():
    twin = WholeBodyTwin()
    twin.add_node("body", level="organism")
    twin.add_node("hand-r", parent_id="body", level="organ")
    twin.add_node("cell-1", parent_id="hand-r", level="cell")
    assert twin.descendants("body") == ("hand-r", "cell-1")


def test_validation_plan_is_staged():
    plan = ClinicalValidationPlan()
    assert plan.next_phase([]) == "analytical_validation"
    assert plan.next_phase(plan.phases[:3]) == "prospective_validation"
