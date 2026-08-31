"""Backend package bootstrap.

The application historically assembled routers directly in backend.app. Keep
that assembly backward-compatible while making the new cellular/molecular
pipeline available to the existing FastAPI application without duplicating
route registration in multiple entrypoints.
"""

from fastapi import FastAPI

from .hand_cellular_pipeline import register_hand_cellular_pipeline
from .reference_cell_extract_routes import register_reference_cell_extract_routes

_original_fastapi_init = FastAPI.__init__


def _testhp_fastapi_init(self, *args, **kwargs):
    _original_fastapi_init(self, *args, **kwargs)
    if getattr(self, "title", "") == "Human Pathology Platform":
        register_hand_cellular_pipeline(self)
        register_reference_cell_extract_routes(self)


if not getattr(FastAPI, "_testhp_cellular_stages_registered", False):
    FastAPI.__init__ = _testhp_fastapi_init
    FastAPI._testhp_cellular_stages_registered = True
