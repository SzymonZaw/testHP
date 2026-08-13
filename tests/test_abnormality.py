"""Tests for the abnormality model."""

import pytest
import torch


def test_abnormality_module_import():
    from models import abnormality_model  # noqa: F401


def _model():
    from models.abnormality_model import AbnormalityModel, AbnormalityModelConfig
    return AbnormalityModel(
        AbnormalityModelConfig(
            input_dim=768,
            hidden_dim=512,
            num_classes=2,
            dropout=0.2,
        )
    )


def test_abnormality_model_creation():
    assert _model() is not None


def test_abnormality_forward():
    model = _model()
    model.eval()
    with torch.no_grad():
        output = model(torch.randn(1, 768))
    assert output.shape == (1, 2)


def test_abnormality_batch():
    model = _model()
    model.eval()
    with torch.no_grad():
        output = model(torch.randn(8, 768))
    assert output.shape == (8, 2)


def test_abnormality_input_finite():
    x = torch.randn(4, 768)
    assert torch.isfinite(x).all()
