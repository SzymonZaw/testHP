from datetime import datetime

from digital_twin.assessment_trends import compare_cell_assessments
from digital_twin.cell_assessment import CellAssessment
from digital_twin.intervention_map import build_intervention_map, classify_priority


def test_worsening_high_abnormality_is_investigate():
    t0 = datetime(2026, 1, 1)
    t1 = datetime(2026, 2, 1)
    previous = CellAssessment("c1", t0, abnormality_score=.5)
    current = CellAssessment("c1", t1, abnormality_score=.7, uncertainty=.1)
    trend = compare_cell_assessments(previous, current)

    item = classify_priority(current, trend)

    assert item.priority == "investigate"
    assert item.reason == "high_or_worsening_abnormality"


def test_high_uncertainty_requests_better_measurement():
    current = CellAssessment("c2", datetime(2026, 1, 1), abnormality_score=.2, uncertainty=.8)
    assert classify_priority(current).priority == "improve_measurement"


def test_build_map_preserves_cell_ids():
    assessments = {
        "c1": CellAssessment("c1", datetime(2026, 1, 1), abnormality_score=.1),
        "c2": CellAssessment("c2", datetime(2026, 1, 1), abnormality_score=.8),
    }
    result = build_intervention_map(assessments)
    assert set(result) == {"c1", "c2"}
