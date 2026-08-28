"""
Tissue state representation for the digital twin.

This module stores tissue-level biological measurements and can aggregate
single-cell profiles or precomputed cell populations without discarding
cellular distributions.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, Optional
from datetime import datetime

from .cell_population import CellPopulation
from .cell_profile import CellProfile


@dataclass
class TissueState:
    """Represents the current tissue-level state of a subject."""

    tissue_type: str = "skin"

    thickness: Optional[float] = None
    density: Optional[float] = None

    collagen_disorganization: Optional[float] = None
    vascular_abnormality: Optional[float] = None
    inflammation_score: Optional[float] = None
    fibrosis_score: Optional[float] = None
    pigmentation_score: Optional[float] = None

    lesion_burden: Optional[float] = None
    tissue_abnormality_score: Optional[float] = None

    morphology_score: Optional[float] = None
    pathology_score: Optional[float] = None

    cell_count: int = 0
    health_distribution: Dict[str, int] = field(default_factory=dict)
    function_distribution: Dict[str, int] = field(default_factory=dict)
    populations: Dict[str, CellPopulation] = field(default_factory=dict)
    biological_age: Optional[float] = None
    biological_age_range: Optional[tuple[float, float]] = None
    cellular_heterogeneity: float = 0.0

    confidence: float = 0.0

    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    metadata: Dict[str, Any] = field(default_factory=dict)

    def update(
        self,
        values: Dict[str, Any],
        confidence: Optional[float] = None,
    ) -> None:
        """Update tissue state from a dictionary of measurements."""
        for key, value in values.items():
            if key == "metadata":
                if isinstance(value, dict):
                    self.metadata.update(value)
                continue
            if key == "populations" and isinstance(value, dict):
                self.populations = dict(value)
                continue
            if hasattr(self, key):
                setattr(self, key, value)

        if confidence is not None:
            self.confidence = float(confidence)

        self.timestamp = datetime.utcnow().isoformat()

    def aggregate_cells(
        self,
        cells: Iterable[CellProfile],
        confidence: Optional[float] = None,
    ) -> None:
        """Fold cell profiles into this tissue while retaining distributions."""
        cell_list = list(cells)
        self.cell_count = len(cell_list)
        self.health_distribution = {}
        self.function_distribution = {}
        self.populations = {}

        ages = []
        confidence_values = []
        for cell in cell_list:
            self.health_distribution[cell.health.status] = self.health_distribution.get(cell.health.status, 0) + 1
            self.function_distribution[cell.function.status] = self.function_distribution.get(cell.function.status, 0) + 1
            if cell.biological_age is not None:
                ages.append(float(cell.biological_age))
            confidence_values.append(float(cell.confidence))

        if ages:
            self.biological_age = sum(ages) / len(ages)
            self.biological_age_range = (min(ages), max(ages))
        else:
            self.biological_age = None
            self.biological_age_range = None

        if self.cell_count:
            self.cellular_heterogeneity = 1.0 - max(self.health_distribution.values()) / self.cell_count
            inferred = sum(confidence_values) / len(confidence_values)
        else:
            self.cellular_heterogeneity = 0.0
            inferred = 0.0

        self.confidence = max(0.0, min(1.0, float(confidence if confidence is not None else inferred)))
        self.timestamp = datetime.utcnow().isoformat()

    def aggregate_populations(
        self,
        populations: Iterable[CellPopulation],
        confidence: Optional[float] = None,
    ) -> None:
        """Fold precomputed cell populations into this tissue state."""
        population_list = list(populations)
        self.populations = {population.population_id: population for population in population_list}
        self.cell_count = sum(population.cell_count for population in population_list)
        self.health_distribution = {}
        self.function_distribution = {}

        for population in population_list:
            for state, count in population.health_distribution.items():
                self.health_distribution[state] = self.health_distribution.get(state, 0) + count
            for state, count in population.functional_distribution.items():
                self.function_distribution[state] = self.function_distribution.get(state, 0) + count

        if self.cell_count:
            self.biological_age = self._weighted_optional(population_list, "mean_biological_age")
            self.biological_age_range = self._age_range(population_list)
            unknown = self.health_distribution.get("unknown", 0)
            self.cellular_heterogeneity = sum(
                population.heterogeneity * population.cell_count
                for population in population_list
            ) / self.cell_count
            inferred = sum(
                population.mean_confidence * population.cell_count
                for population in population_list
            ) / self.cell_count
            self.metadata["unknown_cell_count"] = unknown
            self.metadata["unknown_cell_fraction"] = unknown / self.cell_count
        else:
            self.biological_age = None
            self.biological_age_range = None
            self.cellular_heterogeneity = 0.0
            inferred = 0.0

        self.confidence = max(0.0, min(1.0, float(confidence if confidence is not None else inferred)))
        self.timestamp = datetime.utcnow().isoformat()

    @staticmethod
    def _weighted_optional(
        populations: Iterable[CellPopulation],
        attribute: str,
    ) -> Optional[float]:
        values = [
            (getattr(population, attribute), population.cell_count)
            for population in populations
            if getattr(population, attribute) is not None and population.cell_count > 0
        ]
        if not values:
            return None
        return sum(value * weight for value, weight in values) / sum(weight for _, weight in values)

    @staticmethod
    def _age_range(populations: Iterable[CellPopulation]) -> Optional[tuple[float, float]]:
        ages = []
        for population in populations:
            age = population.mean_biological_age
            if age is not None:
                ages.append(float(age))
        return (min(ages), max(ages)) if ages else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert tissue state to a serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TissueState":
        """Create TissueState from dictionary."""
        return cls(**data)

    def summary(self) -> Dict[str, Any]:
        """Return a compact tissue summary."""
        return {
            "tissue_type": self.tissue_type,
            "thickness": self.thickness,
            "inflammation_score": self.inflammation_score,
            "fibrosis_score": self.fibrosis_score,
            "collagen_disorganization": self.collagen_disorganization,
            "vascular_abnormality": self.vascular_abnormality,
            "tissue_abnormality_score": self.tissue_abnormality_score,
            "pathology_score": self.pathology_score,
            "cell_count": self.cell_count,
            "health_distribution": dict(self.health_distribution),
            "function_distribution": dict(self.function_distribution),
            "populations": {key: value.to_dict() for key, value in self.populations.items()},
            "biological_age": self.biological_age,
            "biological_age_range": self.biological_age_range,
            "cellular_heterogeneity": self.cellular_heterogeneity,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }
