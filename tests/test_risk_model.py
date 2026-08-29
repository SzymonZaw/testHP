from backend.risk_model import RiskModel
from backend.risk_signal import RiskSignal


def test_empty_signals_have_insufficient_data():
    model = RiskModel.from_signals(())

    assert model.overall_level == "insufficient_data"
    assert model.confidence == 0.0
    assert model.signals == ()


def test_model_uses_highest_signal_severity_and_average_confidence():
    signals = (
        RiskSignal("health_change", "moderate", 0.8, None, {"health": 0.1}),
        RiskSignal("regional_change", "high", 0.6, "thumb", {"region": "thumb"}),
        RiskSignal("function_change", "low", 1.2, "index", {"function": 0.02}),
    )

    model = RiskModel.from_signals(signals)

    assert model.overall_level == "high"
    assert model.confidence == (0.8 + 0.6 + 1.0) / 3
    assert model.regions == ("index", "thumb")
    assert model.signal_types == ("function_change", "health_change", "regional_change")


def test_unknown_severity_is_treated_conservatively_as_low():
    signal = RiskSignal("unknown", "unexpected", 0.7, None, {})

    model = RiskModel.from_signals((signal,))

    assert model.overall_level == "low"
    assert model.confidence == 0.7
