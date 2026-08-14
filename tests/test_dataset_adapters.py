from pathlib import Path

from datasets.adapters import ImageAdapter, InterHandAdapter, RNAAdapter, WSIAdapter


def test_image_adapter_counts_only_images(tmp_path: Path):
    (tmp_path / "a.jpg").write_bytes(b"123")
    (tmp_path / "b.png").write_bytes(b"12")
    (tmp_path / "notes.txt").write_text("ignore")
    result = ImageAdapter("demo", tmp_path).load()
    assert result.files == 2
    assert result.bytes == 5
    assert result.observations[0].feature == "dataset.demo.image_count"
    assert result.observations[0].value == 2


def test_wsi_adapter_supports_dicom_and_slide_files(tmp_path: Path):
    (tmp_path / "slide.dcm").write_bytes(b"abcd")
    (tmp_path / "slide.svs").write_bytes(b"abc")
    result = WSIAdapter("demo", tmp_path).load()
    assert result.files == 2
    assert result.modality == "wsi"


def test_rna_adapter_normalizes_present_source_files(tmp_path: Path):
    (tmp_path / "matrix.csv").write_text("gene,value\nA,1\n")
    (tmp_path / "matrix.mtx").write_text("1 1 1\n")
    result = RNAAdapter("GSETEST", tmp_path).load()
    assert result.files == 2
    assert all(item.modality == "rna" for item in result.observations)


def test_interhand_adapter_reads_small_annotation_metadata(tmp_path: Path):
    (tmp_path / "image.jpg").write_bytes(b"image")
    (tmp_path / "InterHand2.6M_train_data.json").write_text(
        '{"images": [{"id": 1}], "annotations": [{"id": 2}]}'
    )
    result = InterHandAdapter(tmp_path).load()
    features = {item.feature: item.value for item in result.observations}
    assert features["dataset.InterHand2_6M.image_count"] == 1
    assert features["dataset.InterHand2_6M.annotation_file_count"] == 1
    assert features["dataset.InterHand2_6M.annotation_entries"] == 2
