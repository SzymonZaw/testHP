import unittest

from organs import OrganModel, OrganSystemModel
from organs.propagation import OrganSignalPropagator


class PropagationTests(unittest.TestCase):
    def _system(self):
        heart = OrganModel("heart")
        brain = OrganModel("brain")
        kidney = OrganModel("kidney")
        brain.set_dependency("heart", 0.8)
        kidney.set_dependency("brain", 0.5)
        system = OrganSystemModel()
        for organ in (heart, brain, kidney):
            system.add_organ(organ)
        return system

    def test_signal_propagates_with_decay(self):
        result = OrganSignalPropagator(self._system(), decay=0.5).propagate({"brain": 1.0}, max_depth=2)
        by_path = {signal.path: signal.score for signal in result}
        self.assertEqual(by_path[("brain",)], 1.0)
        self.assertAlmostEqual(by_path[("brain", "heart")], 0.4)

    def test_depth_limits_propagation(self):
        result = OrganSignalPropagator(self._system()).propagate({"brain": 1.0}, max_depth=0)
        self.assertEqual(tuple(signal.path for signal in result), (("brain",),))

    def test_unknown_source_is_rejected(self):
        with self.assertRaises(KeyError):
            OrganSignalPropagator(self._system()).propagate({"lung": 1.0})


if __name__ == "__main__":
    unittest.main()
