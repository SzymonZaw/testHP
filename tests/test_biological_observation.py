from backend.biological_hierarchy import BiologicalHierarchy, BiologicalObservation


def test_observation_validates_confidence():
    observation = BiologicalObservation(
        observation_id="obs-1",
        source="microscopy",
        timestamp="2026-01-01T00:00:00+00:00",
        values={"area": 12.5},
        quality={"signal_to_noise": 0.9},
        confidence=0.8,
    )
    assert observation.values["area"] == 12.5


def test_observations_aggregate_from_cells_to_hand():
    hierarchy = BiologicalHierarchy.create_hand("hand-1")
    hierarchy = hierarchy.add_node("region-1", "region", "dorsal", "hand-1")
    hierarchy = hierarchy.add_node("tissue-1", "tissue", "skin", "region-1")
    hierarchy = hierarchy.add_node("population-1", "cell_population", "keratinocytes", "tissue-1")
    hierarchy = hierarchy.add_node("cell-1", "cell", "cell-1", "population-1")

    observation = BiologicalObservation(
        observation_id="obs-cell-1",
        source="microscopy",
        timestamp="2026-01-01T00:00:00+00:00",
        values={"area": 10.0},
        confidence=0.9,
    )
    hierarchy = hierarchy.with_observation("cell-1", observation)

    aggregated = hierarchy.aggregate_observations("hand-1")
    assert [item.observation_id for item in aggregated] == ["obs-cell-1"]


def test_direct_and_descendant_observations_are_kept_distinct():
    hierarchy = BiologicalHierarchy.create_hand("hand-1")
    hierarchy = hierarchy.add_node("region-1", "region", "dorsal", "hand-1")
    direct = BiologicalObservation("obs-hand", "scanner", "2026-01-01", {"volume": 1}, confidence=0.7)
    child = BiologicalObservation("obs-region", "imaging", "2026-01-02", {"signal": 2}, confidence=0.8)
    hierarchy = hierarchy.with_observation("hand-1", direct)
    hierarchy = hierarchy.with_observation("region-1", child)

    ids = {item.observation_id for item in hierarchy.aggregate_observations("hand-1")}
    assert ids == {"obs-hand", "obs-region"}
