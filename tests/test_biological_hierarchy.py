from backend.biological_hierarchy import BiologicalHierarchy, BiologicalObservation


def test_hierarchy_can_represent_hand_to_molecular_scales():
    hierarchy = BiologicalHierarchy.create_hand("hand-1")
    hierarchy = hierarchy.add_node("region-1", "region", "palm", "hand-1")
    hierarchy = hierarchy.add_node("structure-1", "structure", "skin", "region-1")
    hierarchy = hierarchy.add_node("tissue-1", "tissue", "epidermis", "structure-1")
    hierarchy = hierarchy.add_node("population-1", "cell_population", "keratinocytes", "tissue-1")
    hierarchy = hierarchy.add_node("cell-1", "cell", "keratinocyte", "population-1")
    hierarchy = hierarchy.add_node("molecular-1", "molecular", "marker-panel", "cell-1")

    assert hierarchy.levels() == (
        "hand", "region", "structure", "tissue", "cell_population", "cell", "molecular"
    )
    assert hierarchy.nodes["hand-1"].child_ids == ("region-1",)
    assert hierarchy.nodes["cell-1"].parent_id == "population-1"


def test_observation_confidence_is_bounded():
    observation = BiologicalObservation("obs-1", "microscopy", "2026-01-01", confidence=0.9)
    assert observation.confidence == 0.9


def test_observation_rejects_invalid_confidence():
    try:
        BiologicalObservation("obs-1", "source", "2026-01-01", confidence=1.1)
    except ValueError as exc:
        assert "confidence" in str(exc)
    else:
        raise AssertionError("invalid confidence should be rejected")
