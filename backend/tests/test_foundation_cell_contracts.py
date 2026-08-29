from backend.foundation_contract import DigitalTwin, Evidence, SpatialLevel, SpatialRef
from backend.hand_tissue_contract import CoordinateFrame, HandStructure, Transform, TissueRegion
from backend.microscopy_cell_contract import CellIdentity, CellInstance, CellTypeAssessment, MicroscopyImage
from backend.cell_analysis_contract import SegmentationResult


def test_digital_twin_spatial_tree_validates():
    refs = (
        SpatialRef("hand-1", SpatialLevel.HAND),
        SpatialRef("hand-1/skin", SpatialLevel.STRUCTURE, "hand-1"),
        SpatialRef("hand-1/skin/palm", SpatialLevel.REGION, "hand-1/skin"),
    )
    twin = DigitalTwin("twin-1", "subject-1", ("hand-1",), refs, (Evidence("e1", "image", "img-1"),))
    twin.validate()


def test_transform_is_4x4():
    Transform("tr-1", "frame-a", "frame-b", tuple(float(i) for i in range(16))).validate()


def test_microscopy_and_cell_contracts_validate():
    MicroscopyImage("img-1", "tissue-1", "hand-1/tissue", "svs", 100, 100, .25, "src", "prov", "t0").validate()
    CellInstance("cell-1", "hand-1/tissue/cell-1", "img-1", "seg-1", (10, 20), confidence=.95).validate()
    CellTypeAssessment("cell-1", "keratinocyte", confidence=.94).validate()
    SegmentationResult("seg-1", "img-1", "model", "1", ("cell-1",), confidence=.9).validate()


def test_cell_identity_contains_required_scope():
    identity = CellIdentity("cell-1", "subject-1", "hand-1", "tissue-1", "t0", "seg-1", "hand-1/tissue/cell-1")
    assert identity.subject_id == "subject-1"
