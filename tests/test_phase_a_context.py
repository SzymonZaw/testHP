from pathlib import Path

from backend.observation_routes import _in_spatial_scope


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "frontend" / "digital-twin" / "spatial-contract.js"


def test_region_scope_is_direct_by_default():
    assert _in_spatial_scope("hand/palm", "hand/palm", False) is True
    assert _in_spatial_scope("hand/palm", "hand/palm/thenar", False) is False
    assert _in_spatial_scope("hand/palm", "hand/thumb", False) is False


def test_region_scope_can_explicitly_include_descendants():
    assert _in_spatial_scope("hand/palm", "hand/palm/thenar", True) is True
    assert _in_spatial_scope("hand/palm", "hand/thumb", True) is False


def test_phase_a_frontend_contract_defines_one_canonical_target_channel():
    source = CONTRACT.read_text(encoding="utf-8")
    assert "window.selectedSpatialNode = canonical" in source
    assert "window.spatialEvidenceTarget = canonical" in source
    assert "window.testhpSpatialTarget = canonical" in source
    assert "manager.state.spatial_id = canonical" in source
    assert "manager.spatialTarget = canonical" in source


def test_phase_a_frontend_contract_normalizes_palm_aliases():
    source = CONTRACT.read_text(encoding="utf-8")
    assert "palm: 'hand/palm'" in source
    assert "'śródręcze': 'hand/palm'" in source
    assert "srodrecze: 'hand/palm'" in source
