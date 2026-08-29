"""Conservative cell -> microenvironment -> tissue aggregation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import hypot
from typing import Any, Iterable


@dataclass(frozen=True)
class CellContext:
    cell_id: int
    cell_type: str
    cell_type_confidence: float | None
    nearest_neighbor_count: int
    local_density_cells_per_1e6_px2: float
    neighborhood: str
    tissue_region_id: str


@dataclass(frozen=True)
class TissueRegion:
    region_id: str
    tile_x: int
    tile_y: int
    cell_count: int
    cell_density_cells_per_1e6_px2: float
    mean_cell_area_px: float
    spatial_state: str


def _distance(a: Any, b: Any) -> float:
    return hypot(a.centroid_x_px - b.centroid_x_px, a.centroid_y_px - b.centroid_y_px)


def build_cell_tissue_context(
    cells: Iterable[Any],
    *,
    neighbor_radius_px: float = 150.0,
    region_tile_size_px: int = 1024,
) -> dict[str, Any]:
    """Aggregate detected cells into local neighborhoods and spatial tissue regions.

    Cell identity is deliberately unresolved until a validated classifier is supplied.
    """
    if neighbor_radius_px <= 0:
        raise ValueError("neighbor_radius_px must be positive")
    if region_tile_size_px <= 0:
        raise ValueError("region_tile_size_px must be positive")

    cells = list(cells)
    contexts: list[CellContext] = []
    grouped: dict[tuple[int, int], list[Any]] = {}

    for cell in cells:
        key = (int(cell.centroid_x_px) // region_tile_size_px, int(cell.centroid_y_px) // region_tile_size_px)
        grouped.setdefault(key, []).append(cell)

    for key, group in grouped.items():
        area = float(region_tile_size_px * region_tile_size_px)
        density = len(group) / area * 1_000_000.0
        for cell in group:
            neighbors = sum(
                1 for other in cells
                if other.cell_id != cell.cell_id and _distance(cell, other) <= neighbor_radius_px
            )
            neighborhood = "isolated" if neighbors == 0 else "sparse" if neighbors <= 4 else "dense"
            contexts.append(CellContext(
                cell_id=int(cell.cell_id),
                cell_type="not_established",
                cell_type_confidence=None,
                nearest_neighbor_count=neighbors,
                local_density_cells_per_1e6_px2=density,
                neighborhood=neighborhood,
                tissue_region_id=f"region_{key[0]}_{key[1]}",
            ))

    regions: list[TissueRegion] = []
    for key, group in sorted(grouped.items()):
        area = float(region_tile_size_px * region_tile_size_px)
        regions.append(TissueRegion(
            region_id=f"region_{key[0]}_{key[1]}",
            tile_x=key[0],
            tile_y=key[1],
            cell_count=len(group),
            cell_density_cells_per_1e6_px2=len(group) / area * 1_000_000.0,
            mean_cell_area_px=sum(float(c.area_px) for c in group) / len(group),
            spatial_state="cell_present",
        ))

    return {
        "cells": [asdict(c) for c in contexts],
        "tissue_regions": [asdict(r) for r in regions],
        "cell_type_status": "not_established",
        "microenvironment_status": "spatial_descriptors_only",
        "tissue_state_status": "morphology_and_spatial_descriptors_only",
        "disease_status": "not_established",
        "biological_age_status": "not_established",
    }
