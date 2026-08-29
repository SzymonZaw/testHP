"""End-user WSI -> cell/tissue evidence pipeline.

The adapter is deliberately conservative: it extracts tissue tiles and cell
morphology/locations, but it does not infer cell type, disease or biological
age without a validated model and labels.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image

from segmentation.cell_segmentation import segment_binary_cells

try:
    import openslide  # type: ignore
except ImportError:  # pragma: no cover - exercised when optional dependency is absent
    openslide = None


@dataclass(frozen=True)
class WSICell:
    cell_id: int
    tile_x: int
    tile_y: int
    centroid_x_px: float
    centroid_y_px: float
    area_px: int
    width_px: int
    height_px: int


@dataclass(frozen=True)
class WSIAnalysisResult:
    source: str
    level: int
    dimensions_px: tuple[int, int]
    tile_size: int
    tissue_tiles: int
    cells: list[WSICell]
    cell_type_status: str
    disease_status: str
    biological_age_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "cells": [asdict(cell) for cell in self.cells],
            "dimensions_px": list(self.dimensions_px),
        }


def _open_wsi(path: Path):
    if openslide is None:
        raise RuntimeError(
            "WSI support requires the optional 'openslide-python' package. "
            "Install it before processing SVS/NDPI/MRXS WSI files."
        )
    try:
        return openslide.OpenSlide(str(path))
    except Exception as exc:
        raise RuntimeError(f"could not open WSI {path.name}: {exc}") from exc


def _is_tissue(tile: np.ndarray, min_fraction: float = 0.10) -> bool:
    """Cheap tissue gate: reject mostly white/background tiles."""
    rgb = tile.astype(np.float32)
    brightness = rgb.mean(axis=2)
    foreground = brightness < 245
    return float(foreground.mean()) >= min_fraction


def _cells_from_tile(tile: np.ndarray, offset_x: int, offset_y: int, tile_x: int, tile_y: int) -> list[WSICell]:
    gray = np.asarray(Image.fromarray(tile).convert("L"), dtype=np.float32)
    # This baseline is intentionally transparent and deterministic. A
    # validated Cellpose/StarDist adapter can replace it without changing the
    # result contract.
    mask = segment_binary_cells(gray, threshold=float(np.percentile(gray, 35)), min_area=20)
    cells: list[WSICell] = []
    for label in np.unique(mask):
        if label <= 0:
            continue
        ys, xs = np.where(mask == label)
        if not len(xs):
            continue
        cells.append(
            WSICell(
                cell_id=0,
                tile_x=tile_x,
                tile_y=tile_y,
                centroid_x_px=float(offset_x + xs.mean()),
                centroid_y_px=float(offset_y + ys.mean()),
                area_px=int(len(xs)),
                width_px=int(xs.max() - xs.min() + 1),
                height_px=int(ys.max() - ys.min() + 1),
            )
        )
    return cells


def analyze_wsi(
    path: str | Path,
    *,
    level: int = 0,
    tile_size: int = 1024,
    max_tiles: int = 256,
) -> dict[str, Any]:
    """Extract spatial cell morphology from a WSI without biological claims."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"WSI not found: {path}")
    if tile_size < 128 or tile_size > 4096:
        raise ValueError("tile_size must be between 128 and 4096")
    if max_tiles < 1:
        raise ValueError("max_tiles must be positive")

    slide = _open_wsi(path)
    try:
        dimensions = slide.level_dimensions[level]
        cells: list[WSICell] = []
        tissue_tiles = 0
        tile_count = 0
        width, height = dimensions

        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                if tile_count >= max_tiles:
                    break
                read_w = min(tile_size, width - x)
                read_h = min(tile_size, height - y)
                tile = np.asarray(slide.read_region((x, y), level, (read_w, read_h)).convert("RGB"))
                tile_count += 1
                if not _is_tissue(tile):
                    continue
                tissue_tiles += 1
                cells.extend(_cells_from_tile(tile, x, y, x // tile_size, y // tile_size))
            if tile_count >= max_tiles:
                break

        cells = [WSICell(i, c.tile_x, c.tile_y, c.centroid_x_px, c.centroid_y_px, c.area_px, c.width_px, c.height_px) for i, c in enumerate(cells, 1)]
        return WSIAnalysisResult(
            source=path.name,
            level=level,
            dimensions_px=dimensions,
            tile_size=tile_size,
            tissue_tiles=tissue_tiles,
            cells=cells,
            cell_type_status="not_established",
            disease_status="not_established",
            biological_age_status="not_established",
        ).to_dict()
    finally:
        slide.close()
