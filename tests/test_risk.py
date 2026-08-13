"""Testy dla models/risk_model.py."""

import pytest
import torch


def test_risk_module_import():
    try:
        from models import risk_model  # noqa: F401
    except Exception as exc:
        pytest.fail(f"Nie można zaimportować models.risk_model: {exc}")


def _model():
    from models.risk_model import RiskModel, RiskModelConfig
    return RiskModel(RiskModelConfig(image_dim=768, hidden_dim=256))


def test_risk_model_creation():
    assert _model() is not None


def test_risk_forward():
    model = _model()
    model.eval()
    x = torch.randn(1, 768)
    with torch.no_grad():
        output = model(image=x)
    assert output is not None
    assert output["risk_scores"].shape == (1, 5)
    assert torch.isfinite(output["risk_scores"]).all()


def test_risk_batch():
    model = _model()
    model.eval()
    x = torch.randn(8, 768)
    with torch.no_grad():
        output = model(image=x)
    assert output is not None
    assert output["risk_scores"].shape == (8, 5)
    assert torch.isfinite(output["risk_scores"]).all()


def test_risk_input_finite():
    x = torch.randn(8, 768)
    assert torch.isfinite(x).all()
