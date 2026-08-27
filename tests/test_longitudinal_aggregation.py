from backend.anatomy_foundation import CellObject, Geometry, TissueRegion
from backend.biological_state import BiologicalAgeEstimate, BiologicalStateAssessment, InterpretationEvidence
from backend.data_foundation import Provenance, SpatialReference, Uncertainty
from backend.longitudinal_aggregation import aggregate_hand, aggregate_tissue


def _cell(cell_id: str, tissue_id: str = "t1") -> CellObject:
    return CellObject(cell_id, tissue_id, "s1", "h1", "T0", {"x": 1}, "keratinocyte", {}, {}, {}, (), ("src",), SpatialReference("f"))


def _evidence() -> InterpretationEvidence:
    return InterpretationEvidence("e1", ("src",), "morphology", {"x": 1}, 0.9, Provenance(("src",), "test"))


def _state(cell_id: str, state: str) -> BiologicalStateAssessment:
    return BiologicalStateAssessment("a-" + cell_id, "s1", "h1", "T0", cell_id, state, 0.9, (_evidence(),), Uncertainty(score=0.1), Provenance(("src",), "test"), "2026-08-27T00:00:00+00:00")


def _age(cell_id: str, years: float) -> BiologicalAgeEstimate:
    return BiologicalAgeEstimate("age-" + cell_id, "s1", "h1", "T0", cell_id, years, Uncertainty(interval=(years - 1, years + 1)), (_evidence(),), Provenance(("src",), "test"), "2026-08-27T00:00:00+00:00")


def _tissue(tissue_id: str = "t1") -> TissueRegion:
    return TissueRegion(tissue_id, "a1", "s1", "h1", "T0", "epidermis", Geometry("g-" + tissue_id, "segmentation", "f"), ("src",), SpatialReference("f"))


def test_aggregate_tissue_preserves_coverage_and_age():
    result = aggregate_tissue(_tissue(), [_cell("c1"), _cell("c2")], [_state("c1", "normal")], [_age("c1", 42)])
    assert result.cell_count == 2
    assert result.assessed_cell_count == 1
    assert result.state_counts == {"normal": 1}
    assert result.state_coverage == 0.5
    assert result.mean_biological_age_years == 42
    assert result.biological_age_interval == (41, 43)


def test_aggregate_hand_only_includes_matching_context():
    result = aggregate_hand("s1", "h1", "T0", [_tissue(), _tissue("t2")], [_cell("c1")], [_state("c1", "normal")], [_age("c1", 42)])
    assert result.tissue_count == 2
    assert result.tissues_with_cell_assessments == 1
    assert result.coverage == 0.5
