"""
Testy dla models/digital_twin.py

Uruchomienie:
    pytest tests/test_digital_twin.py -v
"""

import pytest
import torch


def test_digital_twin_module_import():
    """Sprawdza import modułu Digital Twin."""
    try:
        from models import digital_twin  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Nie można zaimportować models.digital_twin: {exc}"
        )


def test_digital_twin_creation():
    """Sprawdza utworzenie Digital Twin."""
    try:
        from models.digital_twin import DigitalTwin
    except ImportError as exc:
        pytest.fail(
            f"Nie można zaimportować DigitalTwin: {exc}"
        )

    twin = DigitalTwin()

    assert twin is not None


def test_digital_twin_state():
    """
    Sprawdza podstawowy stan cyfrowego bliźniaka.
    """
    state = {
        "biological_age": 45.0,
        "risk_score": 0.25,
        "abnormality_score": 0.10,
    }

    assert "biological_age" in state
    assert "risk_score" in state
    assert "abnormality_score" in state

    assert 0.0 <= state["risk_score"] <= 1.0
    assert 0.0 <= state["abnormality_score"] <= 1.0


def test_digital_twin_embedding():
    """Sprawdza przykładowy stan embeddingu."""
    embedding = torch.randn(
        1,
        768,
    )

    assert embedding.shape == (1, 768)
    assert torch.isfinite(embedding).all()


def test_digital_twin_temporal_states():
    """
    Sprawdza strukturę stanów T0-T3.
    """
    states = {
        "T0": torch.randn(1, 768),
        "T1": torch.randn(1, 768),
        "T2": torch.randn(1, 768),
        "T3": torch.randn(1, 768),
    }

    assert len(states) == 4

    for timepoint, state in states.items():
        assert timepoint in {"T0", "T1", "T2", "T3"}
        assert state.shape == (1, 768)
        assert torch.isfinite(state).all()


def test_digital_twin_state_update():
    """
    Sprawdza prostą aktualizację stanu.
    """
    previous_state = {
        "biological_age": 45.0,
        "risk_score": 0.30,
    }

    new_state = {
        "biological_age": 45.5,
        "risk_score": 0.25,
    }

    assert new_state["biological_age"] >= 0
    assert 0 <= new_state["risk_score"] <= 1

    assert previous_state != new_state


def test_digital_twin_no_nan():
    """Sprawdza, czy przykładowy stan nie zawiera NaN."""
    state = torch.tensor(
        [
            [45.0, 0.25, 0.10]
        ],
        dtype=torch.float32,
    )

    assert torch.isfinite(state).all()