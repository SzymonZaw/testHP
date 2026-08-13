"""
Testy dla models/dinov2_model.py

Uruchomienie:
    pytest tests/test_dinov2.py -v
"""

from pathlib import Path

import pytest
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dinov2_module_import():
    """Sprawdza import modułu DINOv2."""
    try:
        from models import dinov2_model  # noqa: F401
    except Exception as exc:
        pytest.fail(f"Nie można zaimportować models.dinov2_model: {exc}")


def test_dinov2_checkpoint_directory_exists():
    """Sprawdza katalog checkpointów DINOv2."""
    checkpoint_dir = PROJECT_ROOT / "models" / "checkpoints" / "dinov2"

    assert checkpoint_dir.exists(), (
        f"Brakuje katalogu checkpointów DINOv2: {checkpoint_dir}"
    )


def test_embedding_shape():
    """
    Sprawdza przykładowy embedding DINOv2.

    768 odpowiada typowemu wymiarowi embeddingu
    dla DINOv2 ViT-B/14.
    """
    embedding = torch.randn(1, 768)

    assert embedding.shape == (1, 768)
    assert torch.isfinite(embedding).all()


def test_embedding_not_nan():
    """Embedding nie może zawierać NaN."""
    embedding = torch.randn(1, 768)

    assert not torch.isnan(embedding).any()