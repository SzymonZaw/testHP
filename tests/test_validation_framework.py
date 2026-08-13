import unittest

from validation.framework import ValidationCase, ValidationFramework


class ValidationFrameworkTests(unittest.TestCase):
    def test_regression_metrics(self):
        cases = [
            ValidationCase("a", 1.0, 0.0),
            ValidationCase("b", 3.0, 2.0),
        ]
        result = ValidationFramework().evaluate(cases)
        self.assertEqual(result.n, 2)
        self.assertAlmostEqual(result.mean_absolute_error, 1.0)
        self.assertAlmostEqual(result.root_mean_squared_error, 1.0)
        self.assertAlmostEqual(result.mean_bias, 1.0)
        self.assertFalse(result.insufficient_evidence)

    def test_low_quality_is_excluded(self):
        result = ValidationFramework(minimum_cases=1).evaluate([
            ValidationCase("a", 100.0, 0.0, quality_score=0.1),
            ValidationCase("b", 2.0, 1.0),
        ])
        self.assertEqual(result.n, 1)
        self.assertFalse(result.insufficient_evidence)

    def test_subgroup_evaluation(self):
        cases = [
            ValidationCase("a", 1.0, 0.0, subgroup="A"),
            ValidationCase("b", 2.0, 2.0, subgroup="A"),
            ValidationCase("c", 4.0, 2.0, subgroup="B"),
            ValidationCase("d", 4.0, 4.0, subgroup="B"),
        ]
        results = ValidationFramework().evaluate_subgroups(cases)
        self.assertEqual(set(results), {"A", "B"})
        self.assertAlmostEqual(results["A"].mean_absolute_error, 0.5)
        self.assertAlmostEqual(results["B"].mean_absolute_error, 1.0)


if __name__ == "__main__":
    unittest.main()
