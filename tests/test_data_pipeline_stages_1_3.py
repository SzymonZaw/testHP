from pathlib import Path

from datasets.dataset_registry import DatasetInfo
from datasets.fusion import fuse
from datasets.normalization import normalize_dataset
from datasets.validation import validate_dataset


def test_validation_accepts_supported_image(tmp_path: Path):
    image = tmp_path / "sample.jpg"
    image.write_bytes(b"test")
    dataset = DatasetInfo("sample", tmp_path, "image")
    result = validate_dataset(dataset)
    assert result.valid
    assert result.files == 1
    assert result.supported_files == 1


def test_normalization_produces_common_observations(tmp_path: Path):
    (tmp_path / "sample.png").write_bytes(b"test")
    dataset = DatasetInfo("sample", tmp_path, "image")
    result = normalize_dataset(dataset)
    assert result.valid
    assert result.observations
    assert {item.modality for item in result.observations} == {"image"}


def test_fusion_does_not_invent_subject_links(tmp_path: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "a.jpg").write_bytes(b"a")
    (b / "b.svs").write_bytes(b"b")
    image = normalize_dataset(DatasetInfo("image_ds", a, "image"))
    wsi = normalize_dataset(DatasetInfo("wsi_ds", b, "wsi"))
    result = fuse([image, wsi])
    assert set(result.modalities) == {"image", "wsi"}
    assert result.linked_subjects == 0
    assert result.warnings
