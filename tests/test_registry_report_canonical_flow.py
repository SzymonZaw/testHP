from backend.anatomy_foundation import AnatomicalStructure, CellObject, Geometry, SpatialReference, TissueRegion
from backend.biological_state import BiologicalAgeEstimate, BiologicalStateAssessment, InterpretationEvidence, Uncertainty
from backend.multiscale_registry import MultiscaleRegistry
from backend.registry_report import build_registry_report


def make_registry():
    r = MultiscaleRegistry()
    sr = SpatialReference("f1")
    r.add_anatomy(AnatomicalStructure("a1", "s1", "h1", "T1", "skin", Geometry("g1", "volume", "f1"), ("d1",), sr))
    r.add_tissue(TissueRegion("t1", "a1", "s1", "h1", "T1", "epidermis", Geometry("g2", "segmentation", "f1"), ("d1",), sr))
    r.add_cell(CellObject("c1", "t1", "s1", "h1", "T1", {"x": 1, "y": 2, "z": 3}, "keratinocyte", {"area": 10}, {"diameter": 4}, {"area": 3}, (), ("d1",), sr))
    evidence = (InterpretationEvidence("e1", ("d1",), "morphology", {"area": 10}, 0.9, None),)
    r.add_biological_state_assessment(BiologicalStateAssessment("bs1", "s1", "h1", "T1", "c1", "normal", 0.9, evidence, Uncertainty("test", 0.1), None, "2026-08-27", "m", "1"))
    r.add_biological_age_estimate(BiologicalAgeEstimate("age1", "s1", "h1", "T1", "c1", 42.0, Uncertainty("test", None, (40, 44)), evidence, None, "2026-08-27", "age", "1"))
    return r


def test_report_uses_canonical_state_as_single_source():
    report = build_registry_report(make_registry(), subject_id="s1", hand_id="h1", timepoint_id="T1")
    assert len(report["cells"]) == 1
    assert report["cells"][0]["cell_id"] == "c1"
    assert report["assessments"][0]["state"] == "normal"
    assert report["biological_age"][0]["biological_age_years"] == 42.0
