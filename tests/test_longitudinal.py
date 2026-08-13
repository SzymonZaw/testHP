"""
Testy dla models/longitudinal_model.py oraz core.longitudinal.

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

    model = LongitudinalModel(input_dim=768, hidden_dim=256)
    assert model is not None


def test_longitudinal_sequence():
    """Sprawdza przykładową sekwencję T0-T3."""
    sequence = torch.randn(2, 4, 768)
    assert sequence.shape == (2, 4, 768)
    assert torch.isfinite(sequence).all()


def test_longitudinal_forward():
    """Sprawdza forward pass modelu longitudinal."""
    from models.longitudinal_model import LongitudinalModel

    model = LongitudinalModel(input_dim=768, hidden_dim=256)
    model.eval()
    x = torch.randn(1, 4, 768)

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_longitudinal_batch():
    """Sprawdza batch longitudinal."""
    from models.longitudinal_model import LongitudinalModel

    model = LongitudinalModel(input_dim=768, hidden_dim=256)
    model.eval()
    x = torch.randn(4, 4, 768)

    with torch.no_grad():
        output = model(x)

    assert output is not None


def test_core_compare_states():
    """Sprawdza zmianę wymiaru biologicznego między T0 i T1."""
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
    """Nie wolno porównywać stanów różnych osób."""
    from core.biological_state import BiologicalState
    from core.longitudinal import compare_states

    a = BiologicalState("person-001", "T0")
    b = BiologicalState("person-002", "T1")

    with pytest.raises(ValueError):
        compare_states(a, b, 30)


def test_core_compare_rejects_invalid_interval():
    """Odstęp czasowy musi być dodatni."""
    from core.biological_state import BiologicalState
    from core.longitudinal import compare_states

    a = BiologicalState("person-001", "T0")
    b = BiologicalState("person-001", "T1")

    with pytest.raises(ValueError):
        compare_states(a, b, 0)


def test_core_trajectory():
    """Sprawdza trajektorię parametru T0-T2."""
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
    """Trajektoria nie może łączyć różnych osób."""
    from core.biological_state import BiologicalState
    from core.longitudinal import trajectory

    a = BiologicalState("person-001", "T0")
    b = BiologicalState("person-002", "T1")

    with pytest.raises(ValueError):
        trajectory([a, b], [0, 365])
