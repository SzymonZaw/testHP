"""Multiscale biological hierarchy for the digital hand twin."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from .biological_timeline import BiologicalTimeline
    from .biological_trajectory import BiologicalTrajectory
    from .biological_state_estimate import BiologicalRiskAssessment

Level = Literal["hand", "region", "structure", "tissue", "cell_population", "cell", "molecular"]
_LEVEL_ORDER = ("hand", "region", "structure", "tissue", "cell_population", "cell", "molecular")


@dataclass(frozen=True)
class BiologicalObservation:
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
        return BiologicalNode(self.node_id, self.level, self.label, self.parent_id, self.child_ids + (child_id,), self.observations, self.metadata)

    def with_observation(self, observation: BiologicalObservation) -> "BiologicalNode":
        return BiologicalNode(self.node_id, self.level, self.label, self.parent_id, self.child_ids, self.observations + (observation,), self.metadata)

    def timeline(self) -> "BiologicalTimeline":
        from .biological_timeline import BiologicalTimeline
        return BiologicalTimeline(self.observations)


@dataclass(frozen=True)
class BiologicalHierarchy:
    root_id: str
    nodes: dict[str, BiologicalNode] = field(default_factory=dict)

    @classmethod
    def create_hand(cls, node_id: str, label: str = "hand") -> "BiologicalHierarchy":
        return cls(node_id, {node_id: BiologicalNode(node_id, "hand", label)})

    def add_node(self, node_id: str, level: Level, label: str, parent_id: str, metadata: dict[str, Any] | None = None) -> "BiologicalHierarchy":
        if node_id in self.nodes:
            raise ValueError(f"node already exists: {node_id}")
        parent = self.nodes.get(parent_id)
        if parent is None:
            raise ValueError(f"parent node does not exist: {parent_id}")
        nodes = dict(self.nodes)
        nodes[parent_id] = parent.add_child(node_id)
        nodes[node_id] = BiologicalNode(node_id, level, label, parent_id=parent_id, metadata=metadata or {})
        return BiologicalHierarchy(self.root_id, nodes)

    def with_observation(self, node_id: str, observation: BiologicalObservation) -> "BiologicalHierarchy":
        node = self.nodes.get(node_id)
        if node is None:
            raise ValueError(f"node does not exist: {node_id}")
        nodes = dict(self.nodes)
        nodes[node_id] = node.with_observation(observation)
        return BiologicalHierarchy(self.root_id, nodes)

    def levels(self) -> tuple[Level, ...]:
        return tuple(level for level in _LEVEL_ORDER if any(n.level == level for n in self.nodes.values()))

    def descendants(self, node_id: str) -> tuple[BiologicalNode, ...]:
        node = self.nodes.get(node_id)
        if node is None:
            raise ValueError(f"node does not exist: {node_id}")
        result: list[BiologicalNode] = []
        for child_id in node.child_ids:
            child = self.nodes[child_id]
            result.append(child)
            result.extend(self.descendants(child_id))
        return tuple(result)

    def aggregate_observations(self, node_id: str) -> tuple[BiologicalObservation, ...]:
        node = self.nodes.get(node_id)
        if node is None:
            raise ValueError(f"node does not exist: {node_id}")
        observations = list(node.observations)
        for descendant in self.descendants(node_id):
            observations.extend(descendant.observations)
        return tuple(observations)

    def timeline(self, node_id: str, include_descendants: bool = False) -> "BiologicalTimeline":
        from .biological_timeline import BiologicalTimeline
        node = self.nodes.get(node_id)
        if node is None:
            raise ValueError(f"node does not exist: {node_id}")
        observations = self.aggregate_observations(node_id) if include_descendants else node.observations
        return BiologicalTimeline(observations)

    def trajectory(self, node_id: str, key: str, include_descendants: bool = False) -> "BiologicalTrajectory":
        from .biological_trajectory import BiologicalTrajectory
        return BiologicalTrajectory.from_timeline(self.timeline(node_id, include_descendants=include_descendants), key)

    def risk_assessment(self, node_id: str, estimate: Any, *, risk_level: str, rationale: str, confidence: float | None = None) -> "BiologicalRiskAssessment":
        """Attach a non-diagnostic risk assessment to an existing state estimate."""
        from .biological_state_estimate import BiologicalRiskAssessment
        if node_id not in self.nodes:
            raise ValueError(f"node does not exist: {node_id}")
        return BiologicalRiskAssessment.from_estimate(estimate, risk_level=risk_level, rationale=rationale, confidence=confidence)

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
