import unittest

from digital_twin.spatial import (
    CellLocation,
    HandRegion,
    HandSpatialModel,
    SpatialPoint,
    StructureRegion,
    TissueRegion,
)
from digital_twin.twin import DigitalTwin


class TestSpatialModel(unittest.TestCase):
    def test_builds_hand_to_cell_hierarchy(self):
        model = HandSpatialModel()
        region = HandRegion(region_id="palm", name="Palm", side="right")
        tissue = TissueRegion(tissue_id="skin-001", tissue_type="skin")
        structure = StructureRegion(
            structure_id="structure-001",
            name="epidermis",
            structure_type="layer",
        )
        cell = CellLocation(
            cell_id="cell-001",
            position=SpatialPoint(10.0, 20.0, 2.0),
            tissue_id="skin-001",
            structure_id="structure-001",
            cell_type="keratinocyte",
            confidence=0.95,
        )

        model.add_region(region)
        model.add_tissue("palm", tissue)
        model.add_structure("palm", "skin-001", structure)
        model.add_cell("palm", "skin-001", cell)

        located = model.locate_cell("cell-001")
        self.assertIs(located, cell)
        self.assertEqual(model.regions["palm"].tissues["skin-001"].structures["structure-001"].name, "epidermis")

    def test_unknown_region_or_tissue_is_rejected(self):
        model = HandSpatialModel()
        with self.assertRaises(KeyError):
            model.add_tissue("missing", TissueRegion(tissue_id="t1"))

        model.add_region(HandRegion(region_id="palm", name="Palm"))
        with self.assertRaises(KeyError):
            model.add_cell(
                "palm",
                "missing",
                CellLocation("cell", SpatialPoint(0, 0, 0)),
            )

    def test_spatial_model_is_part_of_digital_twin(self):
        twin = DigitalTwin(subject_id="P001")
        twin.spatial_model.add_region(
            HandRegion(region_id="palm", name="Palm")
        )
        twin.spatial_model.add_tissue(
            "palm", TissueRegion(tissue_id="skin-001")
        )
        twin.spatial_model.add_cell(
            "palm",
            "skin-001",
            CellLocation("cell-001", SpatialPoint(1, 2, 3)),
        )

        snapshot = twin.snapshot()
        self.assertEqual(snapshot["spatial_model"]["regions"]["palm"]["name"], "Palm")
        self.assertEqual(twin.summary()["spatial_cells"], 1)


if __name__ == "__main__":
    unittest.main()
