"""Single entry point for the Photo 3D Reconstruction pipeline (stages 6-10)."""
from __future__ import annotations

from typing import Any

from .photo_reconstruction import _load_manifest
from .visual_hull import build_reconstruction, clear_reconstructions, latest_reconstruction


def run(subject_id: str, timepoint: str = 'default', resolution: int = 24) -> dict[str, Any]:
    records = [r for r in _load_manifest() if r.get('subject_id') == subject_id and r.get('timepoint') == timepoint]
    registered = [r for r in records if r.get('registration', {}).get('status') == 'registered']
    if len(registered) < 2:
        return {'status': 'blocked', 'reason': 'At least two registered views are required', 'registered_count': len(registered)}
    return build_reconstruction(subject_id, timepoint, resolution)


def get_result(subject_id: str, timepoint: str = 'default') -> dict[str, Any] | None:
    return latest_reconstruction(subject_id, timepoint)


def clear(subject_id: str, timepoint: str = 'default') -> int:
    return clear_reconstructions(subject_id, timepoint)
