"""
Testy dla models/monai_pipeline.py

Uruchomienie:
    pytest tests/test_monai.py -v
"""

import pytest
import torch


def test_monai_import():
    """Sprawdza dostępność biblioteki MONAI."""
    try:
        import monai  # noqa: F401
    except ImportError as exc:
        pytest.fail(
            "MONAI nie jest zainstalowane. "
            f"Uruchom instalację zależności. Szczegóły: {exc}"
        )


def test_monai_pipeline_module_import():
    """Sprawdza import własnego pipeline'u MONAI."""
    try:
        from models import monai_pipeline  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Nie można zaimportować models.monai_pipeline: {exc}"
        )


def test_3d_tensor():
    """
    Sprawdza podstawowy tensor reprezentujący obraz 3D.

    Format:
        batch x channels x depth x height x width
    """
    volume = torch.randn(1, 1, 32, 128, 128)

    assert volume.ndim == 5
    assert volume.shape[0] == 1
    assert volume.shape[1] == 1
    assert torch.isfinite(volume).all()


def test_monai_transform_pipeline():
    """Sprawdza podstawową transformację MONAI."""
    from monai.transforms import Compose, ScaleIntensity, EnsureType

    transform = Compose(
        [
            ScaleIntensity(),
            EnsureType(),
        ]
    )

    image = torch.rand(1, 64, 64)
    result = transform(image)

    assert result is not None
    assert result.shape == image.shape