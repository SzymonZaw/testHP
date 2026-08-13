"""Tests for the longitudinal model and core longitudinal utilities."""

import pytest
import torch


def test_longitudinal_module_import():
    from models import longitudinal_model  # noqa: F401


def _model():
    from models.longitudinal_model import LongitudinalModel, LongitudinalModelConfig
    return LongitudinalModel(LongitudinalModelConfig(input_dim=768, hidden_dim=256))


def test_longitudinal_model_creation():
    assert _model() is not None


def test_longitudinal_sequence():
    sequence = torch.randn(2, 4, 768)
    assert sequence.shape == (2, 4, 768)
    assert torch.isfinite(sequence).all()


def test_longitudinal_forward():
    model = _model()
    model.eval()
    with torch.no_grad():
        output = model(torch.randn(1, 4, 768))
    assert output["current_state"].shape == (1, 256)


def test_longitudinal_batch():
    model = _model()
    model.eval()
    with torch.no_grad():
        output = model(torch.randn(4, 4, 768))
    assert output["current_state"].shape == (4, 256)


def test_core_compare_states():
    from core.biological_state import BiologicalState
    from core.longitudinal import compare_states
    baseline = BiologicalState("person-001", "T0")
    current = BiologicalState("person-001", "T1")
    baseline.set_dimension("cell_density", 100.0)
    current.set_dimension("cell_density", 90.0)
    comparison = compare_states(baseline, current, elapsed_days=365)
    change = comparison.changes[0]
    assert change.name == "cell_density"
    assert change.delta == -10.0
    assert change.rate_per_day == pytest.approx(-10.0 / 365)
    assert change.relative_change == pytest.approx(-0.1)


def test_core_compare_rejects_different_subjects():
    from core.biological_state import BiologicalState
    from core.longitudinal import compare_states
    with pytest.raises(ValueError):
        compare_states(BiologicalState("person-001", "T0"), BiologicalState("person-002", "T1"), 30)


def test_core_compare_rejects_invalid_interval():
    from core.biological_state import BiologicalState
    from core.longitudinal import compare_states
    with pytest.raises(ValueError):
        compare_states(BiologicalState("person-001", "T0"), BiologicalState("person-001", "T1"), 0)


def test_core_trajectory():
    from core.biological_state import BiologicalState
    from core.longitudinal import trajectory
    states = []
    for timepoint, value in [("T0", 100), ("T1", 95), ("T2", 91)]:
        state = BiologicalState("person-001", timepoint)
        state.set_dimension("cell_density", value)
        states.append(state)
    result = trajectory(states, [0, 365, 730])
    assert result["cell_density"] == [100.0, 95.0, 91.0]


def test_core_trajectory_rejects_mixed_subjects():
    from core.biological_state import BiologicalState
    from core.longitudinal import trajectory
    with pytest.raises(ValueError):
        trajectory([BiologicalState("person-001", "T0"), BiologicalState("person-002", "T1")], [0, 365])
