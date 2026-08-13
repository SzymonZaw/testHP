import unittest

from anomaly import AnomalyDetector, detect_anomalies
from anomaly.state_anomaly import detect_state_anomalies
from core.biological_state import BiologicalState


class AnomalyTests(unittest.TestCase):
    def test_reference_deviation(self):
        result = detect_anomalies(
            {"cell_density": 130.0},
            {"cell_density": (100.0, 10.0)},
            z_threshold=3.0,
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].severity, "high")
        self.assertAlmostEqual(result[0].z_score, 3.0)

    def test_normal_value_is_not_flagged(self):
        result = detect_anomalies(
            {"cell_density": 105.0},
            {"cell_density": (100.0, 10.0)},
        )
        self.assertEqual(result, [])

    def test_rate_anomaly(self):
        detector = AnomalyDetector(rate_thresholds={"repair": 0.1})
        result = detector.detect(
            {"repair": 0.5},
            {"repair": (0.5, 1.0)},
            rates={"repair": -0.2},
        )
        self.assertTrue(any(item.reason == "abnormal change rate" for item in result))

    def test_state_adapter(self):
        state = BiologicalState("person-001", "T1")
        state.set_dimension("fibrosis", 20.0)
        result = detect_state_anomalies(
            state,
            {"fibrosis": (10.0, 2.0)},
        )
        self.assertEqual(result[0].feature, "fibrosis")

    def test_invalid_reference_std_is_rejected(self):
        detector = AnomalyDetector()
        with self.assertRaises(ValueError):
            detector.detect({"x": 1.0}, {"x": (0.0, 0.0)})


if __name__ == "__main__":
    unittest.main()
