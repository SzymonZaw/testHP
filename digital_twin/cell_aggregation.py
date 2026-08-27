"""Hierarchical aggregation of individual cell states."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable

from .individual_cell import IndividualCellState


def aggregate_cells(states: Iterable[IndividualCellState]) -> Dict[str, Any]:
    """Aggregate cell-level observations without losing individual states."""
    grouped: dict[str, list[IndividualCellState]] = defaultdict(list)
    for state in states:
        grouped[state.cell_id].append(state)

    latest = [sorted(items, key=lambda item: item.observed_at)[-1] for items in grouped.values()]

    def mean(field_name: str) -> float | None:
        values = [getattr(item, field_name) for item in latest]
        values = [float(value) for value in values if isinstance(value, (int, float))]
        return sum(values) / len(values) if values else None

    return {
        "cell_count": len(latest),
        "abnormality_mean": mean("abnormality"),
        "senescence_mean": mean("senescence"),
        "biological_age_mean": mean("biological_age"),
        "confidence_mean": mean("confidence"),
        "cells": {item.cell_id: item.to_dict() for item in latest},
    }
