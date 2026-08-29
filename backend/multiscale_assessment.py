"""Multiscale roll-up of cell assessments with conservative uncertainty handling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .cell_state_assessment import CellStateAssessment


@dataclass(frozen=True)
class MultiscaleAssessment:
    level: str
    node_id: str
    cell_count: int
    healthy_count: int
    diseased_count: int
    unknown_count: int
    mean_biological_age: float | None
    confidence: float | None
    uncertainty_interval: tuple[float, float] | None
    evidence_ids: tuple[str, ...]
    source_cell_ids: tuple[str, ...]

    @property
    def health_state(self) -> str:
        if self.cell_count == 0:
            return "unknown"
        if self.diseased_count:
            return "diseased_signal"
        if self.unknown_count == self.cell_count:
            return "unknown"
        if self.healthy_count == self.cell_count:
            return "healthy_signal"
        return "mixed"

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "node_id": self.node_id,
            "cell_count": self.cell_count,
            "healthy_count": self.healthy_count,
            "diseased_count": self.diseased_count,
            "unknown_count": self.unknown_count,
            "health_state": self.health_state,
            "mean_biological_age": self.mean_biological_age,
            "confidence": self.confidence,
            "uncertainty_interval": self.uncertainty_interval,
            "evidence_ids": self.evidence_ids,
            "source_cell_ids": self.source_cell_ids,
        }


def _health_counts(items: list[CellStateAssessment]) -> tuple[int, int, int]:
    healthy = sum(item.health_state == "healthy" for item in items)
    diseased = sum(item.health_state == "diseased" for item in items)
    unknown = len(items) - healthy - diseased
    return healthy, diseased, unknown


def aggregate_assessments(
    assessments: Iterable[CellStateAssessment],
    *,
    cell_to_population: dict[str, str],
    population_to_tissue: dict[str, str],
    tissue_to_region: dict[str, str],
    hand_id: str,
) -> list[MultiscaleAssessment]:
    """Aggregate cell state assessments to population, tissue, region and hand."""
    grouped: dict[tuple[str, str], list[CellStateAssessment]] = {}
    for item in assessments:
        population = cell_to_population.get(item.cell_id)
        if population is None:
            raise ValueError(f"missing population mapping for cell {item.cell_id}")
        tissue = population_to_tissue.get(population)
        if tissue is None:
            raise ValueError(f"missing tissue mapping for population {population}")
        region = tissue_to_region.get(tissue)
        if region is None:
            raise ValueError(f"missing region mapping for tissue {tissue}")
        grouped.setdefault(("cell_population", population), []).append(item)
        grouped.setdefault(("tissue", tissue), []).append(item)
        grouped.setdefault(("region", region), []).append(item)
        grouped.setdefault(("hand", hand_id), []).append(item)

    result: list[MultiscaleAssessment] = []
    for (level, node_id), items in grouped.items():
        ages = [item.biological_age for item in items if item.biological_age is not None]
        confidences = [item.confidence for item in items if item.confidence is not None]
        intervals = [item.age_interval for item in items if item.age_interval is not None]
        evidence = tuple(sorted({e for item in items for e in item.evidence_ids}))
        healthy, diseased, unknown = _health_counts(items)
        result.append(MultiscaleAssessment(
            level=level,
            node_id=node_id,
            cell_count=len(items),
            healthy_count=healthy,
            diseased_count=diseased,
            unknown_count=unknown,
            mean_biological_age=sum(ages) / len(ages) if ages else None,
            confidence=min(confidences) if confidences else None,
            uncertainty_interval=(min(i[0] for i in intervals), max(i[1] for i in intervals)) if intervals else None,
            evidence_ids=evidence,
            source_cell_ids=tuple(sorted({item.cell_id for item in items})),
        ))
    order = {"cell_population": 0, "tissue": 1, "region": 2, "hand": 3}
    return sorted(result, key=lambda item: (order[item.level], item.node_id))
