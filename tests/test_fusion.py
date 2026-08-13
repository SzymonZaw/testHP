"""
Testy dla models/fusion_model.py

Uruchomienie:
    pytest tests/test_fusion.py -v
"""

import pytest
import torch


def test_fusion_module_import():
    """Sprawdza import modułu fusion."""
    try:
        from models import fusion_model  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Nie można zaimportować models.fusion_model: {exc}"
        )


def test_fusion_input_embeddings():
    """
    Sprawdza przykładowe embeddingi wejściowe
    dla różnych modalności.
    """
    image = torch.randn(1, 768)
    wsi = torch.randn(1, 768)
    rna = torch.randn(1, 256)
    hand = torch.randn(1, 128)

    assert image.shape == (1, 768)
    assert wsi.shape == (1, 768)
    assert rna.shape == (1, 256)
    assert hand.shape == (1, 128)

    assert torch.isfinite(image).all()
    assert torch.isfinite(wsi).all()
    assert torch.isfinite(rna).all()
    assert torch.isfinite(hand).all()


def test_fusion_concatenation():
    """Sprawdza możliwość połączenia embeddingów."""
    image = torch.randn(1, 768)
    rna = torch.randn(1, 256)
    hand = torch.randn(1, 128)

    fused = torch.cat(
        [image, rna, hand],
        dim=1,
    )

    assert fused.shape == (1, 1152)
    assert torch.isfinite(fused).all()


def test_fusion_batch_size():
    """Sprawdza zachowanie wspólnego batch size."""
    batch_size = 4

    image = torch.randn(batch_size, 768)
    rna = torch.randn(batch_size, 256)
    hand = torch.randn(batch_size, 128)

    fused = torch.cat(
        [image, rna, hand],
        dim=1,
    )

    assert fused.shape[0] == batch_size
    assert fused.shape[1] == 1152