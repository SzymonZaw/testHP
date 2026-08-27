"""End-to-end synthetic Digital Twin Hand v0.1 test.

The scenario is deliberately synthetic: it validates data flow and
aggregation, not biological or clinical validity.
"""

from datetime import datetime, timedelta

from digital_twin.assessment_trends import compare_cell_assessments
from digital_twin.cell_assessment import CellAssessment
from digital_twin.intervention_map import build_intervention_map
from digital_twin.spatial import CellLocation, HandRegion, HandSpatialModel, SpatialPoint, TissueRegion
from digital_twin.twin import DigitalTwin
from digital_twin.individual_cell import IndividualCellState


def _build_twin(cell_count=1000):
    spatial = HandSpatialModel()
    regions = ["palm", "thumb", "index", "middle", "ring"]
    for region_id in regions:
        region = HandRegion(region_id=region_id, name=region_id.title(), side="left")
        tissue = TissueRegion(tissue_id=f"{region_id}-skin", tissue_type="skin", region_id=region_id)
        region.add_tissue(tissue)
        spatial.add_region(region)

    ids = []
    for i in range(cell_count):
        region_id = regions[i % len(regions)]
        tissue = spatial.regions[region_id].tissues[f"{region_id}-skin"]
        cell_id = f"cell-{i:04d}"
        tissue.add_cell(CellLocation(cell_id, SpatialPoint(float(i % 20), float(i // 20), 0), tissue_id=tissue.tissue_id))
        ids.append(cell_id)

    return DigitalTwin("synthetic-hand-v01", spatial_model=spatial), ids


def _state(cell_id, observed_at, age, abnormality):
    return IndividualCellState(
        cell_id=cell_id,
        observed_at=observed_at,
        biological_age=age,
        abnormality=abnormality,
        confidence=0.9,
    )


def _assessment(cell_id, observed_at, health_state, health_score, age, abnormality):
    return CellAssessment(
        cell_id=cell_id,
        observed_at=observed_at,
        health_state=health_state,
        health_score=health_score,
        biological_age=age,
        age_confidence=0.9,
        abnormality_score=abnormality,
        uncertainty=0.1,
    )


def test_synthetic_hand_end_to_end():
    twin, cell_ids = _build_twin()
    t0 = datetime(2026, 1, 1)
    t1 = t0 + timedelta(days=30)
    t2 = t0 + timedelta(days=60)
    previous_assessments = {}

    for i, cell_id in enumerate(cell_ids):
        group = i % 20
        if group < 14:  # stable
            values = [(30, .10), (30, .10), (30, .11)]
        elif group < 17:  # aging
            values = [(35, .15), (36, .18), (38, .21)]
        elif group == 17:  # worsening
            values = [(40, .45), (42, .60), (44, .75)]
        elif group == 18:  # improving
            values = [(45, .50), (44, .35), (43, .20)]
        else:  # uncertain
            values = [(50, .20), (51, .20), (52, .20)]

        for observed_at, (age, abnormality) in zip((t0, t1, t2), values):
            twin.add_cell_state(_state(cell_id, observed_at, age, abnormality))

        assessments = [
            _assessment(cell_id, t0, "healthy", .90, *values[0]),
            _assessment(cell_id, t1, "healthy", .85, *values[1]),
            _assessment(
                cell_id,
                t2,
                "abnormal" if group == 17 else "healthy",
                .70 if group == 17 else .85,
                *values[2],
            ),
        ]
        previous_assessments[cell_id] = assessments[0]
        twin.add_cell_assessment(assessments[-1])

    hierarchy = twin.hierarchical_assessment()
    trends = {
        cell_id: compare_cell_assessments(previous_assessments[cell_id], assessment)
        for cell_id, assessment in twin.cell_assessments.items()
    }
    priorities = build_intervention_map(twin.cell_assessments, trends)

    assert len(cell_ids) == 1000
    assert len(twin.cell_timeline.states) == 1000
    assert set(hierarchy) == {"tissue", "region", "hand"}
    assert hierarchy["hand"]["hand"]["assessed_cells"] == 1000
    assert sum(item.priority == "investigate" for item in priorities.values()) == 50
    assert all(item.priority == "no_action" for cell_id, item in priorities.items() if int(cell_id.split("-")[1]) % 20 < 14)
