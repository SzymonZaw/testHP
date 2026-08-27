import pytest

from backend.anatomy_foundation import (
    AnatomicalStructure,
    CellObject,
    Geometry,
    HandCoordinateSystem,
    HistologyRegion,
    SpatialReference,
    TissueRegion,
)
from backend.multiscale_registry import MultiscaleRegistry


FRAME = SpatialReference("hand-frame", "registered", transform={"type": "identity"})


def _registry() -> MultiscaleRegistry:
    registry = MultiscaleRegistry()
    registry.add_coordinate_system(HandCoordinateSystem("hand-frame", "s1", "h1", "t1"))
    registry.add_anatomy(
        AnatomicalStructure("a1", "s1", "h1", "t1", "skin", Geometry("g1", "surface", "hand-frame"), ("src",), 0.9, FRAME)
    )
    registry.add_tissue(
        TissueRegion("t1", "a1", "s1", "h1", "t1", "epidermis", Geometry("g2", "segmentation", "hand-frame"), ("src",), FRAME)
    )
    return registry


def test_registry_rejects_context_mismatch_at_each_child_layer():
    registry = _registry()
    with pytest.raises(ValueError, match="subject/hand/timepoint"):
        registry.add_histology(
            HistologyRegion("h1", "t1", "s1", "h1", "T1", "H&E", "slide", Geometry("g3", "surface", "hand-frame"), FRAME)
        )

    with pytest.raises(ValueError, match="subject/hand/timepoint"):
        registry.add_cell(
            CellObject("c1", "t1", "s1", "h1", "T1", {"x": 0, "y": 0, "z": 0}, None, {}, {}, {}, (), ("src",), FRAME)
        )


def test_snapshot_validates_existing_chain_before_export():
    registry = _registry()
    registry.tissues["t1"] = TissueRegion(
        "t1", "a1", "other-subject", "h1", "t1", "epidermis",
        Geometry("g2", "segmentation", "hand-frame"), ("src",), FRAME,
    )
    with pytest.raises(ValueError, match="mismatched subject/hand/timepoint"):
        registry.snapshot()
