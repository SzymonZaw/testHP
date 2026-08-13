import unittest

from intervention.surveillance import InterventionObservation, InterventionSurveillance


class InterventionSurveillanceTests(unittest.TestCase):
    def test_efficacy_and_safety_are_tracked_separately(self):
        surveillance = InterventionSurveillance("i1")
        surveillance.add(InterventionObservation("t0", 0.0, "efficacy", 1.0))
        surveillance.add(InterventionObservation("t1", 1.0, "efficacy", 2.0))
        surveillance.add(InterventionObservation("t0", 0.0, "safety", 0.0))
        surveillance.add(InterventionObservation("t1", 1.0, "safety", 0.4))
        summary = surveillance.summary()
        self.assertEqual(summary.efficacy_change, 1.0)
        self.assertEqual(summary.safety_change, 0.4)
        self.assertTrue(summary.safety_signal)
        self.assertFalse(summary.insufficient_evidence)

    def test_low_quality_observation_is_excluded(self):
        surveillance = InterventionSurveillance("i1")
        surveillance.add(InterventionObservation("t0", 0.0, "efficacy", 1.0))
        surveillance.add(InterventionObservation("t1", 1.0, "efficacy", 5.0, quality_score=0.2))
        surveillance.add(InterventionObservation("t0", 0.0, "safety", 0.0))
        surveillance.add(InterventionObservation("t1", 1.0, "safety", 0.0))
        summary = surveillance.summary()
        self.assertIsNone(summary.efficacy_change)
        self.assertTrue(summary.insufficient_evidence)

    def test_invalid_domain_is_rejected(self):
        surveillance = InterventionSurveillance("i1")
        with self.assertRaises(ValueError):
            surveillance.add(InterventionObservation("t0", 0.0, "diagnosis", 1.0))


if __name__ == "__main__":
    unittest.main()
