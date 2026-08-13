"""
Testy dla models/aging_model.py

Uruchomienie:
    pytest tests/test_aging.py -v
"""

import pytest
import torch


def test_aging_module_import():
    """Sprawdza import modelu aging."""
    try:
        from models import aging_model  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Nie można zaimportować models.aging_model: {exc}"
        )


def test_aging_input():
    """Sprawdza przykładowy embedding wejściowy."""
    embedding = torch.randn(1, 768)

    assert embedding.shape == (1, 768)
    assert torch.isfinite(embedding).all()


def test_aging_model_forward():
    """
    Sprawdza podstawowy forward pass.

    Jeżeli implementacja modelu używa innego wymiaru
    wejściowego, test należy dopasować do konfiguracji modelu.
    """
    from models.aging_model import AgingModel

    model = AgingModel(
        input_dim=768,
        hidden_dim=256,
    )

    model.eval()

    x = torch.randn(1, 768)

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_aging_output_finite():
    """Sprawdza, czy wynik modelu jest skończony."""
    from models.aging_model import AgingModel

    model = AgingModel(
        input_dim=768,
        hidden_dim=256,
    )

    model.eval()

    x = torch.randn(1, 768)

    with torch.no_grad():
        output = model(x)

    if isinstance(output, torch.Tensor):
        assert torch.isfinite(output).all()