"""
Testy dla models/pathology_model.py
"""

import pytest
import torch


def test_pathology_module_import():
    try:
        from models import pathology_model  # noqa: F401
    except Exception as exc:
        pytest.fail(f"Nie można zaimportować models.pathology_model: {exc}")


def _model():
    from models.pathology_model import PathologyModel
    return PathologyModel(embedding_dim=768)


def test_pathology_model_creation():
    model = _model()
    assert model is not None
    assert model.model is not None


def test_pathology_forward():
    model = _model()
    model.eval()
    x = torch.randn(1, 768)
    with torch.no_grad():
        output = model.model(x)
    assert output.shape == (1, 4)
    assert torch.isfinite(output).all()


def test_pathology_batch():
    model = _model()
    model.eval()
    x = torch.randn(4, 768)
    with torch.no_grad():
        output = model.model(x)
    assert output.shape == (4, 4)
    assert torch.isfinite(output).all()


def test_pathology_input_finite():
    x = torch.randn(4, 768)
    assert torch.isfinite(x).all()
