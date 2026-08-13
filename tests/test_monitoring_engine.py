import unittest

from monitoring.monitor import MonitoringEngine
from core.biological_state import BiologicalState


class MonitoringEngineTests(unittest.TestCase):
    def _state(self, value):
        state = BiologicalState(subject_id="demo-subject", timepoint_id="t1")
        state.set_dimension("marker", value)
        return state

    def test_cycle_is_recorded_and_retrievable(self):
        state = self._state(1.0)
        engine = MonitoringEngine()
        cycle = engine.run_cycle(state, {"marker": (0.0, 2.0)})
        self.assertIs(engine.latest(), cycle)
        self.assertEqual(len(engine.history), 1)
        self.assertIs(cycle.state, state)

    def test_history_preserves_multiple_cycles(self):
        engine = MonitoringEngine()
        first = self._state(0.5)
        second = BiologicalState(subject_id="demo-subject", timepoint_id="t2")
        second.set_dimension("marker", 1.5)
        engine.run_cycle(first, {"marker": (0.0, 2.0)})
        engine.run_cycle(second, {"marker": (0.0, 2.0)})
        self.assertEqual(len(engine.history), 2)
        self.assertIs(engine.latest().state, second)

    def test_empty_engine_has_no_latest_cycle(self):
        self.assertIsNone(MonitoringEngine().latest())


if __name__ == "__main__":
    unittest.main()
