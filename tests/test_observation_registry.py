from backend.observation_registry import create_observation, get_observation, update_observation


def test_observation_create_and_update(tmp_path, monkeypatch):
    import backend.observation_registry as registry

    monkeypatch.setattr(registry, "REGISTRY_ROOT", tmp_path)
    item = create_observation({
        "subject_id": "own_cohort",
        "timepoint": "T0",
        "spatial_id": "hand/palm/hypothenar/field-a",
        "location_name": "Microscopy field A",
        "biological_level": "cellular",
        "modality": "microscopy",
        "name": "Cell density",
        "value": {"count": 33, "unit": "cells/mm2"},
        "source": "manual-entry",
    })

    assert item["version"] == 1
    assert item["status"] == "active"
    assert get_observation(item["id"])["name"] == "Cell density"

    updated = update_observation(item["id"], {"value": {"count": 34, "unit": "cells/mm2"}, "notes": "recounted"})
    assert updated["version"] == 2
    assert updated["value"]["count"] == 34
    assert len(updated["audit"]) == 2
