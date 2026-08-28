from backend.anatomical_region_state import AnatomicalRegionState
from digital_twin.tissue_state import TissueState


def tissue(population_id, cells, age, health, function, confidence):
    return TissueState(
        tissue_type="dermis",
        cell_count=len(cells),
        health_distribution=health,
        function_distribution=function,
        biological_age=age,
        biological_age_range=(age - 2, age + 2),
        confidence=confidence,
        populations={population_id: object()},
        metadata={"source_cell_ids": tuple(cells)},
    )


def test_region_aggregates_tissues_and_preserves_provenance():
    region = AnatomicalRegionState("palm-dermis", "Palm dermis")
    region.aggregate_tissues(
        (
            tissue("p1", ("C1", "C2"), 70, {"healthy": 1, "abnormal": 1}, {"normal": 2}, 0.8),
            tissue("p2", ("C3",), 80, {"healthy": 1}, {"normal": 1}, 0.9),
        )
    )

    assert region.cell_count == 3
    assert region.health_distribution == {"healthy": 2, "abnormal": 1}
    assert region.function_distribution == {"normal": 3}
    assert region.source_population_ids == ("p1", "p2")
    assert region.source_cell_ids == ("C1", "C2", "C3")
    assert region.biological_age == (70 * 2 + 80) / 3
    assert region.biological_age_range == (68, 82)
    assert region.confidence == (0.8 * 2 + 0.9) / 3


def test_region_rejects_duplicate_population_ids():
    region = AnatomicalRegionState("r1", "Region")
    try:
        region.aggregate_tissues(
            (
                tissue("p1", ("C1",), 70, {"healthy": 1}, {"normal": 1}, 0.8),
                tissue("p1", ("C2",), 70, {"healthy": 1}, {"normal": 1}, 0.8),
            )
        )
    except ValueError as exc:
        assert "duplicate population" in str(exc)
    else:
        raise AssertionError("duplicate population ids must be rejected")


def test_region_rejects_duplicate_cell_ids():
    region = AnatomicalRegionState("r1", "Region")
    try:
        region.aggregate_tissues(
            (
                tissue("p1", ("C1",), 70, {"healthy": 1}, {"normal": 1}, 0.8),
                tissue("p2", ("C1",), 71, {"healthy": 1}, {"normal": 1}, 0.9),
            )
        )
    except ValueError as exc:
        assert "duplicate source cell" in str(exc)
    else:
        raise AssertionError("duplicate cell ids must be rejected")


def test_region_handles_missing_age():
    region = AnatomicalRegionState("r1", "Region")
    tissue_state = TissueState(
        tissue_type="dermis",
        cell_count=1,
        health_distribution={"healthy": 1},
        function_distribution={"normal": 1},
        biological_age=None,
        confidence=0.7,
        populations={"p1": object()},
        metadata={"source_cell_ids": ("C1",)},
    )
    region.aggregate_tissues((tissue_state,))

    assert region.biological_age is None
    assert region.biological_age_range is None
    assert region.source_cell_ids == ("C1",)
