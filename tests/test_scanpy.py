"""
Testy dla models/scanpy_model.py

Uruchomienie:
    pytest tests/test_scanpy.py -v
"""

import numpy as np
import pytest


def test_scanpy_import():
    """Sprawdza dostępność Scanpy."""
    try:
        import scanpy as sc  # noqa: F401
    except ImportError as exc:
        pytest.fail(
            f"Scanpy nie jest zainstalowane: {exc}"
        )


def test_scanpy_model_import():
    """Sprawdza import własnego modelu Scanpy."""
    try:
        from models import scanpy_model  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Nie można zaimportować models.scanpy_model: {exc}"
        )


def test_expression_matrix():
    """
    Tworzy małą sztuczną macierz ekspresji RNA.

    Format:
        komórki x geny
    """
    expression = np.random.poisson(
        lam=2.0,
        size=(20, 100),
    )

    assert expression.shape == (20, 100)
    assert np.all(expression >= 0)


def test_expression_matrix_no_nan():
    """Macierz RNA nie powinna zawierać NaN."""
    expression = np.random.poisson(
        lam=2.0,
        size=(20, 100),
    ).astype(float)

    assert not np.isnan(expression).any()
    assert np.isfinite(expression).all()


def test_anndata_creation():
    """Sprawdza utworzenie podstawowego obiektu AnnData."""
    import anndata as ad

    expression = np.random.poisson(
        lam=2.0,
        size=(10, 50),
    )

    data = ad.AnnData(expression)

    assert data.n_obs == 10
    assert data.n_vars == 50