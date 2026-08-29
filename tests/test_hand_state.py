from backend.anatomical_region_state import AnatomicalRegionState
from backend.hand_state import HandState


def region(region_id, cells, age, health, function, confidence):
    return AnatomicalRegionState(
        region_id=region_id,
        name=region_id,
        cell_count=len(cells),
        health_distribution=health,
        function_distribution=function,
        biological_age=age,
        biological_age_range=(age - 2, age + 2),
        confidence=confidence,
        source_population_ids=(f"{region_id}-p",),
        source_cell_ids=tuple(cells),
    )


def test_hand_aggregates_regions_and_preserves_provenance():
    hand = HandState(hand_id="hand-1", laterality="left")
    hand.aggregate_regions(
        (
            region("palm", ("C1", "C2"), 70, {"healthy": 1, "abnormal": 1}, {"normal": 2}, 0.8),
            region("thumb", ("C3",), 80, {"healthy": 1}, {"normal": 1}, 0.9),
        )
    )

    assert hand.cell_count == 3
    assert set(hand.anatomical_regions) == {"palm", "thumb"}
    assert hand.health_distribution == {"healthy": 2, "abnormal": 1}
    assert hand.function_distribution == {"normal": 3}
    assert hand.source_population_ids == ("palm-p", "thumb-p")
    assert hand.source_cell_ids == ("C1", "C2", "C3")
    assert hand.biological_age == (70 * 2 + 80) / 3
    assert hand.biological_age_range == (68, 82)
    assert hand.confidence == (0.8 * 2 + 0.9) / 3
    assert hand.laterality == "left"


def test_hand_rejects_duplicate_population_ids():
    hand = HandState(hand_id="hand-1")
    try:
        hand.aggregate_regions(
            (
                region("r1", ("C1",), 70, {"healthy": 1}, {"normal": 1}, 0.8),
                region("r2", ("C2",), 71, {"healthy": 1}, {"normal": 1}, 0.9),
            )
        )
        hand.anatomical_regions["r2"].source_population_ids = ("r1-p",)
        hand.aggregate_regions(tuple(hand.anatomical_regions.values()))
    except ValueError as exc:
        assert "duplicate source population" in str(exc)
    else:
        raise AssertionError("duplicate population ids must be rejected")


def test_hand_rejects_duplicate_cell_ids():
    hand = HandState(hand_id="hand-1")
    try:
        hand.aggregate_regions(
            (
                region("r1", ("C1",), 70, {"healthy": 1}, {"normal": 1}, 0.8),
                region("r2", ("C1",), 71, {"healthy": 1}, {"normal": 1}, 0.9),
            )
        )
    except ValueError as exc:
        assert "duplicate source cell" in str(exc)
    else:
        raise AssertionError("duplicate cell ids must be rejected")


def test_hand_handles_regions_without_age():
    hand = HandState(hand_id="hand-1")
    region_state = AnatomicalRegionState(
        region_id="r1",
        name="Region",
        cell_count=1,
        health_distribution={"healthy": 1},
        function_distribution={"normal": 1},
        biological_age=None,
        confidence=0.7,
        source_population_ids=("p1",),
        source_cell_ids=("C1",),
    )
    hand.aggregate_regions((region_state,))

    assert hand.biological_age is None
    assert hand.biological_age_range is None
    assert hand.source_cell_ids == ("C1",)
