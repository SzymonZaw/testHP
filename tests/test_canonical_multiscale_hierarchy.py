from backend.anatomy_foundation import (
    AnatomicalStructure,
    CellObject,
    Geometry,
    MultiscaleHierarchy,
    TissueRegion,
)
from backend.data_foundation import SpatialReference


def test_canonical_hierarchy_validates_hand_structure_tissue_cell_chain():
    frame = SpatialReference("hand-frame")
    structure = AnatomicalStructure(
        "structure-1", "subject-1", "hand-1", "t1", "muscle",
        Geometry("g-1", "volume", "hand-frame"), ("scan-1",),
        spatial_reference=frame,
    )
    tissue = TissueRegion(
        "tissue-1", "structure-1", "subject-1", "hand-1", "t1", "muscle",
        Geometry("g-2", "volume", "hand-frame"), ("scan-1",), frame,
    )
    cell = CellObject(
        "cell-1", "tissue-1", "subject-1", "hand-1", "t1",
        {"x": 1.0, "y": 2.0, "z": 3.0}, "myocyte", {}, {"volume": 1.0},
        {}, (), ("cell-scan-1",), frame,
    )
    hierarchy = MultiscaleHierarchy("hand-1", (structure,), (tissue,), (), (cell,))

    hierarchy.validate()
    assert hierarchy.tissues_for_structure("structure-1") == (tissue,)
    assert hierarchy.cells_for_tissue("tissue-1") == (cell,)


def test_canonical_hierarchy_rejects_cross_hand_cell():
    frame = SpatialReference("hand-frame")
    structure = AnatomicalStructure(
        "structure-1", "subject-1", "hand-1", "t1", "muscle",
        Geometry("g-1", "volume", "hand-frame"), ("scan-1",),
        spatial_reference=frame,
    )
    tissue = TissueRegion(
        "tissue-1", "structure-1", "subject-1", "hand-1", "t1", "muscle",
        Geometry("g-2", "volume", "hand-frame"), ("scan-1",), frame,
    )
    cell = CellObject(
        "cell-1", "tissue-1", "subject-1", "hand-2", "t1",
        {"x": 1.0, "y": 2.0, "z": 3.0}, "myocyte", {}, {"volume": 1.0},
        {}, (), ("cell-scan-1",), frame,
    )
    hierarchy = MultiscaleHierarchy("hand-1", (structure,), (tissue,), (), (cell,))

    try:
        hierarchy.validate()
    except ValueError as exc:
        assert "different hand" in str(exc)
    else:
        raise AssertionError("expected cross-hand cell to be rejected")
