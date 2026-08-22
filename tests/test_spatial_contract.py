from backend.photo_reconstruction_spatial import photo_record_to_spatial, spatial_input_set
from backend.spatial_contract import (
    lifecycle,
    make_photo_asset_id,
    make_prepared_photo_asset_id,
    make_registered_view_id,
    make_reconstruction_id,
    make_spatial_object_id,
    observation_id,
)


def test_shared_ids_are_deterministic():
    assert make_photo_asset_id("a1") == "photo:a1"
    assert make_prepared_photo_asset_id("a1") == "prepared-photo:a1"
    assert make_registered_view_id("prepared-photo:a1", "front") == "registered-view:prepared-photo:a1:front"
    assert observation_id("photo:a1") == "observation:photo:a1"
    assert make_reconstruction_id("s", "T0", "abc") == "reconstruction:s:T0:abc"
    assert make_spatial_object_id("s", "reconstruction:s:T0:abc") == "spatial-hand:s:reconstruction:s:T0:abc"


def test_lifecycle_normalizes_existing_photo_statuses():
    assert lifecycle("uploaded") == "created"
    assert lifecycle("prepared") == "prepared"
    assert lifecycle("needs-registration-review") == "needs_review"
    assert lifecycle("registered") == "registered"


def test_photo_record_maps_to_shared_spatial_contract():
    record = {
        "asset_id": "a1",
        "subject_id": "subject-1",
        "timepoint": "T0",
        "filename": "front.jpg",
        "path": "data/front.jpg",
        "prepared": True,
        "prepared_asset_id": "prepared_123",
        "prepared_path": "data/prepared/front.png",
        "view": "front",
        "view_source": "filename",
        "status": "registered",
        "quality": {"overall": 0.9},
        "background_method": "adaptive-border-separation",
        "registration": {"status": "registered", "coordinate_system": "hand-surface-v1"},
    }
    mapped = photo_record_to_spatial(record)
    assert mapped["photo_asset_id"] == "photo:a1"
    assert mapped["prepared_photo_asset_id"] == "prepared-photo:a1"
    assert mapped["registered_view_id"] == "registered-view:prepared-photo:a1:front"
    assert mapped["observation_id"] == "observation:photo:a1"
    assert mapped["status"] == "registered"


def test_spatial_input_set_does_not_create_duplicate_photo_entities():
    records = [
        {"asset_id": "a1", "subject_id": "s", "timepoint": "T0", "status": "prepared", "prepared_asset_id": "p1", "view": "front"},
        {"asset_id": "a2", "subject_id": "s", "timepoint": "T0", "status": "registered", "prepared_asset_id": "p2", "view": "back", "registration": {"status": "registered"}},
    ]
    result = spatial_input_set(records)
    assert result["photo_asset_ids"] == ["photo:a1", "photo:a2"]
    assert result["prepared_photo_asset_ids"] == ["prepared-photo:a1", "prepared-photo:a2"]
    assert result["registered_view_ids"] == ["registered-view:prepared-photo:a2:back"]
    assert result["ready_count"] == 1
