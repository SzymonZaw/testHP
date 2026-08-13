import unittest

from anomaly import Anomaly
from decision import InvestigationPlanner, RiskAssessor


class DecisionTests(unittest.TestCase):
    def _anomaly(self, feature, severity="high", reason="reference deviation"):
        return Anomaly(feature, 10.0, 4.0, 3.0, severity, reason)

    def test_risk_assessment(self):
        result = RiskAssessor().assess([
            self._anomaly("cell_density", "high"),
            self._anomaly("rna", "critical"),
        ])
        self.assertEqual(result.level, "high")
        self.assertEqual(result.score, 5.0)
        self.assertEqual(result.signals, ("cell_density", "rna"))

    def test_investigation_planner(self):
        anomalies = [self._anomaly("cell_density", "high")]
        plan = InvestigationPlanner().plan(anomalies, risk_level="high")
        self.assertEqual(plan.priority, "urgent")
        self.assertIn("cell_imaging", plan.recommended_modalities)
        self.assertIn("tissue_imaging", plan.recommended_modalities)

    def test_unknown_signal_is_preserved(self):
        plan = InvestigationPlanner().plan([self._anomaly("unknown_marker")])
        self.assertEqual(plan.unresolved_signals, ("unknown_marker",))


if __name__ == "__main__":
    unittest.main()
