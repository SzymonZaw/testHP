import unittest
from datetime import datetime

from core import Biomarker, Measurement, Observation, Uncertainty
from core.quality import MeasurementQualityEngine


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.engine = MeasurementQualityEngine()
        self.measurement = Measurement(
            id="m1",
            subject_id="p1",
            timepoint_id="t1",
            modality="mri",
            biomarker=Biomarker("bone_density", "bone", "density"),
            value=1.0,
            measured_at=datetime.now(),
        )

    def test_missing_uncertainty_reduces_score(self):
        result = self.engine.assess_measurement(self.measurement)
        self.assertEqual(result.score, 0.8)
        self.assertTrue(result.usable)
        self.assertIn("missing_uncertainty", result.flags)

    def test_low_quality_is_not_usable(self):
        measurement = Measurement(
            **{**self.measurement.__dict__, "uncertainty": Uncertainty(quality_score=0.2)}
        )
        result = self.engine.assess_measurement(measurement)
        self.assertEqual(result.score, 0.6)
        self.assertTrue(result.usable)

    def test_observation_quality_flags_are_preserved(self):
        observation = Observation(
            id="o1", subject_id="p1", timepoint_id="t1", name="cell_shape",
            value=0.2, observed_at=datetime.now(),
            uncertainty=Uncertainty(quality_score=0.4, quality_flags=("blurred",)),
        )
        result = self.engine.assess_observation(observation)
        self.assertIn("low_quality_score", result.flags)
        self.assertIn("blurred", result.flags)


if __name__ == "__main__":
    unittest.main()
