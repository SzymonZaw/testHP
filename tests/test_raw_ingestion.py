from pathlib import Path

from backend.raw_ingestion import artifact_records, infer_modality, scan_raw


def test_infer_modality():
    assert infer_modality(Path("hand/media/example.mp4")) == "video"
    assert infer_modality(Path("hand/own_cohort/front.jpg")) == "image"
    assert infer_modality(Path("rna/expression.tsv")) == "rna"
    assert infer_modality(Path("wsi/slide.tiff")) == "wsi"


def test_scan_raw_is_non_destructive(tmp_path: Path):
    root = tmp_path / "raw"
    source = root / "hand" / "media" / "sample.mp4"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"video")

    records = scan_raw(root)

    assert source.exists()
    assert records == [
        {
            "path": str(source),
            "relative_path": "hand/media/sample.mp4",
            "modality": "video",
            "size_bytes": 5,
        }
    ]


def test_artifact_records(tmp_path: Path):
    root = tmp_path / "raw"
    source = root / "images" / "normal_skin" / "skin.jpg"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"image")

    records = artifact_records(root)
    assert records[0]["relative_path"] == "images/normal_skin/skin.jpg"
    assert records[0]["modality"] == "image"
