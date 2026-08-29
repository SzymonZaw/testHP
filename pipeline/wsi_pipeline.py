"""End-user WSI -> cell/tissue evidence pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from segmentation.cell_segmentation import segment_binary_cells
from pipeline.cell_tissue_pipeline import build_cell_tissue_context

try:
    import openslide  # type: ignore
except ImportError:  # pragma: no cover
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
    microenvironment_status: str
    tissue_state_status: str
    disease_status: str
    biological_age_status: str

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "cells": [asdict(c) for c in self.cells], "dimensions_px": list(self.dimensions_px)}


def _open_wsi(path: Path):
    if openslide is None:
        raise RuntimeError("WSI support requires the optional 'openslide-python' package.")
    try:
        return openslide.OpenSlide(str(path))
    except Exception as exc:
        raise RuntimeError(f"could not open WSI {path.name}: {exc}") from exc


def _is_tissue(tile: np.ndarray, min_fraction: float = 0.10) -> bool:
    brightness = tile.astype(np.float32).mean(axis=2)
    return float((brightness < 245).mean()) >= min_fraction


def _cells_from_tile(tile: np.ndarray, offset_x: int, offset_y: int, tile_x: int, tile_y: int) -> list[WSICell]:
    gray = np.asarray(Image.fromarray(tile).convert("L"), dtype=np.float32)
    mask = segment_binary_cells(gray, threshold=float(np.percentile(gray, 35)), min_area=20)
    cells: list[WSICell] = []
    for label in np.unique(mask):
        if label <= 0:
            continue
        ys, xs = np.where(mask == label)
        if not len(xs):
            continue
        cells.append(WSICell(0, tile_x, tile_y, float(offset_x + xs.mean()), float(offset_y + ys.mean()), int(len(xs)), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)))
    return cells


def analyze_wsi(path: str | Path, *, level: int = 0, tile_size: int = 1024, max_tiles: int = 256) -> dict[str, Any]:
    """Extract spatial cell morphology and conservative tissue context."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"WSI not found: {path}")
    if tile_size < 128 or tile_size > 4096:
        raise ValueError("tile_size must be between 128 and 4096")
    if max_tiles < 1:
        raise ValueError("max_tiles must be positive")

    slide = _open_wsi(path)
    try:
        if level < 0 or level >= len(slide.level_dimensions):
            raise ValueError(f"invalid WSI level: {level}")
        dimensions = slide.level_dimensions[level]
        cells: list[WSICell] = []
        tissue_tiles = 0
        tile_count = 0
        width, height = dimensions
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                if tile_count >= max_tiles:
                    break
                read_w, read_h = min(tile_size, width - x), min(tile_size, height - y)
                tile = np.asarray(slide.read_region((x, y), level, (read_w, read_h)).convert("RGB"))
                tile_count += 1
                if not _is_tissue(tile):
                    continue
                tissue_tiles += 1
                cells.extend(_cells_from_tile(tile, x, y, x // tile_size, y // tile_size))
            if tile_count >= max_tiles:
                break

        cells = [WSICell(i, c.tile_x, c.tile_y, c.centroid_x_px, c.centroid_y_px, c.area_px, c.width_px, c.height_px) for i, c in enumerate(cells, 1)]
        context = build_cell_tissue_context(cells, region_tile_size_px=tile_size)
        result = WSIAnalysisResult(path.name, level, dimensions, tile_size, tissue_tiles, cells, context["cell_type_status"], context["microenvironment_status"], context["tissue_state_status"], context["disease_status"], context["biological_age_status"]).to_dict()
        result["cell_context"] = context["cells"]
        result["tissue_regions"] = context["tissue_regions"]
        return result
    finally:
        slide.close()
