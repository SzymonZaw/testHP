from pathlib import Path

from backend import observation_routes
from backend.observation_registry import _canonical_spatial_id
from backend.stage_2_4 import _direct_state, _node_match_debug


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "frontend" / "digital-twin" / "spatial-contract.js"
OVERLAY = ROOT / "frontend" / "digital-twin" / "spatial-evidence-overlay-fallback.js"


def test_frontend_contract_keeps_manager_and_legacy_channels_on_one_id():
    source = CONTRACT.read_text(encoding="utf-8")
    assert "manager.state.spatialTarget = canonical" in source
    assert "manager.spatialTarget = canonical" in source
    assert "window.selectedSpatialNode = canonical" in source
    assert "window.spatialEvidenceTarget = canonical" in source
    assert "window.testhpSpatialTarget = canonical" in source
    assert "body.dataset.spatialTarget = canonical" in source
    assert "ROOT_ALIASES" in source
    assert "digital-twin:target-changed" in source


def test_human_spatial_aliases_resolve_to_one_canonical_id():
    assert _canonical_spatial_id("Palm") == "hand/palm"
    assert _canonical_spatial_id("Śródręcze") == "hand/palm"
    assert _canonical_spatial_id("srodrecze") == "hand/palm"
    assert _canonical_spatial_id("/hand/palm/") == "hand/palm"
    assert _canonical_spatial_id("hand/palm/thenar-eminence") == "hand/palm/thenar"


def test_root_registered_evidence_is_not_treated_as_deep_attachment():
    item = {
        "evidence_id": "registered_raw_1",
        "asset_id": "raw_1",
        "spatial_node_id": "hand",
        "attachment_status": "registered_root",
        "spatially_localized": False,
    }
    decision = _node_match_debug(item, "hand/palm/hypothenar/hypothenar-field-a")
    assert decision["matched"] is False
    assert decision["reason"] == "ROOT_ONLY_REGISTERED_ASSET_NOT_DEEP_ATTACHED"


def test_exact_deep_attachment_matches_only_the_same_canonical_node():
    item = {
        "evidence_id": "evidence_1",
        "asset_id": "asset_1",
        "spatial_node_id": "hand/palm/hypothenar/hypothenar-field-a",
        "attachment_status": "explicit",
        "spatially_localized": True,
        "signals": {"cell_age": 42},
        "layers": ["cellular"],
    }
    decision = _node_match_debug(item, "hand/palm/hypothenar/hypothenar-field-a")
    assert decision["matched"] is True
    assert decision["reason"] == "EXACT_SPATIAL_ID_MATCH"

    state = _direct_state([item], "hand/palm/hypothenar/hypothenar-field-a")
    assert state["evidence_count"] == 1
    assert state["localized_evidence_count"] == 1
    assert state["signals"]["cell_age"]["value"] == 42


def test_deep_target_does_not_inherit_root_evidence():
    root = {
        "spatial_node_id": "hand",
        "signals": {"macro_age": 50},
        "layers": ["macro"],
        "spatially_localized": False,
    }
    state = _direct_state([root], "hand/palm/hypothenar/hypothenar-field-a")
    assert state["evidence_count"] == 0
    assert state["insufficient_evidence"] is True


def test_spatial_registry_uses_stable_exact_match_reason(monkeypatch):
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
        spatial_node_id="hand",
        debug=True,
    )
    assert payload["count"] == 1
    assert payload["debug"]["decisions"][0]["reason"] == "EXACT_SPATIAL_NODE_MATCH"


def test_visual_overlay_fallback_is_a_disabled_compatibility_shim():
    source = OVERLAY.read_text(encoding="utf-8")
    assert "Projection ownership belongs to photo-surface-projection.js" in source
    assert "disabled: true" in source
    assert "projection-owned-by-photo-surface-projection" in source
    assert "/api/spatial/registry" not in source
