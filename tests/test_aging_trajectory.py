import pytest

from aging import AgingClockResult, AgingObservation, AgingTrajectoryAnalyzer


def result(name, score):
    return AgingClockResult(name, score, ("feature",), ())


def test_aging_rate_increases():
    observations = [
        AgingObservation(0, result("cell", 40)),
        AgingObservation(2, result("cell", 44)),
    ]
    rates = AgingTrajectoryAnalyzer().analyze(observations)
    assert rates[0].slope == pytest.approx(2.0)
    assert rates[0].delta == pytest.approx(4.0)
    assert rates[0].direction == "increasing"


def test_multiple_clocks_are_kept_separate():
    observations = [
        AgingObservation(0, result("cell", 40)),
        AgingObservation(1, result("cell", 41)),
        AgingObservation(0, result("tissue", 50)),
        AgingObservation(1, result("tissue", 49)),
    ]
    rates = AgingTrajectoryAnalyzer().analyze(observations)
    assert {rate.clock_name for rate in rates} == {"cell", "tissue"}


def test_single_observation_has_no_rate():
    observations = [AgingObservation(0, result("cell", 40))]
    assert AgingTrajectoryAnalyzer().analyze(observations) == ()
