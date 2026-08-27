from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_stage_11_20_catalog():
    response = client.get("/api/hand/stages-11-20")
    assert response.status_code == 200
    stages = response.json()["stages"]
    assert [item["stage"] for item in stages] == list(range(11, 21))


def test_cell_segmentation_requires_real_source_and_cells():
    payload = {
        "subject_id": "s1",
        "hand_id": "h1",
        "timepoint_id": "t0",
        "source": "histology",
        "source_asset_id": "asset-histo-1",
        "method": "manual",
        "cells": [{
            "cell_id": "cell-1",
            "position": [1.0, 2.0, 3.0],
            "tissue": "dermis",
            "morphology": {"area": 10.2},
            "nucleus": {},
            "neighbors": [],
            "coordinate_frame": "HAND_COORDINATE_SYSTEM",
            "confidence": 0.9,
        }],
        "provenance": {"method_version": "1"},
        "quality": {"status": "acceptable"},
        "confidence": 0.9,
    }
    response = client.post("/api/hand/cells/segmentations", json=payload)
    assert response.status_code == 200
    assert response.json()["stage"] == 11
    assert response.json()["cell_count"] == 1


def test_state_requires_evidence():
    response = client.post("/api/hand/cells/states", json={
        "subject_id": "s1", "hand_id": "h1", "timepoint_id": "t0",
        "source": "pathology", "cell_id": "cell-1", "state": "unknown",
        "evidence_object_ids": ["obs-1"], "method": "expert_annotation",
        "confidence": 0.5,
    })
    assert response.status_code == 200
    assert response.json()["evidence_ids"] == ["obs-1"]
