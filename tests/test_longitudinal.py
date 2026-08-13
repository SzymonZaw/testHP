"""
Testy dla models/longitudinal_model.py

Uruchomienie:
    pytest tests/test_longitudinal.py -v
"""

import pytest
import torch


def test_longitudinal_module_import():
    """Sprawdza import modelu longitudinal."""
    try:
        from models import longitudinal_model  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Nie można zaimportować models.longitudinal_model: {exc}"
        )


def test_longitudinal_model_creation():
    """Sprawdza inicjalizację modelu."""
    from models.longitudinal_model import LongitudinalModel

    model = LongitudinalModel(
        input_dim=768,
        hidden_dim=256,
    )

    assert model is not None


def test_longitudinal_sequence():
    """
    Sprawdza przykładową sekwencję T0-T3.

    Format:
        batch x time x features
    """
    sequence = torch.randn(
        2,
        4,
        768,
    )

    assert sequence.shape == (2, 4, 768)
    assert torch.isfinite(sequence).all()


def test_longitudinal_forward():
    """Sprawdza forward pass modelu longitudinal."""
    from models.longitudinal_model import LongitudinalModel

    model = LongitudinalModel(
        input_dim=768,
        hidden_dim=256,
    )

    model.eval()

    x = torch.randn(
        1,
        4,
        768,
    )

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_longitudinal_batch():
    """Sprawdza batch longitudinal."""
    from models.longitudinal_model import LongitudinalModel

    model = LongitudinalModel(
        input_dim=768,
        hidden_dim=256,
    )

    model.eval()

    x = torch.randn(
        4,
        4,
        768,
    )

    with torch.no_grad():
        output = model(x)

    assert output is not None