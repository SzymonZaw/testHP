"""Compatibility mount helper for the Photo Reconstruction quality API."""
from .photo_reconstruction_quality_routes import router as photo_reconstruction_quality_router

__all__ = ["photo_reconstruction_quality_router"]
