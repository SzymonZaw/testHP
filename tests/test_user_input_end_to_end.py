from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


def _package(*inputs: dict) -> dict:
    return {
        "contract_version": "1.0",
        "subject": {"subject_id": "user-001"},
        "acquisition": {
            "timepoint_id": "T0",
            "acquisition_time": "2026-08-29T10:00:00Z",
            "laterality": "right",
        },
        "inputs": list(inputs),
    }


def _input(kind: str, input_id: str = "input-001", fmt: str = "jpg") -> dict:
    return {
        "input_id": input_id,
        "kind": kind,
        "uri": f"uploads/{input_id}.{fmt}",
        "format": fmt,
        "provenance": {"source_type": "user"},
    }


def test_realistic_user_package_is_accepted_without_local_access() -> None:
    response = client.post(
        "/api/user-input/validate",
        json=_package(
            _input("hand_images", "hand-front"),
            _input("hand_images", "hand-back"),
            _input("hand_3d", "hand-mesh", "ply"),
            _input("tissue_wsi", "skin-wsi", "svs"),
            _input("single_cell_rna", "skin-scrna", "h5ad"),
            _input("proteomics", "skin-proteome", "csv"),
            _input("epigenetics", "skin-methylation", "tsv"),
            _input("ground_truth", "diagnosis", "json"),
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert set(body["available_modalities"]) == {
        "hand_images", "hand_3d", "tissue_wsi", "single_cell_rna",
        "proteomics", "epigenetics", "ground_truth",
    }
    assert "genomics" in body["missing_modalities"]
    assert body["evidence_status"] == "ground_truth"
    assert body["policy"] == {
        "uri_accessed": False,
        "raw_data_scanned": False,
        "database_queried": False,
        "missing_data_fabricated": False,
    }


def test_missing_modality_is_reported_not_fabricated() -> None:
    response = client.post(
        "/api/user-input/validate",
        json=_package(_input("hand_images")),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert "genomics" in body["missing_modalities"]
    assert "tissue_wsi" in body["missing_modalities"]
    assert "hand_images" in body["available_modalities"]
    assert body["policy"]["missing_data_fabricated"] is False


def test_invalid_package_is_rejected_deterministically() -> None:
    package = _package(_input("hand_images"))
    del package["acquisition"]["laterality"]
    package["inputs"][0]["provenance"] = {"source_type": "not-a-source"}

    response = client.post("/api/user-input/validate", json=package)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any(issue["path"] == "acquisition.laterality" for issue in body["issues"])
    assert any(issue["path"] == "inputs[0].provenance.source_type" for issue in body["issues"])
