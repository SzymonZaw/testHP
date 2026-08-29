from backend.cell_state_contract import CellHealthAssessment, CellState
from backend.biological_age_contract import BiologicalAgeAssessment
from backend.pathology_contract import PathologySignal
from backend.temporal_twin_contract import TemporalChange, TemporalTwin, Timepoint
from backend.risk_intervention_contract import InterventionAction, InterventionMapEntry, RiskLevel, RiskMapEntry


def test_health_assessment_requires_limitation_for_unknown():
    try:
        CellHealthAssessment("c1", CellState.UNKNOWN).validate()
    except ValueError:
        pass
    else:
        raise AssertionError("unknown health without limitation must fail")


def test_age_assessment_validates_interval():
    age = BiologicalAgeAssessment("c1", "cellular-biological-age-v1", 71, 65, 68, 74, .8)
    age.validate()


def test_temporal_twin_references_known_timepoints():
    twin = TemporalTwin("twin-1", (Timepoint("2026", "2026-01-01"), Timepoint("2028", "2028-01-01")), (TemporalChange("hand/palm", "2026", "2028", {"health": -.1}, "decline", .7),))
    twin.validate()


def test_risk_and_intervention_are_bounded():
    RiskMapEntry("hand/palm", RiskLevel.MONITOR, .3, .9).validate()
    InterventionMapEntry("hand/palm", InterventionAction.INVESTIGATE, 1, .8).validate()


def test_pathology_signal_is_location_anchored():
    PathologySignal("p1", "hand/palm", category="unknown", confidence=.5).validate()
