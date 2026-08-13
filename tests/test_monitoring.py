import unittest

from core.biological_state import BiologicalState
from monitoring import MonitoringEngine


class MonitoringTests(unittest.TestCase):
    def _state(self, value=130.0, timepoint="T1"):
        state = BiologicalState("person-001", timepoint)
        state.set_dimension("cell_density", value)
        return state

    def test_cycle_runs_end_to_end(self):
        engine = MonitoringEngine()
        cycle = engine.run_cycle(
            self._state(),
            {"cell_density": (100.0, 10.0)},
        )
        self.assertEqual(len(cycle.anomalies), 1)
        self.assertEqual(cycle.risk.level, "low")
        self.assertIn("cell_imaging", cycle.investigation.recommended_modalities)
        self.assertIs(engine.latest(), cycle)

    def test_history_retains_multiple_cycles(self):
        engine = MonitoringEngine()
        engine.run_cycle(self._state(130, "T1"), {"cell_density": (100, 10)})
        engine.run_cycle(self._state(100, "T2"), {"cell_density": (100, 10)})
        self.assertEqual(len(engine.history), 2)
        self.assertEqual(engine.latest().state.timepoint_id, "T2")

    def test_empty_cycle_has_no_risk_or_investigation(self):
        engine = MonitoringEngine()
        cycle = engine.run_cycle(
            self._state(100),
            {"cell_density": (100.0, 10.0)},
        )
        self.assertEqual(cycle.anomalies, ())
        self.assertEqual(cycle.risk.level, "none")
        self.assertEqual(cycle.investigation.priority, "none")


if __name__ == "__main__":
    unittest.main()
