from pathlib import Path

from backend.macro_analysis import analyze_image


def test_macro_analysis_extracts_reproducible_features(tmp_path: Path):
    from PIL import Image

    image_path = tmp_path / "hand.jpg"
    Image.new("RGB", (100, 50), (120, 120, 120)).save(image_path)

    result = analyze_image(image_path)

    assert result["status"] == "ok"
    assert result["features"]["width_px"] == 100
    assert result["features"]["height_px"] == 50
    assert result["features"]["aspect_ratio"] == 2.0
    assert "diagnosis" not in result


def test_macro_analysis_missing_file_is_safe(tmp_path: Path):
    result = analyze_image(tmp_path / "missing.jpg")
    assert result["status"] == "unavailable"
