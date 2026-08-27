import unittest
from datetime import datetime, timezone

from core import AnatomicalLocation, Observation
from digital_twin.observation_mapper import SpatialObservationMapper
from digital_twin.spatial import CellLocation, HandRegion, HandSpatialModel, SpatialPoint, TissueRegion


class TestSpatialObservationMapping(unittest.TestCase):
    def setUp(self) -> None:
        self.model = HandSpatialModel()
        self.model.add_region(HandRegion(region_id="palm", name="Palm", side="left"))
        self.model.add_tissue(
            "palm",
            TissueRegion(tissue_id="palm_skin", tissue_type="skin", region_id="palm"),
        )
        self.model.add_cell(
            "palm",
            "palm_skin",
            CellLocation(
                cell_id="cell-001",
                position=SpatialPoint(1.0, 2.0, 3.0),
                tissue_id="palm_skin",
                cell_type="keratinocyte",
                confidence=0.97,
            ),
        )

    def test_cell_observation_resolves_to_spatial_hierarchy(self):
        observation = Observation(
            id="O-CELL-001",
            subject_id="P001",
            timepoint_id="T0",
            name="cell_area",
            value=123.4,
            observed_at=datetime.now(timezone.utc),
            anatomical_location=AnatomicalLocation(
                id="cell-001", name="Cell 001", level="cell"
            ),
            biological_level="cellular",
            modality="microscopy",
        )

        resolved = SpatialObservationMapper(self.model).resolve(observation)

        self.assertEqual(resolved["region_id"], "palm")
        self.assertEqual(resolved["tissue_id"], "palm_skin")
        self.assertEqual(resolved["cell_id"], "cell-001")
        self.assertEqual(resolved["timepoint_id"], "T0")

    def test_metadata_can_supply_region_and_tissue(self):
        observation = Observation(
            id="O-TISSUE-001",
            subject_id="P001",
            timepoint_id="T0",
            name="thickness",
            value=1.42,
            observed_at=datetime.now(timezone.utc),
            anatomical_location=AnatomicalLocation(
                id="skin", name="Skin", level="tissue"
            ),
            biological_level="tissue",
            metadata={"region_id": "palm"},
        )

        resolved = SpatialObservationMapper(self.model).resolve(observation)

        self.assertEqual(resolved["region_id"], "palm")
        self.assertEqual(resolved["tissue_id"], "skin")

    def test_unknown_cell_is_rejected(self):
        observation = Observation(
            id="O-CELL-404",
            subject_id="P001",
            timepoint_id="T0",
            name="cell_area",
            value=1.0,
            observed_at=datetime.now(timezone.utc),
            anatomical_location=AnatomicalLocation(
                id="missing", name="Missing", level="cell"
            ),
            biological_level="cellular",
        )

        with self.assertRaises(KeyError):
            SpatialObservationMapper(self.model).resolve(observation)


if __name__ == "__main__":
    unittest.main()
