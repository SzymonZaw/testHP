"""Hierarchical biological state aggregation."""

from dataclasses import dataclass, field
from typing import Iterable, Optional

from .measurement import Measurement


_LEVELS = ("organism", "system", "organ", "tissue", "cell_population", "cell", "site")


@dataclass(frozen=True)
class BiologicalNode:
    id: str
    level: str
    name: str
    parent_id: Optional[str] = None
    measurements: tuple[Measurement, ...] = ()
    value: Optional[float] = None

    def __post_init__(self) -> None:
        if self.level not in _LEVELS:
            raise ValueError(f"Unsupported biological level: {self.level}")


@dataclass
class BiologicalHierarchy:
    nodes: dict[str, BiologicalNode] = field(default_factory=dict)

    def add_node(self, node: BiologicalNode) -> None:
        if node.parent_id is not None and node.parent_id not in self.nodes:
            raise ValueError(f"Unknown parent node: {node.parent_id}")
        self.nodes[node.id] = node

    def add_measurement(self, node_id: str, measurement: Measurement) -> None:
        node = self.nodes[node_id]
        self.nodes[node_id] = BiologicalNode(
            id=node.id,
            level=node.level,
            name=node.name,
            parent_id=node.parent_id,
            measurements=node.measurements + (measurement,),
            value=node.value,
        )

    def ancestors(self, node_id: str) -> list[BiologicalNode]:
        result: list[BiologicalNode] = []
        current = self.nodes[node_id]
        while current.parent_id is not None:
            current = self.nodes[current.parent_id]
            result.append(current)
        return result

    def children(self, node_id: str) -> list[BiologicalNode]:
        return [node for node in self.nodes.values() if node.parent_id == node_id]

    def propagate_measurement(self, node_id: str, measurement: Measurement) -> None:
        self.add_measurement(node_id, measurement)
        for ancestor in self.ancestors(node_id):
            self.add_measurement(ancestor.id, measurement)

    def path(self, node_id: str) -> list[str]:
        result = [node_id]
        current = self.nodes[node_id]
        while current.parent_id is not None:
            result.append(current.parent_id)
            current = self.nodes[current.parent_id]
        return result

    def nodes_at_level(self, level: str) -> list[BiologicalNode]:
        if level not in _LEVELS:
            raise ValueError(f"Unsupported biological level: {level}")
        return [node for node in self.nodes.values() if node.level == level]


def build_hierarchy(nodes: Iterable[BiologicalNode]) -> BiologicalHierarchy:
    hierarchy = BiologicalHierarchy()
    pending = list(nodes)
    while pending:
        progressed = False
        for node in pending[:]:
            if node.parent_id is None or node.parent_id in hierarchy.nodes:
                hierarchy.add_node(node)
                pending.remove(node)
                progressed = True
        if not progressed:
            raise ValueError("Hierarchy contains an unresolved parent relationship")
    return hierarchy
