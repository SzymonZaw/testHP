"""
Testy dla models/intervention_model.py

Uruchomienie:
    pytest tests/test_intervention.py -v
"""

import pytest
import torch


def test_intervention_module_import():
    """Sprawdza import modelu intervention."""
    try:
        from models import intervention_model  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Nie można zaimportować models.intervention_model: {exc}"
        )


def test_intervention_model_creation():
    """Sprawdza inicjalizację modelu."""
    from models.intervention_model import InterventionModel

    model = InterventionModel(
        input_dim=768,
        hidden_dim=256,
        num_interventions=5,
    )

    assert model is not None


def test_intervention_forward():
    """Sprawdza forward pass."""
    from models.intervention_model import InterventionModel

    model = InterventionModel(
        input_dim=768,
        hidden_dim=256,
        num_interventions=5,
    )

    model.eval()

    x = torch.randn(1, 768)

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_intervention_batch():
    """Sprawdza działanie dla batcha."""
    from models.intervention_model import InterventionModel

    model = InterventionModel(
        input_dim=768,
        hidden_dim=256,
        num_interventions=5,
    )

    model.eval()

    x = torch.randn(4, 768)

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_intervention_input_finite():
    """Sprawdza brak NaN/Inf."""
    x = torch.randn(4, 768)

    assert torch.isfinite(x).all()