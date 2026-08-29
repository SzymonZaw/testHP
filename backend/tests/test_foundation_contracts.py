from backend.spatial_contract import canonical_spatial_id, is_descendant
from backend.microscopy_contract import MicroscopyImage, SegmentationResult
from backend.cell_identity_contract import CellIdentity, CellTypeAssessment


def test_spatial_aliases_are_canonical():
    assert canonical_spatial_id("Palm") == "hand/palm"
    assert canonical_spatial_id("Śródręcze") == "hand/palm"
    assert is_descendant("hand/palm/thenar", "hand/palm")


def test_microscopy_and_segmentation_contracts_validate():
    image = MicroscopyImage("img1", "s1", "h1", "tissue1", "T0", "hand/palm", "wsi", 100, 200, 0.5)
    image.validate()
    SegmentationResult("seg1", "img1", "test-model", "1", 4, 4, 0.9).validate()


def test_cell_identity_and_type_validate():
    CellIdentity("c1", "s1", "h1", "tissue1", "T0", "seg1", "hand/palm", (1, 2, 3)).validate()
    CellTypeAssessment("c1", "keratinocyte", 0.94, {"area_um2": 100}).validate()
