"""Adapters that expose Photo 3D data through the shared spatial contract.

This module deliberately contains no reconstruction algorithm. It translates
stage 1-5 photo records into canonical observation/prepared/registered IDs so
later reconstruction stages can publish a SpatialObject without duplicating
Hand Surface concepts.
"""
from __future__ import annotations

from typing import Any

from .spatial_contract import (
    lifecycle,
    make_photo_asset_id,
    make_prepared_photo_asset_id,
    make_registered_view_id,
    observation_id,
)


def photo_record_to_spatial(record: dict[str, Any]) -> dict[str, Any]:
    """Return a canonical, read-only projection of one photo record."""
    asset_id = str(record["asset_id"])
    prepared_id = record.get("prepared_asset_id")
    view = record.get("view")
    registration = record.get("registration") or {}
    registered_id = (
        make_registered_view_id(make_prepared_photo_asset_id(asset_id), str(view))
        if prepared_id and view and registration.get("status") == "registered"
        else None
    )
    return {
        "observation_id": observation_id(make_photo_asset_id(asset_id)),
        "photo_asset_id": make_photo_asset_id(asset_id),
        "prepared_photo_asset_id": make_prepared_photo_asset_id(asset_id) if prepared_id else None,
        "registered_view_id": registered_id,
        "subject_id": record.get("subject_id", ""),
        "timepoint_id": record.get("timepoint", ""),
        "view": view,
        "status": lifecycle(str(record.get("status", "created"))),
        "source_uri": record.get("path"),
        "prepared_uri": record.get("prepared_path"),
        "coordinate_system": registration.get("coordinate_system", "hand-surface-v1"),
        "registration": registration or None,
        "quality": record.get("quality"),
        "provenance": {
            "filename": record.get("filename"),
            "view_source": record.get("view_source"),
            "background_method": record.get("background_method"),
        },
    }


def spatial_input_set(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the shared input set consumed by downstream spatial modules."""
    projected = [photo_record_to_spatial(record) for record in records]
    return {
        "schema": "spatial-photo-input-v1",
        "observations": projected,
        "photo_asset_ids": [x["photo_asset_id"] for x in projected],
        "prepared_photo_asset_ids": [x["prepared_photo_asset_id"] for x in projected if x["prepared_photo_asset_id"]],
        "registered_view_ids": [x["registered_view_id"] for x in projected if x["registered_view_id"]],
        "ready_count": sum(x["status"] == "registered" for x in projected),
    }
