import unittest

from organism import HealthStateAggregator, OrganismState
from organs.propagation import OrganSignal


class HealthStateTests(unittest.TestCase):
    def test_aggregate_organ_signals(self):
        state = OrganismState("person-001", "T1", anomaly_signals=("cell_density",))
        signals = (
            OrganSignal("heart", 0.4, "brain", ("brain", "heart")),
            OrganSignal("heart", 0.7, "brain", ("brain", "heart")),
            OrganSignal("kidney", 0.2, "brain", ("brain", "heart", "kidney")),
        )
        result = HealthStateAggregator().aggregate(state, signals)
        self.assertEqual(result.organ_signal_scores["heart"], 0.7)
        self.assertEqual(result.organ_signal_scores["kidney"], 0.2)
        self.assertEqual(result.systemic_score, 0.7)
        self.assertEqual(result.anomaly_count, 1)
        self.assertEqual(result.flags, ("cell_density",))

    def test_empty_state_is_neutral(self):
        result = HealthStateAggregator().aggregate(OrganismState("person-001", "T1"))
        self.assertEqual(result.systemic_score, 0.0)
        self.assertEqual(result.anomaly_count, 0)


if __name__ == "__main__":
    unittest.main()
