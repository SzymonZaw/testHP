from pathlib import Path

from datasets.dataset_registry import DatasetInfo
from datasets.fusion import fuse
from datasets.normalization import normalize_dataset


def test_normalization_includes_content_observations(tmp_path: Path):
    (tmp_path / "sample.csv").write_text("gene,sample\nTP53,1\nEGFR,2\n", encoding="utf-8")
    result = normalize_dataset(DatasetInfo("rna_sample", tmp_path, "rna"))
    features = {item.feature for item in result.observations}
    assert "preprocess.rna_sample.parsed_expression_tables" in features
    assert "preprocess.rna_sample.expression_rows" in features


def test_fusion_preserves_source_observations(tmp_path: Path):
    image_dir = tmp_path / "images"
    rna_dir = tmp_path / "rna"
    image_dir.mkdir()
    rna_dir.mkdir()
    (image_dir / "sample.jpg").write_bytes(b"not-a-real-jpeg")
    (rna_dir / "expr.csv").write_text("gene,value\nA,1\n", encoding="utf-8")
    image = normalize_dataset(DatasetInfo("images", image_dir, "image"))
    rna = normalize_dataset(DatasetInfo("rna", rna_dir, "rna"))
    result = fuse([image, rna])
    features = {item.feature for item in result.observations}
    assert "dataset.images.image_count" in features
    assert "preprocess.rna.expression_rows" in features
    assert "fusion.image.dataset_count" in features
    assert "fusion.rna.dataset_count" in features
