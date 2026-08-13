"""Transparent organ-level state aggregation.

Organ models aggregate measured dimensions and dependencies. They are not
clinical digital twins and do not infer diagnoses without validated data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class OrganState:
    organ: str
    dimensions: Mapping[str, float]
    integrity_score: float | None = None


@dataclass
class OrganModel:
    name: str
    dimensions: dict[str, float] = field(default_factory=dict)
    dependencies: dict[str, float] = field(default_factory=dict)

    def set_dimension(self, name: str, value: float) -> None:
        if not name.strip():
            raise ValueError("Dimension name cannot be empty")
        self.dimensions[name] = float(value)

    def set_dependency(self, organ: str, weight: float) -> None:
        if not organ.strip() or organ == self.name:
            raise ValueError("Dependency must reference another organ")
        if weight < 0:
            raise ValueError("Dependency weight cannot be negative")
        self.dependencies[organ] = float(weight)

    def snapshot(self) -> OrganState:
        return OrganState(
            organ=self.name,
            dimensions=dict(self.dimensions),
        )


@dataclass
class OrganSystemModel:
    organs: dict[str, OrganModel] = field(default_factory=dict)

    def add_organ(self, organ: OrganModel) -> None:
        if organ.name in self.organs:
            raise ValueError(f"Organ already exists: {organ.name}")
        self.organs[organ.name] = organ

    def dependency_graph(self) -> dict[str, dict[str, float]]:
        return {
            name: dict(organ.dependencies)
            for name, organ in self.organs.items()
        }

    def affected_by(self, organ_name: str) -> tuple[str, ...]:
        if organ_name not in self.organs:
            raise KeyError(organ_name)
        return tuple(
            name
            for name, organ in self.organs.items()
            if organ_name in organ.dependencies
        )
