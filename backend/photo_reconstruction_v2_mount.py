"""Compatibility mount helper for applications that register routers centrally."""
from .photo_reconstruction_routes_v2 import router as photo_reconstruction_v2_router

__all__ = ['photo_reconstruction_v2_router']
