"""
Testy dla models/sam2_model.py

Uruchomienie:
    pytest tests/test_sam2.py -v
"""

from pathlib import Path

import pytest
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_sam2_module_import():
    """Sprawdza, czy moduł SAM2 można zaimportować."""
    try:
        from models import sam2_model  # noqa: F401
    except Exception as exc:
        pytest.fail(f"Nie można zaimportować models.sam2_model: {exc}")


def test_sam2_checkpoint_directory_exists():
    """Sprawdza istnienie katalogu checkpointów SAM2."""
    checkpoint_dir = PROJECT_ROOT / "models" / "checkpoints" / "sam2"

    assert checkpoint_dir.exists(), (
        f"Brakuje katalogu checkpointów SAM2: {checkpoint_dir}"
    )


def test_torch_available():
    """Sprawdza dostępność PyTorch."""
    assert torch.__version__ is not None


def test_cuda_information():
    """
    Test informacyjny GPU.

    Nie wymaga GPU.
    """
    if torch.cuda.is_available():
        assert torch.cuda.device_count() >= 1
    else:
        assert True