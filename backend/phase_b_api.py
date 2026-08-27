from __future__ import annotations

"""Small API-facing helpers for Phase B. No clinical interpretation is performed."""

from typing import Any

from .multiscale_registry import MultiscaleRegistry


def get_multiscale_snapshot(registry: MultiscaleRegistry) -> dict[str, Any]:
    """Return the canonical multimodal graph for inspection/debug/API adapters."""
    return registry.snapshot()


def get_subject_timeline(registry: MultiscaleRegistry, subject_id: str) -> dict[str, Any]:
    """Return all Phase-B objects for one subject, preserving their links."""
    snapshot = registry.snapshot()
    result = {}
    for key, objects in snapshot.items():
        result[key] = [obj for obj in objects if obj.get("subject_id") == subject_id]
    return {"subject_id": subject_id, "data": result}
