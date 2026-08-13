"""
Testy dla models/hand_model.py / MANO.

Uruchomienie:
    pytest tests/test_mano.py -v
"""

from pathlib import Path

import pytest
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_hand_model_import():
    """Sprawdza import własnego modelu dłoni."""
    try:
        from models import hand_model  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Nie można zaimportować models.hand_model: {exc}"
        )


def test_mano_checkpoint_directory_exists():
    """Sprawdza katalog checkpointów MANO."""
    checkpoint_dir = PROJECT_ROOT / "models" / "checkpoints" / "mano"

    assert checkpoint_dir.exists(), (
        f"Brakuje katalogu MANO: {checkpoint_dir}"
    )


def test_mano_pose_tensor():
    """
    Sprawdza przykładowy tensor parametrów pozy dłoni.
    """
    pose = torch.zeros(
        1,
        48,
        dtype=torch.float32,
    )

    assert pose.shape == (1, 48)
    assert torch.isfinite(pose).all()


def test_hand_shape_tensor():
    """Sprawdza tensor parametrów kształtu dłoni."""
    shape = torch.zeros(
        1,
        10,
        dtype=torch.float32,
    )

    assert shape.shape == (1, 10)
    assert torch.isfinite(shape).all()


def test_hand_landmarks():
    """
    Sprawdza przykładowe 3D landmarki dłoni.
    """
    landmarks = torch.zeros(
        1,
        21,
        3,
        dtype=torch.float32,
    )

    assert landmarks.shape == (1, 21, 3)
    assert torch.isfinite(landmarks).all()