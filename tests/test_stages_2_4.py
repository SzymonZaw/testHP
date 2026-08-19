from backend.stage_2_4 import _age_summary, _aggregate, _clean_signals


def test_clean_signals_drops_unknown_keys():
    result = _clean_signals({"macro_age": 41, "unknown": 99, "elasticity": 70})
    assert result == {"macro_age": 41.0, "elasticity": 70.0}


def test_age_summary_is_explicit_only():
    result = _age_summary({"macro_age": {"value": 41, "n": 1, "status": "observed"}})
    assert result["overall"] == 41
    assert result["layers"]["tissue"]["status"] == "not_established"


def test_hierarchy_aggregates_descendant_evidence():
    items = [
        {"spatial_node_id": "hand/palm/thenar/field-b/cell-1", "signals": {"cell_age": 40}, "layers": ["cellular"]},
        {"spatial_node_id": "hand/palm/thenar/field-b/cell-2", "signals": {"cell_age": 44}, "layers": ["cellular"]},
        {"spatial_node_id": "hand/palm/thenar", "signals": {"tissue_age": 42}, "layers": ["tissue"]},
    ]
    result = _aggregate(items, "hand/palm/thenar")
    assert result["nodes"][0]["node_id"] == "hand"
    assert result["nodes"][-1]["biological_age"]["overall"] == 42.0
