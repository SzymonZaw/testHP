import json

import pytest

from backend import observation_registry


def test_validated_interpretation_requires_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(observation_registry, "REGISTRY_ROOT", tmp_path)
    with pytest.raises(ValueError, match="validated_interpretations require an explicit evidence_id"):
        observation_registry.create_observation({
            "subject_id": "own_cohort",
            "timepoint": "T0",
            "spatial_id": "hand/palm",
            "biological_level": "macro",
            "name": "Research interpretation",
            "validated_interpretations": {"damage": "Observed"},
        })


def test_validated_interpretation_is_persisted_and_audited(tmp_path, monkeypatch):
    monkeypatch.setattr(observation_registry, "REGISTRY_ROOT", tmp_path)
    item = observation_registry.create_observation({
        "subject_id": "own_cohort",
        "timepoint": "T0",
        "spatial_id": "hand/palm",
        "biological_level": "macro",
        "name": "Macro evidence",
        "evidence_id": "evidence-1",
    })
    updated = observation_registry.update_observation(
        item["id"],
        {
            "validated_interpretations": {"damage": "Brak cech uszkodzenia w ocenianym materiale"},
            "author": "researcher",
        },
    )
    assert updated["validated_interpretations"]["damage"] == "Brak cech uszkodzenia w ocenianym materiale"
    assert updated["version"] == 2
    assert updated["audit"][-1]["author"] == "researcher"
    stored = json.loads((tmp_path / f"{item['id']}.json").read_text(encoding="utf-8"))
    assert stored["validated_interpretations"]["damage"] == "Brak cech uszkodzenia w ocenianym materiale"
