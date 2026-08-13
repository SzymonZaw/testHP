import unittest

from core.biological_state import BiologicalState
from core.longitudinal import compare_states, trajectory


class LongitudinalTests(unittest.TestCase):
    def test_compare_states(self):
        baseline = BiologicalState("person-001", "T0")
        current = BiologicalState("person-001", "T1")
        baseline.set_dimension("cell_density", 100.0)
        current.set_dimension("cell_density", 90.0)

        comparison = compare_states(baseline, current, elapsed_days=365)

        change = comparison.changes[0]
        self.assertEqual(change.name, "cell_density")
        self.assertEqual(change.delta, -10.0)
        self.assertAlmostEqual(change.rate_per_day, -10.0 / 365)
        self.assertAlmostEqual(change.relative_change, -0.1)

    def test_subject_mismatch_is_rejected(self):
        a = BiologicalState("person-001", "T0")
        b = BiologicalState("person-002", "T1")
        with self.assertRaises(ValueError):
            compare_states(a, b, 30)

    def test_non_positive_interval_is_rejected(self):
        a = BiologicalState("person-001", "T0")
        b = BiologicalState("person-001", "T1")
        with self.assertRaises(ValueError):
            compare_states(a, b, 0)

    def test_trajectory(self):
        states = []
        for timepoint, value in [("T0", 100), ("T1", 95), ("T2", 91)]:
            state = BiologicalState("person-001", timepoint)
            state.set_dimension("cell_density", value)
            states.append(state)

        result = trajectory(states, [0, 365, 730])
        self.assertEqual(result["cell_density"], [100.0, 95.0, 91.0])

    def test_trajectory_rejects_mixed_subjects(self):
        a = BiologicalState("person-001", "T0")
        b = BiologicalState("person-002", "T1")
        with self.assertRaises(ValueError):
            trajectory([a, b], [0, 365])


if __name__ == "__main__":
    unittest.main()
