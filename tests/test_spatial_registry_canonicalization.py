from backend import observation_routes


def test_spatial_registry_matches_display_alias_to_canonical_target(monkeypatch):
    monkeypatch.setattr(
        observation_routes,
        "registry_status",
        lambda: {
            "assets": [
                {
                    "asset_id": "asset-palm",
                    "evidence_id": "evidence-palm",
                    "spatial_node_id": "palm",
                    "subject_id": "own_cohort",
                    "timepoint": "T0",
                    "attachment_status": "explicit",
                    "spatially_localized": True,
                }
            ]
        },
    )

    payload = observation_routes.spatial_registry(
        subject_id="own_cohort",
        timepoint="T0",
        spatial_node_id="Śródręcze",
        debug=True,
    )

    assert payload["scope"] == "hand/palm"
    assert payload["count"] == 1
    assert payload["items"][0]["spatial_node_id"] == "hand/palm"
    assert payload["debug"]["accepted_count"] == 1
    assert payload["debug"]["rejected_count"] == 0
    assert payload["debug"]["decisions"][0]["reason"] == "EXACT_SPATIAL_NODE_MATCH"


def test_spatial_registry_does_not_turn_root_attachment_into_deep_attachment(monkeypatch):
    monkeypatch.setattr(
        observation_routes,
        "registry_status",
        lambda: {
            "assets": [
                {
                    "asset_id": "asset-hand",
                    "evidence_id": "evidence-hand",
                    "spatial_node_id": "hand",
                    "subject_id": "own_cohort",
                    "timepoint": "T0",
                    "attachment_status": "registered_root",
                    "spatially_localized": False,
                }
            ]
        },
    )

    payload = observation_routes.spatial_registry(
        subject_id="own_cohort",
        timepoint="T0",
        spatial_node_id="Palm",
        debug=True,
    )

    assert payload["scope"] == "hand/palm"
    assert payload["count"] == 0
    assert payload["debug"]["rejected_count"] == 1
    assert payload["debug"]["decisions"][0]["reason"] == "ROOT_OR_ANCESTOR_ATTACHMENT_NOT_DEEP_ATTACHED"
