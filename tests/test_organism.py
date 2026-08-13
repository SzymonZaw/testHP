import unittest

from organism import OrganismModel, OrganismState
from organs import OrganModel


class OrganismTests(unittest.TestCase):
    def _state(self, timepoint, biomarker):
        heart = OrganModel("heart")
        heart.set_dimension("function", biomarker)
        return OrganismState(
            subject_id="person-001",
            timepoint_id=timepoint,
            organs={"heart": heart.snapshot()},
            biomarkers={"marker": biomarker},
            aging_scores={"systemic": 42.0},
        )

    def test_history_and_current_state(self):
        model = OrganismModel("person-001")
        model.add_state(self._state("T1", 1.0))
        model.add_state(self._state("T2", 2.0))
        self.assertEqual(model.current.timepoint_id, "T2")
        self.assertEqual(len(model.trajectory()), 2)
        self.assertEqual(model.biomarker_change("marker"), 1.0)

    def test_subject_mismatch_is_rejected(self):
        model = OrganismModel("person-001")
        with self.assertRaises(ValueError):
            model.add_state(OrganismState("person-002", "T1"))

    def test_duplicate_timepoint_is_rejected(self):
        model = OrganismModel("person-001")
        model.add_state(self._state("T1", 1.0))
        with self.assertRaises(ValueError):
            model.add_state(self._state("T1", 2.0))

    def test_anomaly_is_traceable(self):
        state = self._state("T1", 1.0).with_anomaly("cell_density")
        self.assertEqual(state.anomaly_signals, ("cell_density",))


if __name__ == "__main__":
    unittest.main()
