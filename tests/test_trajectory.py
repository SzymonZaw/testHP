import unittest

from longitudinal.trajectory import TrajectoryAnalyzer, TrajectoryPoint


class TrajectoryTests(unittest.TestCase):
    def test_increasing_trend(self):
        points = [
            TrajectoryPoint("T1", 0.0, {"marker": 1.0}),
            TrajectoryPoint("T2", 1.0, {"marker": 2.0}),
            TrajectoryPoint("T3", 2.0, {"marker": 3.0}),
        ]
        trend = TrajectoryAnalyzer().analyze(points)[0]
        self.assertEqual(trend.direction, "increasing")
        self.assertAlmostEqual(trend.slope, 1.0)
        self.assertAlmostEqual(trend.delta, 2.0)

    def test_missing_values_are_ignored_per_feature(self):
        points = [
            TrajectoryPoint("T1", 0.0, {"marker": 1.0}),
            TrajectoryPoint("T2", 1.0, {"other": 5.0}),
            TrajectoryPoint("T3", 2.0, {"marker": 3.0}),
        ]
        trends = TrajectoryAnalyzer().analyze(points)
        marker = next(t for t in trends if t.feature == "marker")
        self.assertEqual(marker.points, 2)
        self.assertAlmostEqual(marker.slope, 1.0)

    def test_fewer_than_two_points_returns_no_trends(self):
        point = TrajectoryPoint("T1", 0.0, {"marker": 1.0})
        self.assertEqual(TrajectoryAnalyzer().analyze([point]), ())


if __name__ == "__main__":
    unittest.main()
