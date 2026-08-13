import unittest

from organs import OrganModel, OrganSystemModel


class OrganTests(unittest.TestCase):
    def test_organ_snapshot(self):
        heart = OrganModel("heart")
        heart.set_dimension("ejection_fraction", 0.62)
        snapshot = heart.snapshot()
        self.assertEqual(snapshot.organ, "heart")
        self.assertEqual(snapshot.dimensions["ejection_fraction"], 0.62)

    def test_dependency_graph(self):
        heart = OrganModel("heart")
        brain = OrganModel("brain")
        brain.set_dependency("heart", 0.8)
        system = OrganSystemModel()
        system.add_organ(heart)
        system.add_organ(brain)
        self.assertEqual(system.dependency_graph()["brain"]["heart"], 0.8)
        self.assertEqual(system.affected_by("heart"), ("brain",))

    def test_duplicate_organ_is_rejected(self):
        system = OrganSystemModel()
        system.add_organ(OrganModel("heart"))
        with self.assertRaises(ValueError):
            system.add_organ(OrganModel("heart"))

    def test_self_dependency_is_rejected(self):
        heart = OrganModel("heart")
        with self.assertRaises(ValueError):
            heart.set_dependency("heart", 1.0)


if __name__ == "__main__":
    unittest.main()
