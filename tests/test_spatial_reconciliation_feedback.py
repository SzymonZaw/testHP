from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICALIZER = ROOT / "frontend" / "digital-twin" / "spatial-target-canonicalizer.js"


def test_spatial_target_canonicalizer_is_process_wide_idempotent():
    source = CANONICALIZER.read_text(encoding="utf-8")
    assert "if (window.__testhpSpatialTargetCanonicalizerInstalled) return;" in source
    assert "window.__testhpSpatialTargetCanonicalizerInstalled = true;" in source


def test_spatial_target_reconcile_does_not_reenter_contract_event_publication():
    source = CANONICALIZER.read_text(encoding="utf-8")
    assert "Do not call contract.reconcile() here." in source
    assert "api?.reconcile()" not in source


def test_spatial_target_mutation_reconciliation_is_coalesced_and_child_list_only():
    source = CANONICALIZER.read_text(encoding="utf-8")
    assert "let reconcileScheduled = false;" in source
    assert "queueMicrotask(() =>" in source
    assert "m.type === 'childList'" in source
    assert "attributeFilter" not in source
