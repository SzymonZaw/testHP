"""Tests for the aging model and biological aging clocks."""

import pytest
import torch


def test_aging_module_import():
    from models import aging_model  # noqa: F401


def test_aging_input():
    embedding = torch.randn(1, 768)
    assert embedding.shape == (1, 768)
    assert torch.isfinite(embedding).all()


def test_aging_model_forward():
    from models.aging_model import AgingModel
    model = AgingModel()
    model.eval()
    with torch.no_grad():
        output = model(image_features=torch.randn(1, 768))
    assert output is not None
    assert output.predicted_age.shape == (1,)


def test_aging_output_finite():
    from models.aging_model import AgingModel
    model = AgingModel()
    model.eval()
    with torch.no_grad():
        output = model(image_features=torch.randn(1, 768))
    assert torch.isfinite(output.predicted_age).all()


def test_clock_prediction_is_transparent():
    from aging import AgingClock, estimate_age
    clock = AgingClock("cell_clock", {"senescence": 2.0, "repair": -1.0}, intercept=50)
    result = estimate_age(clock, {"senescence": 0.5, "repair": 1.0})
    assert result.score == pytest.approx(50.0)
    assert result.missing_features == ()


def test_missing_features_are_reported():
    from aging import AgingClock, estimate_age
    clock = AgingClock("tissue_clock", {"fibrosis": 3.0, "repair": -1.0})
    result = estimate_age(clock, {"fibrosis": 0.5})
    assert result.missing_features == ("repair",)


def test_z_score():
    from aging.biological_clock import z_score
    assert z_score(12, 10, 2) == pytest.approx(1.0)


def test_invalid_reference_std_is_rejected():
    from aging.biological_clock import z_score
    with pytest.raises(ValueError):
        z_score(12, 10, 0)


def test_multilevel_profile():
    from aging import AgingClock, build_aging_profile
    clocks = {
        "cellular": AgingClock("cell", {"x": 1.0}),
        "tissue": AgingClock("tissue", {"x": 2.0}),
    }
    profile = build_aging_profile(
        clocks,
        {"cellular": {"x": 10}, "tissue": {"x": 5}},
    )
    assert profile.scores["cellular"].score == pytest.approx(10.0)
    assert profile.scores["tissue"].score == pytest.approx(10.0)
    assert profile.overall_score == pytest.approx(10.0)
