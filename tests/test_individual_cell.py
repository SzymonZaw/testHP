from datetime import datetime, timedelta

from digital_twin.cell_aggregation import aggregate_cells
from digital_twin.individual_cell import CellTimeline, IndividualCellState


def test_cell_timeline_orders_states_and_computes_change():
    timeline = CellTimeline()
    t0 = datetime(2026, 1, 1)
    timeline.add(IndividualCellState("c1", t0 + timedelta(days=1), senescence=0.3))
    timeline.add(IndividualCellState("c1", t0, senescence=0.1))

    assert timeline.latest("c1").senescence == 0.3
    assert timeline.change("c1", "senescence") == 0.2


def test_aggregate_cells_uses_latest_state_per_cell():
    t0 = datetime(2026, 1, 1)
    states = [
        IndividualCellState("c1", t0, abnormality=0.1, confidence=0.9),
        IndividualCellState("c1", t0 + timedelta(days=1), abnormality=0.3, confidence=0.8),
        IndividualCellState("c2", t0, abnormality=0.5, confidence=0.7),
    ]

    result = aggregate_cells(states)

    assert result["cell_count"] == 2
    assert result["abnormality_mean"] == 0.4
    assert result["confidence_mean"] == 0.75
    assert set(result["cells"]) == {"c1", "c2"}
