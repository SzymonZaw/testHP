from backend.cell_health_v2 import CellHealthAssessment, CellState
from backend.biological_age_v2 import BiologicalAgeAssessment
from backend.pathology_v2 import PathologySignal, AbnormalityCluster
from backend.temporal_twin_v2 import Timepoint, TemporalChange, TemporalTwin
from backend.personal_baseline_v2 import BaselineFeature, PersonalBaseline, BaselineDeviation
from backend.risk_intervention_v2 import RiskMapEntry, RiskLevel, InterventionMapEntry, InterventionAction

def test_cell_health():
    CellHealthAssessment("c1", CellState.HEALTHY, confidence=.95, baseline_id="b1").validate()

def test_unknown_requires_limitations():
    try: CellHealthAssessment("c1", CellState.UNKNOWN).validate(); assert False
    except ValueError: pass

def test_biological_age_interval():
    BiologicalAgeAssessment("c1","keratinocyte",65,71,68,74,confidence=.8).validate()

def test_pathology():
    PathologySignal("p1","hand/palm","abnormality",confidence=.7).validate()
    AbnormalityCluster("a1","hand/palm",signal_ids=("p1",),confidence=.7).validate()

def test_temporal_twin():
    t=TemporalTwin("tw",(Timepoint("t0","2026-01-01"),Timepoint("t1","2028-01-01")),changes=(TemporalChange("ch","hand/palm","t0","t1",{"health":-.1}, {"health":-.05},"decline",.8),))
    t.validate()

def test_personal_baseline():
    b=PersonalBaseline("b1","s1",(BaselineFeature("thickness","um",10,8,12,.5),),("t0",))
    d=BaselineDeviation("s1","b1","t1",{"thickness":2})
    d.validate(); assert b.features[0].lower < b.features[0].center < b.features[0].upper

def test_risk_and_intervention():
    RiskMapEntry("hand/palm",RiskLevel.MONITOR,.4,.9).validate()
    InterventionMapEntry("hand/palm",InterventionAction.INVESTIGATE,1,.8,expert_review_status="required").validate()
