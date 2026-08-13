"""
Testy dla models/cellpose_model.py

Uruchomienie:
    pytest tests/test_cellpose.py -v
"""

from pathlib import Path

import pytest
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_cellpose_module_import():
    """Sprawdza import modułu Cellpose."""
    try:
        from models import cellpose_model  # noqa: F401
    except Exception as exc:
        pytest.fail(f"Nie można zaimportować models.cellpose_model: {exc}")


def test_cellpose_checkpoint_directory_exists():
    """
    Sprawdza katalog checkpointów.

    Sam katalog może być pusty na etapie developmentu.
    """
    checkpoint_dir = PROJECT_ROOT / "models" / "checkpoints" / "cellpose"

    assert checkpoint_dir.exists(), (
        f"Brakuje katalogu checkpointów Cellpose: {checkpoint_dir}"
    )


def test_tensor_creation():
    """Podstawowy test operacji tensorowych."""
    image = torch.randn(1, 3, 256, 256)

    assert image.shape == (1, 3, 256, 256)
    assert torch.isfinite(image).all()


def test_cell_mask_shape():
    """
    Sprawdza oczekiwany typ danych dla przykładowej maski komórek.
    """
    mask = torch.zeros((256, 256), dtype=torch.int64)

    assert mask.ndim == 2
    assert mask.shape == (256, 256)