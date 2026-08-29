"""Unified multiscale health and aging assessment."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from .anatomy_foundation import CellStateAssessment
from .assessment_trace import AssessmentTrace
from .risk_signal import RiskSignal
from .hand_aging_profile import HandAgingProfile
from .aging_priority import AgingPriority
from .hierarchy_mapping import HierarchyMappingRegistry


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
    aging_profile: HandAgingProfile | None = None
    aging_priorities: tuple[AgingPriority, ...] = ()
    trace: AssessmentTrace | None = None

    def __post_init__(self) -> None:
        if self.trace is not None:
            if self.trace.level != self.level or self.trace.node_id != self.node_id:
                raise ValueError("assessment trace must match assessment level and node_id")

    @property
    def health_state(self) -> str:
        if self.cell_count == 0 or self.unknown_count == self.cell_count:
            return "unknown"
        if self.diseased_count:
            return "diseased_signal"
        if self.healthy_count == self.cell_count:
            return "healthy_signal"
        return "mixed"

    @property
    def aging_priority_count(self) -> int:
        return len(self.aging_priorities)

    @property
    def aging_priority_max(self) -> float | None:
        scores = [item.priority_score for item in self.aging_priorities if item.priority_score is not None]
        return max(scores) if scores else None

    def with_trace(self, trace: AssessmentTrace) -> "MultiscaleAssessment":
        """Return this assessment with an explicit audit/provenance trace."""
        if trace.level != self.level or trace.node_id != self.node_id:
            raise ValueError("assessment trace must match assessment level and node_id")
        return replace(self, trace=trace)

    def with_aging(self, aging_profile: HandAgingProfile, aging_priorities: Iterable[AgingPriority] = ()) -> "MultiscaleAssessment":
        """Attach hand-level aging information to an existing assessment."""
        if self.level != "hand":
            raise ValueError("aging_profile can only be attached to a hand assessment")
        if self.node_id != aging_profile.hand_id:
            raise ValueError("aging_profile hand_id must match assessment node_id")
        evidence_ids = tuple(sorted(set(self.evidence_ids) | set(aging_profile.evidence_ids)))
        trace = self.trace
        if trace is not None:
            trace = replace(trace, evidence_ids=tuple(sorted(set(trace.evidence_ids) | set(aging_profile.evidence_ids))))
        return replace(self, evidence_ids=evidence_ids, aging_profile=aging_profile,
                       aging_priorities=tuple(aging_priorities), trace=trace)

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level, "node_id": self.node_id,
            "cell_count": self.cell_count, "healthy_count": self.healthy_count,
            "diseased_count": self.diseased_count, "unknown_count": self.unknown_count,
            "health_state": self.health_state, "confidence": self.confidence,
            "uncertainty": self.uncertainty, "evidence_ids": self.evidence_ids,
            "source_cell_ids": self.source_cell_ids,
            "aging_profile": self.aging_profile.to_dict() if self.aging_profile else None,
            "aging_priorities": tuple(item.to_dict() for item in self.aging_priorities),
            "aging_priority_count": self.aging_priority_count,
            "aging_priority_max": self.aging_priority_max,
            "trace": self.trace.to_dict() if self.trace else None,
        }

    def to_risk_signal(self) -> RiskSignal:
        if self.health_state == "diseased_signal": severity = "high"
        elif self.health_state == "mixed": severity = "moderate"
        else: severity = "low"
        return RiskSignal(
            signal_type=f"{self.level}_health_change", severity=severity,
            confidence=float(self.confidence or 0.0),
            region=self.node_id if self.level == "region" else None,
            evidence={"level": self.level, "node_id": self.node_id,
                      "health_state": self.health_state, "uncertainty": self.uncertainty,
                      "evidence_ids": self.evidence_ids, "source_cell_ids": self.source_cell_ids,
                      "aging_priority_count": self.aging_priority_count,
                      "aging_priority_max": self.aging_priority_max,
                      "assessment_id": self.trace.assessment_id if self.trace else None},
        )


def _health_counts(items: list[CellStateAssessment]) -> tuple[int, int, int]:
    healthy = sum(item.state == "normal" for item in items)
    diseased = sum(item.state == "pathological" for item in items)
    return healthy, diseased, len(items) - healthy - diseased


def _aggregate(items: list[CellStateAssessment], level: str, node_id: str) -> MultiscaleAssessment:
    healthy, diseased, unknown = _health_counts(items)
    confidences = [item.confidence for item in items if item.confidence is not None]
    evidence_ids = tuple(sorted({e.evidence_id for item in items for e in item.evidence}))
    source_ids = tuple(sorted({item.cell_id for item in items}))
    confidence = min(confidences) if confidences else None
    uncertainty = (1.0 - confidence) if confidence is not None else 1.0
    trace = AssessmentTrace(
        assessment_id=f"{level}:{node_id}", level=level, node_id=node_id,
        source_ids=source_ids, evidence_ids=evidence_ids,
        confidence=confidence, uncertainty=uncertainty,
    )
    return MultiscaleAssessment(level=level, node_id=node_id, cell_count=len(items),
        healthy_count=healthy, diseased_count=diseased, unknown_count=unknown,
        confidence=confidence, uncertainty=uncertainty,
        evidence_ids=evidence_ids, source_cell_ids=source_ids, trace=trace)


def _attach_lineage(
    assessments: list[MultiscaleAssessment],
    mapping_registry: HierarchyMappingRegistry | None,
) -> list[MultiscaleAssessment]:
    """Attach direct parent assessment IDs and mapping provenance to each level."""
    if mapping_registry is None:
        return assessments

    mappings = mapping_registry.mappings
    by_cell = {item.cell_id: item for item in mappings}
    result_by_id = {f"{item.level}:{item.node_id}": item for item in assessments}

    parents: dict[str, set[str]] = {key: set() for key in result_by_id}
    evidence: dict[str, set[str]] = {key: set() for key in result_by_id}
    provenance: dict[str, set[str]] = {key: set() for key in result_by_id}

    for mapping in mappings:
        cell_result = result_by_id.get(f"cell:{mapping.cell_id}")
        # CellStateAssessment is the source object, not a MultiscaleAssessment;
        # keep it in source_ids rather than fabricating a cell-level assessment.
        chain = (
            ("cell_population", mapping.population_id),
            ("tissue", mapping.tissue_id),
            ("region", mapping.region_id),
        )
        for level, node_id in chain:
            key = f"{level}:{node_id}"
            if key in evidence:
                evidence[key].update(mapping.evidence_ids)
                provenance[key].update(mapping.provenance)
        population_key = f"cell_population:{mapping.population_id}"
        tissue_key = f"tissue:{mapping.tissue_id}"
        region_key = f"region:{mapping.region_id}"
        hand_key = None
        # The hand assessment is identified by the registry's hand_id below.
        if tissue_key in parents:
            parents[tissue_key].add(population_key)
        if region_key in parents:
            parents[region_key].add(tissue_key)
        hand_key = next((key for key in result_by_id if key == f"hand:{mapping.hand_id}"), None)
        if hand_key:
            parents[hand_key].add(region_key)
        if population_key in result_by_id:
            evidence[population_key].update(mapping.evidence_ids)
            provenance[population_key].update(mapping.provenance)

    updated: list[MultiscaleAssessment] = []
    for item in assessments:
        key = f"{item.level}:{item.node_id}"
        trace = item.trace
        if trace is None:
            updated.append(item)
            continue
        trace = replace(
            trace,
            parent_assessment_ids=tuple(sorted(parents[key])),
            evidence_ids=tuple(sorted(set(trace.evidence_ids) | evidence[key])),
            provenance=tuple(sorted(set(trace.provenance) | provenance[key])),
        )
        updated.append(replace(
            item,
            evidence_ids=tuple(sorted(set(item.evidence_ids) | evidence[key])),
            trace=trace,
        ))
    return updated


def aggregate_assessments(
    assessments: Iterable[CellStateAssessment], *,
    cell_to_population: dict[str, str] | None = None,
    population_to_tissue: dict[str, str] | None = None,
    tissue_to_region: dict[str, str] | None = None,
    hand_id: str,
    hierarchy_mapping: HierarchyMappingRegistry | None = None,
) -> list[MultiscaleAssessment]:
    """Aggregate cells to population, tissue, region and hand.

    ``hierarchy_mapping`` is the preferred API. The three dictionaries remain
    accepted for backwards compatibility, but cannot be mixed with the registry.
    """
    if hierarchy_mapping is not None:
        if any(value is not None for value in (cell_to_population, population_to_tissue, tissue_to_region)):
            raise ValueError("use hierarchy_mapping or individual mapping dictionaries, not both")
        hierarchy_mapping.validate()
        cell_to_population, population_to_tissue, tissue_to_region = hierarchy_mapping.as_multiscale_dicts()
        registry_hand_ids = {item.hand_id for item in hierarchy_mapping.mappings}
        if registry_hand_ids and registry_hand_ids != {hand_id}:
            raise ValueError("hierarchy mapping contains a different hand_id")
    if cell_to_population is None or population_to_tissue is None or tissue_to_region is None:
        raise ValueError("complete hierarchy mapping is required")

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
        for key in (("cell_population", population), ("tissue", tissue), ("region", region), ("hand", hand_id)):
            grouped.setdefault(key, []).append(item)

    order = {"cell_population": 0, "tissue": 1, "region": 2, "hand": 3}
    result = sorted((_aggregate(items, level, node_id) for (level, node_id), items in grouped.items()),
                    key=lambda item: (order[item.level], item.node_id))
    return _attach_lineage(result, hierarchy_mapping)


def assessments_to_risk_signals(assessments: Iterable[MultiscaleAssessment]) -> tuple[RiskSignal, ...]:
    return tuple(item.to_risk_signal() for item in assessments)
