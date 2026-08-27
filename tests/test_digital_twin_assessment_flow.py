from datetime import datetime

import pytest

from digital_twin.assessment_trends import AssessmentTrend
from digital_twin.cell_assessment import CellAssessment
from digital_twin.individual_cell import IndividualCellState
from digital_twin.spatial import CellLocation, HandRegion, HandSpatialModel, SpatialPoint, TissueRegion
from digital_twin.twin import DigitalTwin


def make_twin() -> DigitalTwin:
    model = HandSpatialModel()
    region = HandRegion(region_id="palm", name="Palm", side="left")
    tissue = TissueRegion(tissue_id="skin", tissue_type="skin", region_id="palm")
    tissue.add_cell(CellLocation("c1", SpatialPoint(1, 2, 3), tissue_id="skin"))
    region.add_tissue(tissue)
    model.add_region(region)
    return DigitalTwin(subject_id="demo", spatial_model=model)


def test_assess_cell_connects_state_assessment_and_trend():
    twin = make_twin()
    t0 = datetime(2026, 1, 1)
    t1 = datetime(2026, 2, 1)

    first = twin.assess_cell(
        IndividualCellState("c1", t0, abnormality=.2),
        CellAssessment("c1", t0, health_state="healthy", health_score=.9, abnormality_score=.2),
    )
    second = twin.assess_cell(
        IndividualCellState("c1", t1, abnormality=.7),
        CellAssessment("c1", t1, health_state="abnormal", health_score=.6, abnormality_score=.7),
    )

    assert first is None
    assert isinstance(second, AssessmentTrend)
    assert second.abnormality_delta == .5
    assert len(twin.cell_state_history("c1")) == 2
    assert twin.get_cell_assessment("c1").health_state == "abnormal"


def test_assess_cell_rejects_mismatched_ids():
    twin = make_twin()
    t = datetime(2026, 1, 1)
    with pytest.raises(ValueError):
        twin.assess_cell(
            IndividualCellState("c1", t),
            CellAssessment("c2", t),
        )


def test_assess_cell_rejects_untracked_cell():
    twin = make_twin()
    t = datetime(2026, 1, 1)
    with pytest.raises(KeyError):
        twin.assess_cell(
            IndividualCellState("unknown", t),
            CellAssessment("unknown", t),
        )
