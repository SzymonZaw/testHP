from __future__ import annotations

"""Optional adapters for external foundation models.

Weights are never committed to testHP. Each adapter performs lazy imports so
that the core application remains usable without GPU/model environments.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExternalModelHandle:
    integration_id: str
    model_name: str
    model_version: str | None = None
    device: str = "auto"


def load_optional_module(module_name: str) -> Any:
    try:
        return __import__(module_name)
    except ImportError as exc:
        raise RuntimeError(
            f"optional scientific model dependency '{module_name}' is not installed"
        ) from exc


def make_handle(integration_id: str, model_name: str, *, model_version: str | None = None, device: str = "auto") -> ExternalModelHandle:
    return ExternalModelHandle(integration_id, model_name, model_version, device)


# These are deliberately handles, not hard-coded model implementations. The
# exact upstream loading API can change independently of testHP.
def scgpt_handle(**kwargs: Any) -> ExternalModelHandle:
    return make_handle("scgpt", "scGPT", **kwargs)


def geneformer_handle(**kwargs: Any) -> ExternalModelHandle:
    return make_handle("geneformer", "Geneformer", **kwargs)


def scgpt_spatial_handle(**kwargs: Any) -> ExternalModelHandle:
    return make_handle("scgpt-spatial", "scGPT-spatial", **kwargs)


def uni2_handle(**kwargs: Any) -> ExternalModelHandle:
    return make_handle("uni2", "UNI2", **kwargs)


def u_segment3d_handle(**kwargs: Any) -> ExternalModelHandle:
    return make_handle("u-segment3d", "u-Segment3D", **kwargs)
