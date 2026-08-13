"""Tests for the first end-to-end cell pipeline."""

import unittest

import numpy as np

from core.anatomy import AnatomicalLocation
from pipelines.cell_pipeline import run_cell_pipeline
from segmentation.cell_segmentation import segment_binary_cells


class CellPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.location = AnatomicalLocation(
            id="skin_sample",
            name="Skin sample",
            level="tissue",
        )

    def test_segmentation_creates_instance_labels(self) -> None:
        image = np.zeros((20, 20), dtype=np.float32)
        image[2:6, 2:6] = 10
        image[12:17, 12:17] = 10

        mask = segment_binary_cells(image, threshold=5, min_area=4)

        self.assertEqual(mask.max(), 2)
        self.assertEqual(len(np.unique(mask)) - 1, 2)

    def test_pipeline_builds_measurements_observations_and_state(self) -> None:
        image = np.zeros((30, 30), dtype=np.float32)
        image[2:7, 2:7] = 10
        image[18:25, 18:25] = 10

        result = run_cell_pipeline(
            image,
            subject_id="person-001",
            timepoint_id="T0",
            anatomical_location=self.location,
            threshold=5,
            min_area=4,
            quality=0.9,
        )

        self.assertEqual(result.analysis["cell_count"], 2)
        self.assertEqual(len(result.measurements), 6)
        self.assertEqual(len(result.observations), 6)
        self.assertIsNotNone(result.state)
        self.assertEqual(len(result.state.observations), 6)
        self.assertAlmostEqual(
            result.state.get_dimension("cell_count"),
            2.0,
        )
        self.assertEqual(
            result.measurements[0].uncertainty.confidence,
            0.9,
        )

    def test_pipeline_accepts_external_instance_mask(self) -> None:
        mask = np.zeros((15, 15), dtype=np.int32)
        mask[1:5, 1:5] = 1
        mask[8:13, 8:13] = 2

        result = run_cell_pipeline(
            mask,
            subject_id="person-002",
            timepoint_id="T0",
            anatomical_location=self.location,
            input_is_mask=True,
        )

        self.assertEqual(result.analysis["cell_count"], 2)
        self.assertEqual(result.mask.dtype, np.int32)


if __name__ == "__main__":
    unittest.main()
