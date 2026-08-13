import unittest
from datetime import datetime, timezone

from integration.observation_to_twin import Observation, ObservationToTwinPipeline
from organism.digital_twin import DigitalBiologicalTwin


class ObservationToTwinPipelineTests(unittest.TestCase):
    def test_ingest_filters_low_quality_and_preserves_provenance(self):
        twin = DigitalBiologicalTwin()
        pipeline = ObservationToTwinPipeline(twin, minimum_quality=0.5)
        snapshot = pipeline.ingest(
            "t1",
            [
                Observation("bone_density", 1.2, 0.9, "mri"),
                Observation("skin_marker", 0.4, 0.2, "microscopy"),
            ],
            datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(snapshot.state["bone_density"], 1.2)
        self.assertNotIn("skin_marker", snapshot.state)
        self.assertEqual(snapshot.provenance, ("mri",))
        self.assertEqual(twin.latest().timepoint_id, "t1")

    def test_invalid_quality_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            ObservationToTwinPipeline(DigitalBiologicalTwin(), minimum_quality=1.5)


if __name__ == "__main__":
    unittest.main()
