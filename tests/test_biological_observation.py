from backend.biological_hierarchy import BiologicalHierarchy, BiologicalObservation


def test_observation_validates_confidence():
    observation = BiologicalObservation(
        observation_id="obs-1", source="microscopy", timestamp="2026-01-01T00:00:00+00:00",
        values={"area": 12.5}, quality={"signal_to_noise": 0.9}, confidence=0.8,
    )
    assert observation.values["area"] == 12.5


def test_observations_aggregate_from_cells_to_hand():
    hierarchy = BiologicalHierarchy.create_hand("hand-1")
    hierarchy = hierarchy.add_node("region-1", "region", "dorsal", "hand-1")
    hierarchy = hierarchy.add_node("tissue-1", "tissue", "skin", "region-1")
    hierarchy = hierarchy.add_node("population-1", "cell_population", "keratinocytes", "tissue-1")
    hierarchy = hierarchy.add_node("cell-1", "cell", "cell-1", "population-1")
    hierarchy = hierarchy.with_observation("cell-1", BiologicalObservation("obs-cell-1", "microscopy", "2026-01-01T00:00:00+00:00", {"area": 10.0}, confidence=0.9))

    assert [item.observation_id for item in hierarchy.aggregate_observations("hand-1")] == ["obs-cell-1"]


def test_node_timeline_contains_only_direct_observations():
    hierarchy = BiologicalHierarchy.create_hand("hand-1")
    hierarchy = hierarchy.add_node("region-1", "region", "dorsal", "hand-1")
    hierarchy = hierarchy.with_observation("hand-1", BiologicalObservation("obs-hand", "scanner", "2026-01-01", {"volume": 1}, confidence=0.7))
    hierarchy = hierarchy.with_observation("region-1", BiologicalObservation("obs-region", "imaging", "2027-01-01", {"signal": 2}, confidence=0.8))

    timeline = hierarchy.timeline("hand-1")
    assert [item.observation_id for item in timeline.observations] == ["obs-hand"]


def test_hierarchy_timeline_can_include_descendant_evidence_and_calculate_change():
    hierarchy = BiologicalHierarchy.create_hand("hand-1")
    hierarchy = hierarchy.add_node("region-1", "region", "dorsal", "hand-1")
    hierarchy = hierarchy.add_node("cell-1", "cell", "cell-1", "region-1")
    hierarchy = hierarchy.with_observation("cell-1", BiologicalObservation("obs-1", "microscopy", "2026-01-01", {"marker_x": 0.8}, confidence=0.9))
    hierarchy = hierarchy.with_observation("cell-1", BiologicalObservation("obs-2", "microscopy", "2028-01-01", {"marker_x": 0.6}, confidence=0.85))

    timeline = hierarchy.timeline("hand-1", include_descendants=True)
    changes = timeline.changes("marker_x")
    assert len(changes) == 1
    assert changes[0].delta == -0.2
    assert changes[0].direction == "decreasing"
