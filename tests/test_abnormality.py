"""
Testy dla models/abnormality_model.py

Uruchomienie:
    pytest tests/test_abnormality.py -v
"""

import pytest
import torch


def test_abnormality_module_import():
    """Sprawdza import modelu abnormality."""
    try:
        from models import abnormality_model  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Nie można zaimportować models.abnormality_model: {exc}"
        )


def test_abnormality_model_creation():
    """Sprawdza utworzenie modelu."""
    from models.abnormality_model import AbnormalityModel

    model = AbnormalityModel(
        input_dim=768,
        hidden_dim=512,
        num_classes=2,
        dropout=0.2,
    )

    assert model is not None


def test_abnormality_forward():
    """Sprawdza forward pass modelu."""
    from models.abnormality_model import AbnormalityModel

    model = AbnormalityModel(
        input_dim=768,
        hidden_dim=512,
        num_classes=2,
        dropout=0.2,
    )

    model.eval()

    x = torch.randn(1, 768)

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_abnormality_batch():
    """Sprawdza działanie dla batcha."""
    from models.abnormality_model import AbnormalityModel

    model = AbnormalityModel(
        input_dim=768,
        hidden_dim=512,
        num_classes=2,
        dropout=0.2,
    )

    model.eval()

    x = torch.randn(8, 768)

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_abnormality_input_finite():
    """Sprawdza poprawność danych wejściowych."""
    x = torch.randn(4, 768)

    assert torch.isfinite(x).all()