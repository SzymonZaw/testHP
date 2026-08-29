from __future__ import annotations

"""Adapters for image-based external models.

Cellpose is already a project dependency, so the adapter uses it when
installed. The wrapper returns raw model output and keeps scientific
interpretation in testHP's evidence/state layers.
"""

from typing import Any


def cellpose_sam_available() -> bool:
    try:
        import cellpose  # noqa: F401
    except ImportError:
        return False
    return True


def segment_cells(image: Any, *, model_type: str = "cpsam", channels: list[int] | None = None, **kwargs: Any) -> Any:
    """Run Cellpose-SAM lazily; raises a clear error when the dependency is absent."""
    try:
        from cellpose import models
    except ImportError as exc:
        raise RuntimeError("Cellpose is not installed; install the project's cellpose dependency") from exc

    model = models.CellposeModel(model_type=model_type, **kwargs)
    return model.eval(image, channels=channels or [0, 0])
