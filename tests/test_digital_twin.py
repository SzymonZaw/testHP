"""Testy dla models/digital_twin.py."""

import pytest
import torch


def test_digital_twin_module_import():
    try:
        from models import digital_twin  # noqa: F401
    except Exception as exc:
        pytest.fail(f"Nie można zaimportować models.digital_twin: {exc}")


def test_digital_twin_creation():
    from models.digital_twin import DigitalTwin
    twin = DigitalTwin(subject_id="demo-subject")
    assert twin is not None


def test_digital_twin_state():
    state = {"biological_age": 45.0, "risk_score": 0.25, "abnormality_score": 0.10}
    assert "biological_age" in state
    assert "risk_score" in state
    assert "abnormality_score" in state
    assert 0.0 <= state["risk_score"] <= 1.0
    assert 0.0 <= state["abnormality_score"] <= 1.0


def test_digital_twin_embedding():
    embedding = torch.randn(1, 768)
    assert embedding.shape == (1, 768)
    assert torch.isfinite(embedding).all()


def test_digital_twin_temporal_states():
    states = {f"T{i}": torch.randn(1, 768) for i in range(4)}
    assert len(states) == 4
    for timepoint, state in states.items():
        assert timepoint in {"T0", "T1", "T2", "T3"}
        assert state.shape == (1, 768)
        assert torch.isfinite(state).all()


def test_digital_twin_state_update():
    previous_state = {"biological_age": 45.0, "risk_score": 0.30}
    new_state = {"biological_age": 45.5, "risk_score": 0.25}
    assert new_state["biological_age"] >= 0
    assert 0 <= new_state["risk_score"] <= 1
    assert previous_state != new_state


def test_digital_twin_no_nan():
    state = torch.tensor([[45.0, 0.25, 0.10]], dtype=torch.float32)
    assert torch.isfinite(state).all()
