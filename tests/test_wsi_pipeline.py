from pathlib import Path

import numpy as np
from PIL import Image

import pipeline.wsi_pipeline as wsi_pipeline


class _FakeSlide:
    level_dimensions = [(256, 256)]

    def read_region(self, location, level, size):
        width, height = size
        image = np.full((height, width, 3), 255, dtype=np.uint8)
        # Tissue-like patch with deterministic cell-like bright/dark structure.
        image[20:min(120, height), 20:min(120, width)] = 100
        image[45:min(65, height), 45:min(65, width)] = 220
        return Image.fromarray(image, mode="RGB")

    def close(self):
        pass


def test_analyze_wsi_returns_spatial_cells(monkeypatch, tmp_path: Path):
    source = tmp_path / "sample.svs"
    source.write_bytes(b"placeholder")
    monkeypatch.setattr(wsi_pipeline, "openslide", type("OpenSlideModule", (), {"OpenSlide": lambda _: _FakeSlide()}))

    result = wsi_pipeline.analyze_wsi(source, tile_size=128, max_tiles=4)

    assert result["dimensions_px"] == [256, 256]
    assert result["tissue_tiles"] >= 1
    assert result["cells"]
    assert result["cells"][0]["centroid_x_px"] >= 0
    assert result["cells"][0]["centroid_y_px"] >= 0
    assert result["cell_type_status"] == "not_established"
    assert result["disease_status"] == "not_established"
    assert result["biological_age_status"] == "not_established"


def test_wsi_requires_openslide_for_real_files(monkeypatch, tmp_path: Path):
    source = tmp_path / "sample.svs"
    source.write_bytes(b"placeholder")
    monkeypatch.setattr(wsi_pipeline, "openslide", None)

    try:
        wsi_pipeline.analyze_wsi(source)
    except RuntimeError as exc:
        assert "openslide-python" in str(exc)
    else:
        raise AssertionError("Expected a clear missing-OpenSlide error")
