from dataclasses import dataclass

import pytest

from pipeline.cell_tissue_pipeline import build_cell_tissue_context


@dataclass
class Cell:
    cell_id: int
    centroid_x_px: float
    centroid_y_px: float
    area_px: int


def test_cells_get_spatial_context_and_regions():
    result = build_cell_tissue_context([
        Cell(1, 100, 100, 50),
        Cell(2, 130, 100, 60),
        Cell(3, 1800, 100, 80),
    ], neighbor_radius_px=50, region_tile_size_px=1024)

    assert len(result["cells"]) == 3
    assert len(result["tissue_regions"]) == 2
    assert result["cells"][0]["nearest_neighbor_count"] == 1
    assert result["cells"][0]["neighborhood"] == "sparse"
    assert result["cells"][0]["cell_type"] == "not_established"
    assert result["disease_status"] == "not_established"


def test_invalid_spatial_parameters_are_rejected():
    with pytest.raises(ValueError):
        build_cell_tissue_context([], neighbor_radius_px=0)
    with pytest.raises(ValueError):
        build_cell_tissue_context([], region_tile_size_px=0)
