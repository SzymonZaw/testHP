"""Explicit, auditable mapping between cell and hand hierarchy levels.

The mapping is intentionally separate from biological assessment. It only
states containment/identity relationships and refuses to infer missing links.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable

from .anatomy_foundation import MultiscaleHierarchy


@dataclass(frozen=True)
class HierarchyMapping:
    """Canonical containment path for one cell assessment."""

    cell_id: str
    population_id: str
    tissue_id: str
    region_id: str
    hand_id: str
    confidence: float | None = None
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    def validate(self) -> None:
        for name, value in (
            ("cell_id", self.cell_id),
            ("population_id", self.population_id),
            ("tissue_id", self.tissue_id),
            ("region_id", self.region_id),
            ("hand_id", self.hand_id),
        ):
            if not value:
                raise ValueError(f"{name} is required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")
        if len(set(self.provenance)) != len(self.provenance):
            raise ValueError("provenance must be unique")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class HierarchyMappingRegistry:
    """Validated collection of explicit cell-to-hand mappings."""

    mappings: tuple[HierarchyMapping, ...] = ()

    def validate(self, hierarchy: MultiscaleHierarchy | None = None) -> None:
        seen_cells: set[str] = set()
        for mapping in self.mappings:
            mapping.validate()
            if mapping.cell_id in seen_cells:
                raise ValueError(f"duplicate hierarchy mapping for cell {mapping.cell_id}")
            seen_cells.add(mapping.cell_id)
            if hierarchy is not None:
                if mapping.hand_id != hierarchy.hand_id:
                    raise ValueError("mapping belongs to a different hand")
                cell_ids = {cell.cell_id for cell in hierarchy.cells}
                tissue_ids = {tissue.tissue_id for tissue in hierarchy.tissues}
                if mapping.cell_id not in cell_ids:
                    raise ValueError(f"mapping references unknown cell {mapping.cell_id}")
                if mapping.tissue_id not in tissue_ids:
                    raise ValueError(f"mapping references unknown tissue {mapping.tissue_id}")
                cell = next(cell for cell in hierarchy.cells if cell.cell_id == mapping.cell_id)
                if cell.tissue_id != mapping.tissue_id:
                    raise ValueError("mapping tissue does not match canonical cell containment")

    def as_multiscale_dicts(self) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
        """Return mappings in the format consumed by multiscale aggregation."""
        self.validate()
        return (
            {item.cell_id: item.population_id for item in self.mappings},
            {item.population_id: item.tissue_id for item in self.mappings},
            {item.tissue_id: item.region_id for item in self.mappings},
        )

    @classmethod
    def from_iterable(cls, mappings: Iterable[HierarchyMapping]) -> "HierarchyMappingRegistry":
        registry = cls(tuple(mappings))
        registry.validate()
        return registry

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {"mappings": tuple(item.to_dict() for item in self.mappings)}
