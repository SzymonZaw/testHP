"""Tests for models/intervention_model.py."""

import pytest
import torch


def test_intervention_module_import():
    from models import intervention_model  # noqa: F401


def test_intervention_model_creation():
    from models.intervention_model import InterventionModel
    assert InterventionModel() is not None


def test_intervention_forward():
    from models.intervention_model import InterventionModel
    model = InterventionModel()
    model.eval()
    with torch.no_grad():
        output = model(risk=torch.randn(1, 128))
    assert output["intervention_probabilities"].shape == (1, 8)


def test_intervention_batch():
    from models.intervention_model import InterventionModel
    model = InterventionModel()
    model.eval()
    with torch.no_grad():
        output = model(risk=torch.randn(4, 128))
    assert output["intervention_probabilities"].shape == (4, 8)


def test_intervention_input_finite():
    x = torch.randn(4, 128)
    assert torch.isfinite(x).all()
