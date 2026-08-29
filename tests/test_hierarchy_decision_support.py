from backend.biological_hierarchy import BiologicalHierarchy
from backend.decision_support import DecisionSupport
from backend.risk_model import RiskModel
from backend.risk_signal import RiskSignal


def test_hierarchy_exposes_decision_support_for_existing_node():
    hierarchy = BiologicalHierarchy.create_hand("hand-1")
    hierarchy = hierarchy.add_node("cell-1", "cell", "Cell 1", "hand-1")
    risk_model = RiskModel.from_signals((RiskSignal("marker", "elevated", 0.9, None, {"node_id": "cell-1"}),))

    result = hierarchy.decision_support("cell-1", risk_model)

    assert isinstance(result, DecisionSupport)
    assert result.action == "investigate"
    assert result.risk_level == "elevated"
    assert result.evidence["node_id"] == "cell-1"


def test_hierarchy_decision_support_rejects_unknown_node():
    hierarchy = BiologicalHierarchy.create_hand("hand-1")
    risk_model = RiskModel.from_signals(())

    try:
        hierarchy.decision_support("missing", risk_model)
    except ValueError as exc:
        assert str(exc) == "node does not exist: missing"
    else:
        raise AssertionError("expected ValueError")
