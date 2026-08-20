from datetime import datetime, timezone

from core.anatomy import AnatomicalLocation
from core.biological_state_aggregation import BiologicalStateAggregator
from core.evidence import Evidence
from core.observation import Observation
from backend.biological_state_routes import _confidence_payload


def _observation(observation_id, spatial_id, parent_id=None, validated=None):
    return Observation(
        id=observation_id,
        subject_id="own_cohort",
        timepoint_id="T0",
        name=observation_id,
        value=1,
        observed_at=datetime.now(timezone.utc),
        anatomical_location=AnatomicalLocation(
            id=spatial_id,
            name=spatial_id,
            level="site",
            parent_id=parent_id,
        ),
        metadata={"validated_interpretations": validated or {}},
        biological_level="tissue",
        modality="manual-entry",
    )


def test_confidence_is_unknown_without_evidence_confidence():
    assert _confidence_payload(None) == {"value": None, "label": "Nieustalona", "status": "unknown"}


def test_confidence_is_derived_from_explicit_evidence_only():
    observation = _observation("obs-1", "hand/palm")
    evidence = Evidence(id="ev-1", subject_id="own_cohort", observation_id="obs-1", confidence=0.8)
    aggregator = BiologicalStateAggregator([observation], [evidence], [observation.anatomical_location])
    state = aggregator.build_state("own_cohort", "T0", location_id="hand/palm")
    assert state.evidence_ids == ("ev-1",)
    assert state.confidence == 0.8


def test_validated_interpretation_requires_linked_evidence():
    observation = _observation("obs-1", "hand/palm", validated={"damage": "badanie sugeruje zmianę"})
    aggregator = BiologicalStateAggregator([observation], [], [observation.anatomical_location])
    state = aggregator.build_state("own_cohort", "T0", location_id="hand/palm")
    assert state.interpretation("damage") is None


def test_descendant_evidence_is_explicitly_aggregated_to_parent():
    parent = _observation("parent", "hand/palm")
    child = _observation("child", "hand/palm/central-palm", parent_id="hand/palm")
    evidence = Evidence(id="ev-child", subject_id="own_cohort", observation_id="child", confidence=0.6)
    aggregator = BiologicalStateAggregator(
        [parent, child],
        [evidence],
        [parent.anatomical_location, child.anatomical_location],
    )
    assert aggregator.summarize_location("hand/palm", include_descendants=False).count == 0
    summary = aggregator.summarize_location("hand/palm", include_descendants=True)
    assert summary.evidence_ids == ("ev-child",)
    assert summary.status == "observed"
