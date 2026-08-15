from __future__ import annotations

from pathlib import Path

from PIL import Image

from backend.multiscale_pipeline import EvidenceRecord, DigitalTwinState, analyze_images, fuse_explicit


def test_image_adapter_emits_macroscopic_observations(tmp_path: Path):
    image_path = tmp_path / "skin.jpg"
    Image.new("RGB", (20, 10), (100, 150, 200)).save(image_path)

    records = analyze_images(tmp_path, subject_id="subject-1")

    assert records
    assert any(r.metric == "image_width" and r.value == 20 for r in records)
    assert all(r.subject_id == "subject-1" for r in records)
    assert all(r.modality == "images" for r in records)


def test_twin_has_stable_hand_zones_and_history():
    twin = DigitalTwinState(subject_id="subject-1")
    twin.ensure_hand_zones()
    twin.add_timepoint("T0", [])

    assert set(twin.zones) == {"wrist", "palm", "thumb", "index", "middle", "ring", "little"}
    assert twin.history[0]["timepoint"] == "T0"


def test_fusion_rejects_records_without_explicit_subject_link():
    linked = EvidenceRecord("subject-1", "a", "images", "surface", "hand.palm", "observation", "brightness", 0.5)
    unlinked = EvidenceRecord(None, "b", "rna", "molecular", None, "observation", "numeric_max", 10)

    result = fuse_explicit([linked, unlinked])

    assert len(result["linked_groups"]) == 1
    assert result["linked_groups"][0]["subject_id"] == "subject-1"
    assert result["rejected_unlinked_records"][0]["reason"] == "missing_subject_id"
    assert result["interpretation"] == "not established"
