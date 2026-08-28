from backend.cell_population import CellPopulation
from digital_twin.tissue_state import TissueState


def population(population_id, cells, age, health_distribution, confidence):
    return CellPopulation(
        population_id=population_id,
        cell_type="fibroblast",
        cell_count=len(cells),
        source_cell_ids=tuple(cells),
        biological_age_mean=age,
        biological_age_min=age - 2,
        biological_age_max=age + 2,
        healthy_fraction=health_distribution.get("healthy", 0) / len(cells),
        abnormal_fraction=health_distribution.get("abnormal", 0) / len(cells),
        confidence=confidence,
        health_distribution=health_distribution,
    )


def test_population_contract_rejects_duplicate_source_cells():
    candidate = population("p1", ("C1", "C1"), 70, {"healthy": 2}, 0.9)
    try:
        candidate.validate()
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate source cells must be rejected")


def test_tissue_aggregation_preserves_population_and_cell_provenance():
    populations = (
        population("p1", ("C1", "C2"), 70, {"healthy": 1, "abnormal": 1}, 0.8),
        population("p2", ("C3",), 80, {"healthy": 1}, 0.9),
    )
    tissue = TissueState()
    tissue.aggregate_populations(populations)

    assert tissue.cell_count == 3
    assert set(tissue.populations) == {"p1", "p2"}
    assert tissue.metadata["source_cell_ids"] == ("C1", "C2", "C3")
    assert tissue.health_distribution == {"healthy": 2, "abnormal": 1}
    assert tissue.biological_age == (70 * 2 + 80) / 3
    assert tissue.confidence == (0.8 * 2 + 0.9) / 3


def test_tissue_aggregation_rejects_duplicate_cell_provenance_across_populations():
    populations = (
        population("p1", ("C1",), 70, {"healthy": 1}, 0.8),
        population("p2", ("C1",), 80, {"healthy": 1}, 0.9),
    )
    tissue = TissueState()
    try:
        tissue.aggregate_populations(populations)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate cell provenance must be rejected")


def test_missing_population_age_does_not_become_zero_or_healthy():
    candidate = population("p1", ("C1",), 70, {}, 0.7)
    tissue = TissueState()
    tissue.aggregate_populations((candidate,))

    assert tissue.health_distribution == {}
    assert tissue.biological_age == 70
