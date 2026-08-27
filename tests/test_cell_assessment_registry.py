from backend.anatomy_foundation import AnatomicalStructure, CellObject, Geometry, SpatialReference, TissueRegion
from backend.multiscale_registry import MultiscaleRegistry


def _cell():
    frame = "hand-frame"
    sr = SpatialReference(frame)
    anatomy = AnatomicalStructure("a1", "s1", "h1", "t1", "skin", Geometry("g1", "volume", frame), ("src",), spatial_reference=sr)
    tissue = TissueRegion("t1", "a1", "s1", "h1", "t1", "epidermis", Geometry("g2", "segmentation", frame), ("src",), sr)
    cell = CellObject("c1", "t1", "s1", "h1", "t1", {"x": 1.0, "y": 2.0, "z": 3.0}, "keratinocyte", {"area": 12.5}, {"diameter": 4.0}, {"area": 3.0}, (), ("src",), sr)
    registry = MultiscaleRegistry()
    registry.add_anatomy(anatomy)
    registry.add_tissue(tissue)
    registry.add_cell(cell)
    return registry


def test_assess_and_register_cell_creates_state_and_age():
    registry = _cell()
    bundle = registry.assess_and_register_cell(
        "c1",
        observations={"anomaly_score": 0.1},
        age_observations={"estimated_age_years": 42.0, "age_interval": (39.0, 45.0), "confidence": 0.8},
        source_data_ids=("src",),
        assessed_at="2026-08-27T00:00:00+00:00",
    )
    assert bundle.state_assessment.cell_id == "c1"
    assert bundle.state_assessment.state == "normal"
    assert bundle.age_estimate.target_object_id == "c1"
    assert bundle.age_estimate.estimated_age_years == 42.0
    assert registry.chain_for_cell("c1").age_estimate == bundle.age_estimate


def test_assess_and_register_requires_existing_cell():
    registry = MultiscaleRegistry()
    try:
        registry.assess_and_register_cell("missing", observations={"anomaly_score": 0.1}, age_observations={"estimated_age_years": 42}, source_data_ids=("src",), assessed_at="2026-08-27T00:00:00+00:00")
    except KeyError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("missing cell should be rejected")
