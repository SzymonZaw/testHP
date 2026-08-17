from pathlib import Path

import backend.dataset_manager as dm


def test_create_dataset_creates_manifest(tmp_path: Path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(dm, "ROOT", root)
    monkeypatch.setattr(dm, "REGISTRY_PATH", root / "data" / "registry" / "datasets.json")
    monkeypatch.setattr(dm, "DATASET_ROOT", root / "data" / "raw")

    created = dm.create_dataset(
        name="my cohort",
        modality="hand",
        description="Longitudinal hand cohort",
        source="own cohort",
        version="1.0",
        tags=["hand", "longitudinal"],
    )

    assert created["dataset_id"].startswith("DS-")
    assert created["status"] == "draft"
    assert Path(created["root_path"]).exists() is False  # relative to process root, not temp root
    manifest = dm.manifest(created["dataset_id"])
    assert manifest["records"] == []
    assert manifest["modality"] == "hand"


def test_refresh_manifest_tracks_files(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(dm, "ROOT", tmp_path)
    monkeypatch.setattr(dm, "REGISTRY_PATH", tmp_path / "data" / "registry" / "datasets.json")
    monkeypatch.setattr(dm, "DATASET_ROOT", tmp_path / "data" / "raw")

    created = dm.create_dataset(name="images", modality="image")
    record = dm.get_dataset(created["dataset_id"])
    dataset_root = tmp_path / record["root_path"]
    dataset_root.joinpath("T0").mkdir(parents=True)
    dataset_root.joinpath("T0", "front.jpg").write_bytes(b"image")
    dataset_root.joinpath("T0", "empty.jpg").write_bytes(b"")

    manifest = dm.refresh_manifest(created["dataset_id"])
    assert len(manifest["records"]) == 2
    assert sum(x["status"] == "available" for x in manifest["records"]) == 1
    assert dm.get_dataset(created["dataset_id"])["status"] == "ready"
