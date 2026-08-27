import os

import pytest

from backend.canonical_ingestion import canonicalize_asset, register_canonical_asset
from backend.data_ingestion import DataAsset


pytestmark = pytest.mark.integration


def _asset() -> DataAsset:
    return DataAsset(
        asset_id="asset_test_postgres_001",
        subject_id="test_subject",
        timepoint="T0",
        modality="hand",
        subtype=None,
        view="front",
        path="data/raw/hand/test_subject/T0/front.png",
        filename="front.png",
        size_bytes=123,
        status="available",
        created_at="2026-08-27T00:00:00+00:00",
        source="test",
    )


def test_canonicalize_asset_keeps_hierarchy_metadata():
    obj = canonicalize_asset(_asset())
    assert obj.subject_id == "test_subject"
    assert obj.timepoint_id == "T0"
    assert obj.metadata["hand_id"].startswith("hand_")
    assert obj.spatial_reference.frame_id == "hand-frame:test_subject:T0"


def test_postgresql_round_trip():
    if not os.getenv("TESTHP_DATABASE_URL"):
        pytest.skip("TESTHP_DATABASE_URL is required for PostgreSQL integration tests")

    obj = register_canonical_asset(_asset())

    from backend.database import connect

    with connect() as conn:
        subject = conn.execute("SELECT subject_id FROM subjects WHERE subject_id=%s", (obj.subject_id,)).fetchone()
        dataset = conn.execute("SELECT dataset_id, hand_id, timepoint_id FROM datasets WHERE dataset_id=%s", (obj.data_id,)).fetchone()

    assert subject is not None
    assert dataset is not None
    assert dataset["hand_id"] == obj.metadata["hand_id"]
    assert dataset["timepoint_id"] == obj.timepoint_id
