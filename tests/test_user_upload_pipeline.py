from types import SimpleNamespace

from backend.user_upload_routes import _kind, _package


def test_user_upload_modalities_map_to_user_contract():
    assert _kind("hand", None) == "hand_images"
    assert _kind("video", None) == "hand_video"
    assert _kind("wsi", "skin") == "tissue_wsi"
    assert _kind("rna", "single_cell") == "single_cell_rna"
    assert _kind("rna", "bulk") == "bulk_rna"


def test_user_package_uses_application_uri_not_local_path():
    asset = SimpleNamespace(
        asset_id="user_asset_123",
        subject_id="subject_a",
        timepoint="T0",
        created_at="2026-08-29T17:00:00+00:00",
        filename="hand.jpg",
        size_bytes=1234,
    )
    package = _package(asset, "right", "hand_images")
    item = package["inputs"][0]
    assert item["uri"] == "upload://user_asset_123"
    assert "stored_path" not in item["metadata"]
    assert package["acquisition"]["laterality"] == "right"
