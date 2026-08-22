from backend.stage_2_4 import _aggregate, _canonical_node_id, _node_matches, _safe_node


def test_legacy_deep_target_canonicalizes_to_viewport_id():
    assert _canonical_node_id("hand/palm/hypothenar-eminence") == "hand/palm/hypothenar"
    assert _safe_node("hand/palm/hypothenar-eminence") == "hand/palm/hypothenar"


def test_registry_matching_accepts_legacy_and_canonical_ids_as_same_node():
    item = {
        "evidence_id": "evidence-1",
        "spatial_node_id": "hand/palm/hypothenar-eminence",
    }
    assert _node_matches(item, "hand/palm/hypothenar")
    assert _node_matches(item, "hand/palm/hypothenar-eminence")


def test_hierarchical_summary_does_not_split_legacy_deep_node():
    items = [
        {
            "evidence_id": "evidence-1",
            "spatial_node_id": "hand/palm/hypothenar-eminence",
            "signals": {"tissue_age": 42},
            "layers": ["tissue"],
            "spatially_localized": True,
        }
    ]
    summary = _aggregate(items, "hand/palm/hypothenar")
    hypothenar = next(node for node in summary["nodes"] if node["node_id"] == "hand/palm/hypothenar")
    assert hypothenar["evidence_count"] == 1
    assert hypothenar["signals"]["tissue_age"]["value"] == 42.0
