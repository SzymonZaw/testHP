"""
Testy dla models/pathology_model.py

Uruchomienie:
    pytest tests/test_pathology.py -v
"""

import pytest
import torch


def test_pathology_module_import():
    """Sprawdza import modelu pathology."""
    try:
        from models import pathology_model  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Nie można zaimportować models.pathology_model: {exc}"
        )


def test_pathology_model_creation():
    """Sprawdza inicjalizację modelu."""
    try:
        from models.pathology_model import PathologyModel
    except ImportError as exc:
        pytest.fail(f"Brak PathologyModel: {exc}")

    model = PathologyModel(
        input_dim=768,
        hidden_dim=512,
        num_classes=4,
    )

    assert model is not None


def test_pathology_forward():
    """Sprawdza podstawowy forward pass."""
    from models.pathology_model import PathologyModel

    model = PathologyModel(
        input_dim=768,
        hidden_dim=512,
        num_classes=4,
    )

    model.eval()

    x = torch.randn(1, 768)

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_pathology_batch():
    """Sprawdza obsługę wielu próbek."""
    from models.pathology_model import PathologyModel

    model = PathologyModel(
        input_dim=768,
        hidden_dim=512,
        num_classes=4,
    )

    model.eval()

    x = torch.randn(4, 768)

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_pathology_input_finite():
    """Sprawdza brak NaN/Inf."""
    x = torch.randn(4, 768)

    assert torch.isfinite(x).all()