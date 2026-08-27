import pytest

from backend.anatomy_foundation import (
    AnatomicalStructure, CellObject, Geometry, HandCoordinateSystem, Registration,
    TissueRegion, SpatialReference, Quality, Uncertainty, Provenance,
    HistologyRegion,
)
from backend.cell_assessment import build_cell_state_assessment
from backend.multiscale_registry import ModalityAcquisition, MultiscaleRegistry
from backend.anatomy_foundation import Evidence


def make_registry():
    registry = MultiscaleRegistry()
    registry.add_coordinate_system(HandCoordinateSystem("hand-frame", "s1", "h1", "t1"))
    return registry


def test_registration_requires_registered_target_frame():
    registry = MultiscaleRegistry()
    registration = Registration("r1", "s1", "h1", "t1", "mri-frame", "hand-frame", "mri", {"matrix": [[1,0,0],[0,1,0],[0,0,1]]})
    with pytest.raises(ValueError):
        registry.add_registration(registration)


def test_multiscale_parent_links_are_enforced():
    registry = make_registry()
    geometry = Geometry("g1", "surface", "hand-frame")
    anatomy = AnatomicalStructure("a1", "s1", "h1", "t1", "muscle", geometry, ("img1",), 0.9, SpatialReference("hand-frame", "registered", transform={"type": "identity"}))
    registry.add_anatomy(anatomy)
    tissue = TissueRegion("t1", "a1", "s1", "h1", "t1", "muscle_tissue", geometry, ("img1",), SpatialReference("hand-frame", "registered", transform={"type": "identity"}), 0.9)
    registry.add_tissue(tissue)
    assert "t1" in registry.tissues


def test_histology_and_cells_require_existing_tissue():
    registry = make_registry()
    geometry = Geometry("g1", "surface", "hand-frame")
    histology = HistologyRegion("hist1", "missing", "s1", "h1", "t1", "H&E", "slide1", geometry, SpatialReference("hand-frame"))
    with pytest.raises(ValueError):
        registry.add_histology(histology)

    cell = CellObject("c1", "missing", "s1", "h1", "t1", {"x": 0, "y": 0, "z": 0}, None, {}, {"diameter": 10}, {}, (), ("slide1",), SpatialReference("hand-frame"))
    with pytest.raises(ValueError):
        registry.add_cell(cell)


def test_snapshot_keeps_modality_and_multiscale_layers():
    registry = make_registry()
    registry.add_acquisition(ModalityAcquisition("acq1", "s1", "h1", "t1", "mri", ["raw-mri"], "mri-frame"))
    snapshot = registry.snapshot()
    assert snapshot["acquisitions"][0]["modality"] == "mri"
    assert snapshot["coordinate_systems"][0]["frame_id"] == "hand-frame"


def test_cell_state_assessment_must_attach_to_registered_cell():
    registry = make_registry()
    geometry = Geometry("g1", "surface", "hand-frame")
    anatomy = AnatomicalStructure("a1", "s1", "h1", "t1", "skin", geometry, ("img1",), 0.9, SpatialReference("hand-frame", "registered", transform={"type": "identity"}))
    registry.add_anatomy(anatomy)
    tissue = TissueRegion("t1", "a1", "s1", "h1", "t1", "epidermis", geometry, ("img1",), SpatialReference("hand-frame", "registered", transform={"type": "identity"}), 0.9)
    registry.add_tissue(tissue)
    cell = CellObject("c1", "t1", "s1", "h1", "t1", {"x": 0, "y": 0, "z": 0}, "keratinocyte", {}, {"diameter": 4}, {}, (), ("slide1",), SpatialReference("hand-frame"))
    registry.add_cell(cell)
    assessment = build_cell_state_assessment(
        cell,
        assessment_id="cell-state-1",
        state="senescent",
        confidence=0.82,
        evidence=(Evidence("ev1", ("slide1",), "morphology", {"area": 12.5}, 0.9),),
        provenance=Provenance(),
        assessed_at="2026-08-27T00:00:00+00:00",
    )
    registry.add_cell_state_assessment(assessment)
    assert registry.snapshot()["cell_state_assessments"][0]["cell_id"] == "c1"
