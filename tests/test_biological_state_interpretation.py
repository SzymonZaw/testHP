from datetime import datetime, timezone

from core.anatomy import AnatomicalLocation
from core.biological_state_aggregation import BiologicalStateAggregator
from core.evidence import Evidence
from core.observation import Observation
from backend.biological_state_routes import _canonical_parent_id, _confidence_payload


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


def test_deep_spatial_ids_use_the_immediate_parent():
    assert _canonical_parent_id("hand/palm") == "hand"
    assert _canonical_parent_id("hand/palm/thenar-eminence") == "hand/palm"
    assert _canonical_parent_id("hand/palm/thenar-eminence/field-b") == "hand/palm/thenar-eminence"
    assert _canonical_parent_id("hand/palm/thenar-eminence/field-b/cell-3") == "hand/palm/thenar-eminence/field-b"
    assert _canonical_parent_id("hand/palm/thenar-eminence/field-b/cell-3/marker-a") == "hand/palm/thenar-eminence/field-b/cell-3"


def test_deep_descendant_evidence_reaches_every_ancestor():
    ids = [
        "hand/palm",
        "hand/palm/thenar-eminence",
        "hand/palm/thenar-eminence/field-b",
        "hand/palm/thenar-eminence/field-b/cell-3",
    ]
    locations = []
    observations = []
    for index, spatial_id in enumerate(ids):
        parent_id = _canonical_parent_id(spatial_id)
        observation = _observation(f"obs-{index}", spatial_id, parent_id=parent_id)
        observations.append(observation)
        locations.append(observation.anatomical_location)

    leaf_evidence = Evidence(id="ev-leaf", subject_id="own_cohort", observation_id="obs-3", confidence=0.7)
    aggregator = BiologicalStateAggregator(observations, [leaf_evidence], locations)

    for ancestor in ids[:-1]:
        summary = aggregator.summarize_location(ancestor, include_descendants=True)
        assert summary.evidence_ids == ("ev-leaf",)
        assert summary.count == 1
        assert summary.status == "observed"

    assert aggregator.summarize_location(ids[-1], include_descendants=False).count == 1
