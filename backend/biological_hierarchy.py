"""Multiscale biological hierarchy for the digital hand twin.

This module defines representation contracts only. It does not diagnose disease,
estimate human lifespan, or prescribe treatment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Level = Literal["hand", "region", "structure", "tissue", "cell_population", "cell", "molecular"]


@dataclass(frozen=True)
class BiologicalObservation:
    """Evidence attached to any level of the biological hierarchy."""

    observation_id: str
    source: str
    timestamp: str
    values: dict[str, Any] = field(default_factory=dict)
    quality: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class BiologicalNode:
    """A node at one biological scale, linked to parent and child nodes."""

    node_id: str
    level: Level
    label: str
    parent_id: str | None = None
    child_ids: tuple[str, ...] = ()
    observations: tuple[BiologicalObservation, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_child(self, child_id: str) -> "BiologicalNode":
        if child_id in self.child_ids:
            return self
        return BiologicalNode(
            node_id=self.node_id,
            level=self.level,
            label=self.label,
            parent_id=self.parent_id,
            child_ids=self.child_ids + (child_id,),
            observations=self.observations,
            metadata=self.metadata,
        )

    def with_observation(self, observation: BiologicalObservation) -> "BiologicalNode":
        return BiologicalNode(
            node_id=self.node_id,
            level=self.level,
            label=self.label,
            parent_id=self.parent_id,
            child_ids=self.child_ids,
            observations=self.observations + (observation,),
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class BiologicalHierarchy:
    """Immutable hierarchy from whole hand down to molecular evidence."""

    root_id: str
    nodes: dict[str, BiologicalNode] = field(default_factory=dict)

    @classmethod
    def create_hand(cls, node_id: str, label: str = "hand") -> "BiologicalHierarchy":
        return cls(
            root_id=node_id,
            nodes={node_id: BiologicalNode(node_id, "hand", label)},
        )

    def add_node(
        self,
        node_id: str,
        level: Level,
        label: str,
        parent_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> "BiologicalHierarchy":
        if node_id in self.nodes:
            raise ValueError(f"node already exists: {node_id}")
        parent = self.nodes.get(parent_id)
        if parent is None:
            raise ValueError(f"parent node does not exist: {parent_id}")
        node = BiologicalNode(node_id, level, label, parent_id=parent_id, metadata=metadata or {})
        nodes = dict(self.nodes)
        nodes[parent_id] = parent.add_child(node_id)
        nodes[node_id] = node
        return BiologicalHierarchy(self.root_id, nodes)

    def levels(self) -> tuple[Level, ...]:
        order = ("hand", "region", "structure", "tissue", "cell_population", "cell", "molecular")
        return tuple(level for level in order if any(n.level == level for n in self.nodes.values()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_id": self.root_id,
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "level": node.level,
                    "label": node.label,
                    "parent_id": node.parent_id,
                    "child_ids": list(node.child_ids),
                    "observations": [ob.__dict__ for ob in node.observations],
                    "metadata": node.metadata,
                }
                for node_id, node in self.nodes.items()
            },
        }
