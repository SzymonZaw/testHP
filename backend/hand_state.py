"""Aggregate anatomical region states into a traceable hand state."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from .anatomical_region_state import AnatomicalRegionState


@dataclass
class HandState:
    """Current observational state of one hand, without treatment decisions."""

    hand_id: str
    laterality: str = "unknown"
    anatomical_regions: dict[str, AnatomicalRegionState] = field(default_factory=dict)
    cell_count: int = 0
    health_distribution: dict[str, int] = field(default_factory=dict)
    function_distribution: dict[str, int] = field(default_factory=dict)
    biological_age: float | None = None
    biological_age_range: tuple[float, float] | None = None
    cellular_heterogeneity: float = 0.0
    confidence: float = 0.0
    source_population_ids: tuple[str, ...] = field(default_factory=tuple)
    source_cell_ids: tuple[str, ...] = field(default_factory=tuple)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def aggregate_regions(
        self,
        regions: Iterable[AnatomicalRegionState],
        confidence: float | None = None,
    ) -> None:
        """Aggregate regions while preserving provenance down to source cells."""
        region_list = tuple(regions)
        self.anatomical_regions = {region.region_id: region for region in region_list}
        self.cell_count = sum(region.cell_count for region in region_list)
        self.health_distribution = {}
        self.function_distribution = {}
        population_ids: list[str] = []
        cell_ids: list[str] = []

        for region in region_list:
            for state, count in region.health_distribution.items():
                self.health_distribution[state] = self.health_distribution.get(state, 0) + count
            for state, count in region.function_distribution.items():
                self.function_distribution[state] = self.function_distribution.get(state, 0) + count
            population_ids.extend(region.source_population_ids)
            cell_ids.extend(region.source_cell_ids)

        if len(population_ids) != len(set(population_ids)):
            raise ValueError("hand contains duplicate source population ids")
        if len(cell_ids) != len(set(cell_ids)):
            raise ValueError("hand contains duplicate source cell ids")

        self.source_population_ids = tuple(sorted(population_ids))
        self.source_cell_ids = tuple(sorted(cell_ids))

        age_pairs = [
            (region.biological_age, region.cell_count)
            for region in region_list
            if region.biological_age is not None and region.cell_count > 0
        ]
        if age_pairs:
            total_weight = sum(weight for _, weight in age_pairs)
            self.biological_age = sum(age * weight for age, weight in age_pairs) / total_weight
            ranges = [region.biological_age_range for region in region_list if region.biological_age_range is not None]
            self.biological_age_range = (
                (min(item[0] for item in ranges), max(item[1] for item in ranges))
                if ranges else None
            )
        else:
            self.biological_age = None
            self.biological_age_range = None

        self.cellular_heterogeneity = (
            1.0 - max(self.health_distribution.values()) / self.cell_count
            if self.cell_count else 0.0
        )
        inferred = (
            sum(region.confidence * region.cell_count for region in region_list) / self.cell_count
            if self.cell_count else 0.0
        )
        self.confidence = max(0.0, min(1.0, float(confidence if confidence is not None else inferred)))
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
