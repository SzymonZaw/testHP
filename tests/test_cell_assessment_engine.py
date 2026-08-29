from backend.cell_assessment_engine import CellAssessmentEngine
from backend.hand_assessment import HandAssessment


def test_engine_connects_assessment_risk_and_decision_support():
    assessment = HandAssessment(
        overall_status="observe",
        ageing_signal="accelerated_change",
        health_signal="changing",
        function_signal="stable",
        relationship="health_change_without_function_change",
        affected_regions=("region-1",),
        evidence={
            "health_change_magnitude": 0.2,
            "function_change_magnitude": 0.0,
            "confidence": 0.9,
        },
    )

    engine = CellAssessmentEngine.from_assessment(assessment)

    assert engine.risk_model.overall_level == "high"
    assert engine.risk_model.confidence == 0.9
    assert engine.decision_support.action == "investigate"
    assert "health_change" in engine.risk_model.signal_types
    assert engine.decision_support.risk_level == "high"


def test_engine_preserves_insufficient_data():
    assessment = HandAssessment(
        overall_status="insufficient_data",
        ageing_signal="insufficient_data",
        health_signal="insufficient_data",
        function_signal="insufficient_data",
        relationship="insufficient_data",
        affected_regions=(),
        evidence={"confidence": 0.0},
    )

    engine = CellAssessmentEngine.from_assessment(assessment)

    assert engine.risk_model.overall_level == "insufficient_data"
    assert engine.decision_support.action == "insufficient_data"
