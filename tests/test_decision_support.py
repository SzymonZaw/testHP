from backend.decision_support import DecisionSupport
from backend.risk_model import RiskModel
from backend.risk_signal import RiskSignal
from backend.scenario_comparison import ScenarioComparison
from backend.intervention_scenario import InterventionScenario


def risk(level):
    return RiskModel.from_signals((RiskSignal("test", level, 0.9, None, {}),))


def test_low_risk_maps_to_no_action():
    result = DecisionSupport.from_analysis(risk("low"))
    assert result.action == "no_action"


def test_moderate_risk_maps_to_monitor():
    result = DecisionSupport.from_analysis(risk("moderate"))
    assert result.action == "monitor"


def test_elevated_risk_maps_to_investigate():
    result = DecisionSupport.from_analysis(risk("elevated"))
    assert result.action == "investigate"


def test_insufficient_data_is_explicit():
    result = DecisionSupport.from_analysis(RiskModel.from_signals(()))
    assert result.action == "insufficient_data"
    assert result.reasons == ("insufficient_risk_signals",)


def test_meaningful_scenario_is_preserved_as_evidence():
    scenario = InterventionScenario("hypothetical", 0.8, 0.9, 0.1, 0.0)
    comparison = ScenarioComparison.from_scenario(scenario, uncertainty=0.05)
    result = DecisionSupport.from_analysis(risk("elevated"), comparison)

    assert result.action == "investigate"
    assert "meaningful_projected_difference" in result.reasons
