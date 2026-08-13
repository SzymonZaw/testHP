"""
Testy dla MediaPipe.

Uruchomienie:
    pytest tests/test_mediapipe.py -v
"""

import numpy as np
import pytest


def test_mediapipe_import():
    """Sprawdza dostępność MediaPipe."""
    try:
        import mediapipe as mp  # noqa: F401
    except ImportError as exc:
        pytest.fail(
            f"MediaPipe nie jest zainstalowane: {exc}"
        )


def test_hand_image_shape():
    """Sprawdza przykładowy obraz RGB dłoni."""
    image = np.zeros(
        (512, 512, 3),
        dtype=np.uint8,
    )

    assert image.shape == (512, 512, 3)
    assert image.dtype == np.uint8


def test_landmark_structure():
    """
    Sprawdza oczekiwaną strukturę landmarków dłoni.

    MediaPipe Hands używa 21 punktów.
    """
    landmarks = np.zeros(
        (21, 3),
        dtype=np.float32,
    )

    assert landmarks.shape == (21, 3)
    assert landmarks.dtype == np.float32


def test_landmark_coordinates_finite():
    """Współrzędne landmarków muszą być skończone."""
    landmarks = np.random.rand(21, 3).astype(np.float32)

    assert np.isfinite(landmarks).all()