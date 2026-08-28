"""Aggregate tissue states into traceable anatomical regions."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Iterable

from .cell_population import CellPopulation
from digital_twin.tissue_state import TissueState


@dataclass
class AnatomicalRegionState:
    """Region-level state that preserves tissue and cellular provenance."""

    region_id: str
    name: str
    tissue_states: tuple[TissueState, ...] = field(default_factory=tuple)
    cell_count: int = 0
    health_distribution: dict[str, int] = field(default_factory=dict)
    function_distribution: dict[str, int] = field(default_factory=dict)
    biological_age: float | None = None
    biological_age_range: tuple[float, float] | None = None
    confidence: float = 0.0
    source_population_ids: tuple[str, ...] = field(default_factory=tuple)
    source_cell_ids: tuple[str, ...] = field(default_factory=tuple)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def aggregate_tissues(self, tissues: Iterable[TissueState], confidence: float | None = None) -> None:
        """Aggregate tissues without losing population or cell provenance."""
        tissue_list = tuple(tissues)
        self.tissue_states = tissue_list
        self.cell_count = sum(tissue.cell_count for tissue in tissue_list)
        self.health_distribution = {}
        self.function_distribution = {}
        population_ids: list[str] = []
        cell_ids: list[str] = []

        for tissue in tissue_list:
            for state, count in tissue.health_distribution.items():
                self.health_distribution[state] = self.health_distribution.get(state, 0) + count
            for state, count in tissue.function_distribution.items():
                self.function_distribution[state] = self.function_distribution.get(state, 0) + count
            population_ids.extend(tissue.populations.keys())
            cell_ids.extend(tissue.metadata.get("source_cell_ids", ()))

        if len(population_ids) != len(set(population_ids)):
            raise ValueError("anatomical region contains duplicate population ids")
        if len(cell_ids) != len(set(cell_ids)):
            raise ValueError("anatomical region contains duplicate source cell ids")

        self.source_population_ids = tuple(sorted(population_ids))
        self.source_cell_ids = tuple(sorted(cell_ids))

        age_pairs = [
            (tissue.biological_age, tissue.cell_count)
            for tissue in tissue_list
            if tissue.biological_age is not None and tissue.cell_count > 0
        ]
        if age_pairs:
            total_weight = sum(weight for _, weight in age_pairs)
            self.biological_age = sum(age * weight for age, weight in age_pairs) / total_weight
            ranges = [tissue.biological_age_range for tissue in tissue_list if tissue.biological_age_range is not None]
            self.biological_age_range = (min(item[0] for item in ranges), max(item[1] for item in ranges)) if ranges else None
        else:
            self.biological_age = None
            self.biological_age_range = None

        inferred = (
            sum(tissue.confidence * tissue.cell_count for tissue in tissue_list) / self.cell_count
            if self.cell_count else 0.0
        )
        self.confidence = max(0.0, min(1.0, float(confidence if confidence is not None else inferred)))
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
