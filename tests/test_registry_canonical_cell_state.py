import pytest

from backend.anatomy_foundation import CellObject, Geometry, SpatialReference, TissueRegion, AnatomicalStructure
from backend.biological_state import BiologicalAgeEstimate, BiologicalStateAssessment, InterpretationEvidence, Uncertainty
from backend.canonical_cell_state import CanonicalCellState
from backend.multiscale_registry import MultiscaleRegistry


def make_registry():
    r = MultiscaleRegistry()
    sr = SpatialReference("f1")
    r.add_anatomy(AnatomicalStructure("a1", "s1", "h1", "T1", "skin", Geometry("g1", "volume", "f1"), ("d1",), sr))
    r.add_tissue(TissueRegion("t1", "a1", "s1", "h1", "T1", "epidermis", Geometry("g2", "segmentation", "f1"), ("d1",), sr))
    r.add_cell(CellObject("c1", "t1", "s1", "h1", "T1", {"x": 1, "y": 2, "z": 3}, "keratinocyte", {"area": 10}, {"diameter": 4}, {"area": 3}, (), ("d1",), sr))
    return r


def evidence():
    return (InterpretationEvidence("e1", ("d1",), "morphology", {"area": 10}, 0.9, None),)


def test_registry_returns_one_canonical_cell_state():
    r = make_registry()
    r.add_biological_state_assessment(BiologicalStateAssessment("bs1", "s1", "h1", "T1", "c1", "normal", 0.9, evidence(), Uncertainty("test", 0.1), None, "2026-08-27", "m", "1"))
    r.add_biological_age_estimate(BiologicalAgeEstimate("age1", "s1", "h1", "T1", "c1", 42.0, Uncertainty("test", None, (40, 44)), evidence(), None, "2026-08-27", "age", "1"))
    state = r.canonical_cell_state("c1")
    assert isinstance(state, CanonicalCellState)
    assert state.state.state == "normal"
    assert state.state.biological_age_years == 42.0


def test_registry_rejects_two_state_representations():
    r = make_registry()
    r.cell_state_assessments["legacy"] = object()
    with pytest.raises((AttributeError, ValueError)):
        r.canonical_cell_state("c1")
