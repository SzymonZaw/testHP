from research.predictive_twin import (
    CellAgeModel,
    CellHealthModel,
    CellState,
    ClinicalValidationPlan,
    LongevityScenarioModel,
    LongHorizonPredictor,
    MechanisticSimulator,
    MechanisticState,
    MolecularState,
    OrganState,
    OrganismState,
    RejuvenationPlanner,
    TissueState,
    WholeBodyTwin,
)


def test_cell_health_is_explicitly_research_only():
    state = CellState("cell-1", health_signals={"morphology": 0.9, "viability": 0.8}, confidence=0.9)
    result = CellHealthModel().assess(state)
    assert result.status == "research_favorable"
    assert result.validated is False


def test_cell_age_requires_all_calibrated_signals():
    model = CellAgeModel({"methylation": 10.0, "expression": 5.0}, intercept=20.0)
    result = model.estimate(CellState("cell-1", age_signals={"methylation": 0.2}, confidence=0.8))
    assert result.biological_age is None
    assert result.missing_signals == ("expression",)


def test_multiscale_state_aggregates_bottom_up():
    cells = (
        CellState("c1", function=0.9, damage=0.1, confidence=0.8),
        CellState("c2", function=0.7, damage=0.3, confidence=0.6),
    )
    tissue = TissueState.from_cells("t1", cells)
    organ = OrganState.from_tissues("o1", (tissue,))
    organism = OrganismState.from_organs("person-1", (organ,))
    assert tissue.function == 0.8
    assert organ.function == 0.8
    assert organism.global_function == 0.8


def test_mechanistic_simulator_produces_multiscale_trace():
    traces = MechanisticSimulator().simulate_multiscale(
        MolecularState(dna_integrity=0.95),
        MechanisticState(function=0.9, damage=0.1, repair=0.8, senescence=0.05),
        years=3,
        tissue_context=0.9,
        organ_context=0.95,
        organism_context=0.98,
    )
    assert len(traces) == 3
    assert traces[-1].organism_function <= 1.0


def test_long_horizon_prediction_exposes_uncertainty():
    predictor = LongHorizonPredictor(MechanisticSimulator())
    results = predictor.forecast_standard_horizons(
        MechanisticState(0.9, 0.1, 0.8, 0.05)
    )
    assert [r.horizon_years for r in results] == [5.0, 20.0, 50.0, 100.0]
    assert results[-1].uncertainty > results[0].uncertainty
    assert all(not r.validated for r in results)


def test_longevity_scenario_is_not_a_lifespan_claim():
    model = LongevityScenarioModel(LongHorizonPredictor(MechanisticSimulator()))
    result = model.scenario(MechanisticState(0.9, 0.1, 0.8, 0.05), 100)
    assert result.interpretation == "research_scenario_only"
    assert result.target_years == 100


def test_rejuvenation_planner_withholds_action_when_evidence_is_weak():
    ranked = RejuvenationPlanner().rank([
        {"node_id": "region-a", "priority": 0.9, "confidence": 0.4, "evidence": 0.8, "action": "rejuvenate"},
    ])
    assert ranked[0].action == "insufficient_evidence"


def test_whole_body_twin_supports_bidirectional_hierarchy():
    twin = WholeBodyTwin()
    twin.add_node("person", level="organism")
    twin.add_node("hand", parent_id="person", level="organ")
    twin.add_node("tissue", parent_id="hand", level="tissue")
    twin.add_node("cell", parent_id="tissue", level="cell")
    assert twin.descendants("person") == ("hand", "tissue", "cell")
    assert twin.ancestors("cell") == ("tissue", "hand", "person")


def test_clinical_validation_has_explicit_gates():
    plan = ClinicalValidationPlan()
    assert plan.next_phase(()) == "unit_and_deterministic_validation"
    assert plan.next_phase(plan.phases[:-1]) == "safety_and_regulatory_review"
    assert not plan.is_clinically_ready(plan.phases[:-1])
    assert plan.is_clinically_ready(plan.phases)
