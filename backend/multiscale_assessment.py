"""Multiscale roll-up of cell assessments with conservative uncertainty handling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .anatomy_foundation import CellStateAssessment
from .risk_signal import RiskSignal


@dataclass(frozen=True)
class MultiscaleAssessment:
    level: str
    node_id: str
    cell_count: int
    healthy_count: int
    diseased_count: int
    unknown_count: int
    confidence: float | None
    uncertainty: float | None
    evidence_ids: tuple[str, ...]
    source_cell_ids: tuple[str, ...]

    @property
    def health_state(self) -> str:
        if self.cell_count == 0 or self.unknown_count == self.cell_count:
            return "unknown"
        if self.diseased_count:
            return "diseased_signal"
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
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "evidence_ids": self.evidence_ids,
            "source_cell_ids": self.source_cell_ids,
        }

    def to_risk_signal(self) -> RiskSignal:
        """Translate one multiscale observation into a non-diagnostic risk signal."""
        if self.health_state == "diseased_signal":
            severity = "high"
        elif self.health_state == "mixed":
            severity = "moderate"
        else:
            severity = "low"
        return RiskSignal(
            signal_type=f"{self.level}_health_change",
            severity=severity,
            confidence=float(self.confidence or 0.0),
            region=self.node_id if self.level == "region" else None,
            evidence={
                "level": self.level,
                "node_id": self.node_id,
                "health_state": self.health_state,
                "uncertainty": self.uncertainty,
                "evidence_ids": self.evidence_ids,
                "source_cell_ids": self.source_cell_ids,
            },
        )


def _health_counts(items: list[CellStateAssessment]) -> tuple[int, int, int]:
    healthy = sum(item.state == "normal" for item in items)
    diseased = sum(item.state == "pathological" for item in items)
    unknown = len(items) - healthy - diseased
    return healthy, diseased, unknown


def _aggregate(items: list[CellStateAssessment], level: str, node_id: str) -> MultiscaleAssessment:
    healthy, diseased, unknown = _health_counts(items)
    confidences = [item.confidence for item in items if item.confidence is not None]
    evidence_ids = tuple(sorted({e.evidence_id for item in items for e in item.evidence}))
    source_ids = tuple(sorted({item.cell_id for item in items}))
    return MultiscaleAssessment(
        level=level,
        node_id=node_id,
        cell_count=len(items),
        healthy_count=healthy,
        diseased_count=diseased,
        unknown_count=unknown,
        confidence=min(confidences) if confidences else None,
        uncertainty=(1.0 - min(confidences)) if confidences else 1.0,
        evidence_ids=evidence_ids,
        source_cell_ids=source_ids,
    )


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

    result = [_aggregate(items, level, node_id) for (level, node_id), items in grouped.items()]
    order = {"cell_population": 0, "tissue": 1, "region": 2, "hand": 3}
    return sorted(result, key=lambda item: (order[item.level], item.node_id))


def assessments_to_risk_signals(assessments: Iterable[MultiscaleAssessment]) -> tuple[RiskSignal, ...]:
    """Bridge multiscale observations into the existing RiskModel contract."""
    return tuple(item.to_risk_signal() for item in assessments)
