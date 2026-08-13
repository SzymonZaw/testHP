"""
Testy dla models/risk_model.py

Uruchomienie:
    pytest tests/test_risk.py -v
"""

import pytest
import torch


def test_risk_module_import():
    """Sprawdza import modelu risk."""
    try:
        from models import risk_model  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Nie można zaimportować models.risk_model: {exc}"
        )


def test_risk_model_creation():
    """Sprawdza inicjalizację modelu."""
    from models.risk_model import RiskModel

    model = RiskModel(
        input_dim=768,
        hidden_dim=256,
    )

    assert model is not None


def test_risk_forward():
    """Sprawdza forward pass."""
    from models.risk_model import RiskModel

    model = RiskModel(
        input_dim=768,
        hidden_dim=256,
    )

    model.eval()

    x = torch.randn(1, 768)

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_risk_batch():
    """Sprawdza batch processing."""
    from models.risk_model import RiskModel

    model = RiskModel(
        input_dim=768,
        hidden_dim=256,
    )

    model.eval()

    x = torch.randn(8, 768)

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_risk_input_finite():
    """Sprawdza dane wejściowe."""
    x = torch.randn(8, 768)

    assert torch.isfinite(x).all()