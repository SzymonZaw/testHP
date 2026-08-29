from backend.simulation_contract import SimulationResult, SimulationState, SimulationScenario, TransitionModelRef, compare_results
from backend.predictive_twin_contract import Forecast, ForecastHorizon, PredictiveModelRef, PredictiveTwin
from backend.aging_model_contract import AgingModel, AgingTrajectoryPoint
from backend.human_twin_contract import HumanDigitalTwin, OrganTwinRef, CrossOrganRelation


def test_simulation_scenarios_are_comparable():
    model = TransitionModelRef("m1", "1", "hand")
    state = SimulationState("s1", "2030-01-01", {"health": .8})
    results = tuple(SimulationResult(i, model, state, .8) for i in ("none", "treatment-a"))
    assert set(compare_results(results)) == {"none", "treatment-a"}


def test_predictive_twin_supports_horizons_and_intervals():
    twin = PredictiveTwin("t1", "s1", PredictiveModelRef("pm1", "1"), (Forecast(ForecastHorizon.LONG, "2080-01-01", {"health": .5}, {"health": .2}, {"health": .8}, .6),))
    twin.validate()


def test_aging_trajectory_is_ordered():
    model = AgingModel("a1", "1", "ref1", (), tuple(AgingTrajectoryPoint(str(y), y, 65 + y) for y in (0, 5, 10, 20, 50)))
    model.validate()


def test_human_twin_validates_cross_organ_links():
    twin = HumanDigitalTwin("person-1", (OrganTwinRef("hand", "hand", "hand-twin"), OrganTwinRef("heart", "heart", "heart-twin")), (CrossOrganRelation("r1", "hand", "heart", "vascular", confidence=.7),))
    twin.validate()
