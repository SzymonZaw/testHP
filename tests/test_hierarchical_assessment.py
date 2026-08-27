from datetime import datetime

from digital_twin.cell_assessment import CellAssessment
from digital_twin.hierarchical_assessment import aggregate_assessments
from digital_twin.spatial import CellLocation, HandRegion, HandSpatialModel, SpatialPoint, TissueRegion
from digital_twin.assessment_trends import compare_cell_assessments, compare_level_assessments


def model():
    hand = HandSpatialModel()
    region = HandRegion(region_id="palm", name="Palm", side="left")
    tissue = TissueRegion(tissue_id="skin", tissue_type="skin", region_id="palm")
    for cid, x in (("c1", 1.0), ("c2", 2.0)):
        tissue.add_cell(CellLocation(cid, SpatialPoint(x, 0, 0), tissue_id="skin"))
    region.add_tissue(tissue)
    hand.add_region(region)
    return hand


def test_hierarchy_aggregates_cells_to_tissue_region_and_hand():
    t = datetime(2026, 1, 1)
    assessments = {
        "c1": CellAssessment("c1", t, "healthy", .9, 30, .9, .1, .05),
        "c2": CellAssessment("c2", t, "abnormal", .5, 50, .8, .5, .2),
    }
    result = aggregate_assessments(model(), assessments)

    assert result["tissue"]["skin"].assessed_cells == 2
    assert result["region"]["palm"].abnormality_mean == .3
    assert result["hand"]["hand"].state_counts == {"healthy": 1, "abnormal": 1}


def test_trend_comparison_reports_deltas():
    t0 = datetime(2026, 1, 1)
    t1 = datetime(2026, 2, 1)
    previous = CellAssessment("c1", t0, health_score=.9, abnormality_score=.1, biological_age=30)
    current = CellAssessment("c1", t1, health_score=.7, abnormality_score=.3, biological_age=32)

    trend = compare_cell_assessments(previous, current)

    assert trend.health_score_delta == -.2
    assert trend.abnormality_delta == .2
    assert trend.biological_age_delta == 2.0
