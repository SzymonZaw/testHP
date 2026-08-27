from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SpatialAttentionZone:
    zone_id: str
    level: str
    metric: str
    centroid: tuple[float, float, float]
    score: float
    status: str
    source_cell_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "level": self.level,
            "metric": self.metric,
            "centroid": self.centroid,
            "score": self.score,
            "status": self.status,
            "source_cell_ids": self.source_cell_ids,
        }


def build_spatial_attention_map(
    attention: list[dict[str, Any]],
    *,
    cell_positions: dict[str, dict[str, float]],
    zone_cells: dict[str, tuple[str, ...]],
) -> list[dict[str, Any]]:
    """Attach observed attention zones to spatial cell coordinates.

    Coordinates are descriptive only. No interpolation is performed and zones
    without observed source cells are omitted, preventing unsupported spatial
    claims.
    """
    result: list[SpatialAttentionZone] = []
    for item in attention:
        zone_id = str(item.get("zone_id", ""))
        cells = tuple(c for c in zone_cells.get(zone_id, ()) if c in cell_positions)
        if not cells:
            continue
        points = [cell_positions[c] for c in cells]
        centroid = tuple(round(sum(float(p.get(axis, 0.0)) for p in points) / len(points), 6) for axis in ("x", "y", "z"))
        result.append(SpatialAttentionZone(
            zone_id=zone_id,
            level=str(item.get("level", "unknown")),
            metric=str(item.get("metric", "unknown")),
            centroid=centroid,
            score=max(0.0, min(1.0, float(item.get("score", 0.0)))),
            status=str(item.get("status", "monitor")),
            source_cell_ids=cells,
        ))
    return [x.to_dict() for x in sorted(result, key=lambda x: (-x.score, x.zone_id))]
